"""Static build-boundary policy; mocked GitHub reads, no application or Vercel execution."""

import hashlib
import io
import json
import os
import re
import unittest
from contextlib import redirect_stdout
from copy import deepcopy
from pathlib import Path
from unittest.mock import mock_open, patch
from urllib.error import URLError

import yaml

REPOSITORY = "Sam-24-dev/RideFare-ETL-Pipeline"
API = f"https://api.github.com/repos/{REPOSITORY}"
SHA = "a" * 40
EXPECTED_ACTIONS = [
    "actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09",
    "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1",
    "actions/setup-node@249970729cb0ef3589644e2896645e5dc5ba9c38",
]
# Public project metadata observed by GET on 2026-10-16; never read from secrets.
PROJECT = {
    "projectId": "prj_tS8gW1XL7PuYmvH3rD3ATUh6MTEO",
    "orgId": "team_FO5NX52lZMHAG9a8lgb7Zczq",
    "projectName": "ride-fare-etl-pipeline-web",
    "settings": {
        "createdAt": 1775274106564,
        "framework": "nextjs",
        "devCommand": None,
        "installCommand": None,
        "buildCommand": None,
        "outputDirectory": None,
        "rootDirectory": "apps/web",
        "directoryListing": False,
        "nodeVersion": "22.x",
    },
}
PROJECT_JSON = json.dumps(PROJECT, indent=2) + "\n"
SETTINGS_RUN = (
    'test ! -e .vercel\ntest ! -e "$RUNNER_TEMP/ridefare-vercel-build"\n'
    'mkdir .vercel "$RUNNER_TEMP/ridefare-vercel-build"\n'
    "cat > .vercel/project.json <<'JSON'\n" + PROJECT_JSON + "JSON\n"
)
BUILD_RUN = (
    f"printf '%s\\n' '{hashlib.sha256(PROJECT_JSON.encode()).hexdigest()}"
    "  .vercel/project.json' | sha256sum --check --status\n"
    'vercel build --prod --global-config "$RUNNER_TEMP/ridefare-vercel-build"\n'
)


class ProductionLoader(yaml.SafeLoader):
    # Preserve `on` and real booleans without changing SafeLoader's global resolvers.
    yaml_implicit_resolvers = {
        key: [(tag, pattern) for tag, pattern in resolvers if tag != "tag:yaml.org,2002:bool"]
        for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
    }

    def construct_mapping(self, node, deep=False):
        self.flatten_mapping(node)
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str) or key in mapping:
                raise yaml.constructor.ConstructorError(
                    None, None, "non-string or duplicate YAML key", key_node.start_mark
                )
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


ProductionLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
    list("tTfF"),
)


class TestProductionWorkflowPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[2]
        cls.workflow = yaml.load(
            (root / ".github/workflows/vercel-production.yml").read_text(encoding="utf-8"),
            Loader=ProductionLoader,
        )

    def assert_action_pins(self, workflow):
        actual = [
            step["uses"]
            for job in workflow["jobs"].values()
            for step in job["steps"]
            if "uses" in step
        ]
        self.assertEqual(actual, EXPECTED_ACTIONS)

    def assert_policy(self, workflow):
        self.assertEqual(set(workflow), {"name", "on", "permissions", "jobs"})
        self.assertEqual(workflow["name"], "vercel-production")
        self.assertEqual(set(workflow["on"]), {"workflow_dispatch"})
        dispatch = workflow["on"]["workflow_dispatch"]
        self.assertEqual(set(dispatch), {"inputs"})
        self.assertEqual(set(dispatch["inputs"]), {"ci_run_id", "ci_run_attempt"})
        for value in dispatch["inputs"].values():
            self.assertEqual(set(value), {"description", "required", "type"})
            self.assertIs(value["required"], True)
            self.assertEqual(value["type"], "string")
            self.assertIsInstance(value["description"], str)
        self.assertEqual(
            workflow["permissions"], {"contents": "read", "actions": "read", "checks": "read"}
        )
        self.assertEqual(set(workflow["jobs"]), {"production-build"})
        job = workflow["jobs"]["production-build"]
        self.assertEqual(set(job), {"runs-on", "env", "steps"})
        self.assertEqual(job["runs-on"], "ubuntu-latest")
        self.assertEqual(job["env"], {"RIDEFARE_PROJECT_ROOT": "${{ github.workspace }}"})
        steps = job["steps"]
        self.assertEqual(len(steps), 11)
        gate = steps[0]
        self.assertEqual(set(gate), {"name", "id", "shell", "env", "run"})
        self.assertEqual(gate["name"], "Validate exact CI attempt")
        self.assertEqual(gate["id"], "ci")
        self.assertEqual(gate["shell"], "bash")
        self.assertEqual(gate["env"], {
            "GH_TOKEN": "${{ github.token }}",
            "CI_RUN_ID": "${{ inputs.ci_run_id }}",
            "CI_RUN_ATTEMPT": "${{ inputs.ci_run_attempt }}",
        })
        self.assertTrue(gate["run"].startswith("python3 -I -B - <<'PY'\n"))
        self.assertTrue(gate["run"].endswith("\nPY\n"))
        expected = [
            {"name": "Checkout validated revision", "uses": EXPECTED_ACTIONS[0],
             "with": {"ref": "${{ steps.ci.outputs.sha }}", "persist-credentials": False}},
            {"name": "Set up Python", "uses": EXPECTED_ACTIONS[1],
             "with": {"python-version": "3.13"}},
            {"name": "Install Python dependencies", "run":
             "python -m pip install --upgrade pip\npython -m pip install -e .[data,ml,dev]\n"},
            {"name": "Refresh public artifacts", "shell": "pwsh", "run":
             "./scripts/refresh-public-artifacts.ps1 -RunId production-${{ github.run_number }}"},
            {"name": "Set up Node", "uses": EXPECTED_ACTIONS[2], "with": {"node-version": "22"}},
            {"name": "Enable Corepack", "run": "corepack enable"},
            {"name": "Install workspace dependencies", "run":
             "corepack pnpm install --frozen-lockfile"},
            {"name": "Install Vercel CLI", "run": "npm install --global vercel@50.39.0"},
            {"name": "Prepare public Vercel settings", "shell": "bash", "run": SETTINGS_RUN},
            {"name": "Build production bundle", "shell": "bash", "run": BUILD_RUN},
        ]
        self.assertEqual(steps[1:], expected)
        self.assertIs(steps[1]["with"]["persist-credentials"], False)
        self.assert_action_pins(workflow)
        self.assertNotRegex(
            yaml.safe_dump(workflow),
            r"(?i)secrets\.|VERCEL_TOKEN|vercel\s+(pull|link|login|deploy|promote)|--(yes|token|id)\b",
        )

    def test_workflow_matches_build_only_policy(self):
        self.assert_policy(self.workflow)

    def test_workflow_matches_approved_action_pins(self):
        self.assert_action_pins(self.workflow)

    def test_rejects_unapproved_action_references(self):
        for job_name, job in self.workflow["jobs"].items():
            for index, step in enumerate(job["steps"]):
                if "uses" not in step:
                    continue
                repository, sha = step["uses"].split("@")
                for ref in ("v5", "v6", "v5.1.0", "v6.3.0", "v6.5.0", "main", sha[:12], "0" * 40):
                    invalid = deepcopy(self.workflow)
                    invalid["jobs"][job_name]["steps"][index]["uses"] = f"{repository}@{ref}"
                    with self.subTest(reference=ref), self.assertRaises(AssertionError):
                        self.assert_action_pins(invalid)
                invalid = deepcopy(self.workflow)
                invalid["jobs"][job_name]["steps"][index]["uses"] = f"other/action@{sha}"
                with self.assertRaises(AssertionError):
                    self.assert_action_pins(invalid)

    def test_rejects_automatic_events_credentials_publication_and_bypasses(self):
        self.assert_policy(self.workflow)
        mutations = []
        for event in ("push", "pull_request", "workflow_run", "schedule"):
            bad = deepcopy(self.workflow)
            bad["on"][event] = None
            mutations.append(bad)
        for field, value in (
            ("env", {"VERCEL_TOKEN": "${{ secrets.VERCEL_TOKEN }}"}),
            ("permissions", {"contents": "write"}), ("if", "always()"),
            ("environment", "Production"),
        ):
            bad = deepcopy(self.workflow)
            bad["jobs"]["production-build"][field] = value
            mutations.append(bad)
        for command in (
            "vercel pull --yes", "vercel link", "vercel login", "vercel deploy --prod",
            "vercel promote deployment", "vercel build --prod --yes", "git push --tags",
        ):
            bad = deepcopy(self.workflow)
            bad["jobs"]["production-build"]["steps"][-1]["run"] = command
            mutations.append(bad)
        for path, value in (("ref", "master"), ("persist-credentials", True)):
            bad = deepcopy(self.workflow)
            bad["jobs"]["production-build"]["steps"][1]["with"][path] = value
            mutations.append(bad)
        bad = deepcopy(self.workflow)
        bad["jobs"]["publisher"] = {"runs-on": "ubuntu-latest", "steps": []}
        mutations.append(bad)
        bad = deepcopy(self.workflow)
        bad["jobs"]["production-build"]["steps"].reverse()
        mutations.append(bad)
        for index, bad in enumerate(mutations):
            with self.subTest(candidate=index), self.assertRaises(AssertionError):
                self.assert_policy(yaml.load(yaml.safe_dump(bad), Loader=ProductionLoader))

    def gate_fixture(self):
        run = {
            "id": 123, "workflow_id": 256052140, "check_suite_id": 7,
            "path": ".github/workflows/ci.yml", "event": "push", "head_branch": "master",
            "head_sha": SHA, "status": "completed", "conclusion": "success", "run_attempt": 1,
            "repository": {"full_name": REPOSITORY}, "head_repository": {"full_name": REPOSITORY},
        }
        jobs = [
            {"id": index, "run_id": 123, "run_attempt": 1, "name": name, "head_sha": SHA,
             "status": "completed", "conclusion": "success",
             "check_run_url": f"{API}/check-runs/{index}"}
            for index, name in enumerate(("python-quality", "web-quality"), 11)
        ]
        responses = {
            "/git/ref/heads/master": {"object": {"sha": SHA}},
            "/actions/runs/123/attempts/1": run,
            "/actions/runs/123": deepcopy(run),
            "/actions/runs/123/attempts/1/jobs?per_page=100": {"total_count": 2, "jobs": jobs},
        }
        for job in jobs:
            responses[f"/check-runs/{job['id']}"] = {
                "id": job["id"], "name": job["name"], "head_sha": SHA, "status": "completed",
                "conclusion": "success", "app": {"id": 15368}, "check_suite": {"id": 7},
            }
        return responses

    def run_gate(self, responses, overrides=None):
        self.assert_policy(self.workflow)
        script = self.workflow["jobs"]["production-build"]["steps"][0]["run"]
        script = "\n".join(script.splitlines()[1:-1])
        environment = {
            "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REPOSITORY": REPOSITORY,
            "GITHUB_REF": "refs/heads/master", "GITHUB_SHA": SHA, "GH_TOKEN": "policy-only",
            "CI_RUN_ID": "123", "CI_RUN_ATTEMPT": "1", "GITHUB_OUTPUT": "policy-output",
        } | (overrides or {})
        requests = []

        def fake_get(request, timeout):
            self.assertEqual(request.get_method(), "GET")
            self.assertEqual(timeout, 30)
            self.assertTrue(request.full_url.startswith(API + "/"))
            path = request.full_url.removeprefix(API)
            requests.append(path)
            response = responses[path]
            if callable(response):
                response = response()
            if isinstance(response, Exception):
                raise response
            return io.BytesIO(json.dumps(response).encode())

        output = mock_open()
        with patch.dict(os.environ, environment, clear=True), \
                patch("urllib.request.urlopen", side_effect=fake_get), \
                patch("builtins.open", output), redirect_stdout(io.StringIO()):
            exec(compile(script, "<production-ci-gate>", "exec"), {})
        output.assert_called_once_with("policy-output", "a", encoding="utf-8")
        output().write.assert_called_once_with(f"sha={SHA}\n")
        return requests

    def test_gate_accepts_exact_successful_ci_attempt_with_read_only_requests(self):
        requests = self.run_gate(self.gate_fixture())
        self.assertEqual(requests, [
            "/git/ref/heads/master", "/actions/runs/123/attempts/1",
            "/actions/runs/123/attempts/1/jobs?per_page=100", "/check-runs/11", "/check-runs/12",
            "/actions/runs/123", "/git/ref/heads/master",
        ])

    def test_gate_rejects_wrong_context_and_invalid_inputs_before_network(self):
        for field, value in (
            ("GITHUB_REPOSITORY", "other/repo"), ("GITHUB_REF", "refs/heads/other"),
            ("GITHUB_EVENT_NAME", "push"), ("GITHUB_SHA", "bad"),
            ("CI_RUN_ID", "1; command"), ("CI_RUN_ID", "0"), ("CI_RUN_ATTEMPT", "1.0"),
        ):
            with self.subTest(field=field, value=value), self.assertRaises(SystemExit):
                self.run_gate({}, {field: value})

    def test_gate_rejects_untrusted_ci_jobs_checks_and_incomplete_responses(self):
        run_path = "/actions/runs/123/attempts/1"
        jobs_path = run_path + "/jobs?per_page=100"
        cases = []
        for key, value in (
            ("workflow_id", 999), ("event", "pull_request"), ("head_branch", "other"),
            ("head_sha", "b" * 40), ("run_attempt", 2), ("status", "in_progress"),
            ("conclusion", "failure"), ("path", ".github/workflows/other.yml"),
            ("head_repository", {"full_name": "other/repo"}),
        ):
            data = self.gate_fixture()
            data[run_path][key] = value
            cases.append(data)
        for key, value in (
            ("run_id", 999), ("run_attempt", 2), ("head_sha", "b" * 40),
            ("conclusion", "skipped"), ("name", "web-quality"),
            ("check_run_url", "https://other.invalid/check-runs/11"),
        ):
            data = self.gate_fixture()
            data[jobs_path]["jobs"][0][key] = value
            cases.append(data)
        for check_id in (11, 12):
            for key, value in (
                ("app", {"id": 999}), ("head_sha", "b" * 40), ("check_suite", {"id": 8}),
                ("conclusion", "failure"), ("status", "queued"), ("name", "other"),
            ):
                data = self.gate_fixture()
                data[f"/check-runs/{check_id}"][key] = value
                cases.append(data)
        for path, value in (
            (jobs_path, {"total_count": 101, "jobs": []}),
            (run_path, {}), (run_path, URLError("unavailable")),
            ("/git/ref/heads/master", {"object": {"sha": "b" * 40}}),
        ):
            data = self.gate_fixture()
            data[path] = value
            cases.append(data)
        data = self.gate_fixture()
        data["/actions/runs/123"]["run_attempt"] = 2
        cases.append(data)
        data = self.gate_fixture()
        master = iter(({"object": {"sha": SHA}}, {"object": {"sha": "b" * 40}}))
        data["/git/ref/heads/master"] = lambda: next(master)
        cases.append(data)
        for index, data in enumerate(cases):
            with self.subTest(case=index), self.assertRaises(SystemExit):
                self.run_gate(data)

    def test_loader_is_safe_and_local(self):
        parsed = yaml.load("on: {}\nflag: true\nkeep: false\n", Loader=ProductionLoader)
        self.assertEqual(parsed["on"], {})
        self.assertIs(parsed["flag"], True)
        self.assertIs(parsed["keep"], False)
        self.assertEqual(yaml.safe_load("on: false\n"), {True: False})
        for text in (
            "on: {}\non: {push: {branches: [other]}}\n",
            "steps: [{uses: actions/checkout@v5, uses: actions/checkout@main}]\n",
            "!!python/tuple [blocked]",
        ):
            with self.subTest(yaml=text):
                with self.assertRaises(yaml.constructor.ConstructorError):
                    yaml.load(text, Loader=ProductionLoader)


if __name__ == "__main__":
    unittest.main(verbosity=2)
