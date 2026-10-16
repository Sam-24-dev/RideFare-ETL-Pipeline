"""Static build-boundary policy; mocked GitHub reads, no application or Vercel execution."""

import hashlib
import io
import json
import os
import re
import shutil
import stat
import tarfile
import tempfile
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
    "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    "actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093",
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
ARTIFACT_ID_RUN = (
    "python3 -I -B - <<'PY'\nimport os\nimport re\n\n"
    'value = os.environ.get("ARTIFACT_ID", "")\n'
    'if not re.fullmatch(r"[1-9][0-9]*", value):\n'
    '    raise SystemExit("A single explicit artifact ID is required")\n'
    'with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:\n'
    '    output.write(f"id={value}\\n")\nPY\n'
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
        self.assertEqual(set(workflow["jobs"]), {"production-build", "verify-production-bundle"})
        job = workflow["jobs"]["production-build"]
        self.assertEqual(set(job), {"runs-on", "env", "outputs", "steps"})
        self.assertEqual(job["runs-on"], "ubuntu-latest")
        self.assertEqual(job["env"], {"RIDEFARE_PROJECT_ROOT": "${{ github.workspace }}"})
        steps = job["steps"]
        self.assertEqual(len(steps), 13)
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
        self.assertEqual(steps[1:11], expected)
        self.assertIs(steps[1]["with"]["persist-credentials"], False)
        self.assertEqual(job["outputs"], {
            "artifact_id": "${{ steps.bundle-upload.outputs.artifact-id }}",
            "zip_digest": "${{ steps.bundle-upload.outputs.artifact-digest }}",
            "package_sha256": "${{ steps.bundle.outputs.package_sha256 }}",
        })
        package = steps[11]
        self.assertEqual(set(package), {"name", "id", "shell", "env", "run"})
        self.assertEqual(package["name"], "Package production output")
        self.assertEqual(package["id"], "bundle")
        self.assertEqual(package["shell"], "bash")
        self.assertEqual(package["env"], {
            "BUNDLE_MODE": "pack",
            "BUNDLE_DIR": "${{ runner.temp }}/ridefare-transfer-upload",
            "CI_RUN_ID": "${{ inputs.ci_run_id }}",
            "CI_RUN_ATTEMPT": "${{ inputs.ci_run_attempt }}",
        })
        self.assertEqual(steps[12], {
            "name": "Upload production bundle", "id": "bundle-upload",
            "uses": EXPECTED_ACTIONS[3],
            "with": {
                "name": "production-bundle-${{ github.run_id }}-${{ github.run_attempt }}",
                "path": "${{ runner.temp }}/ridefare-transfer-upload/production-bundle.tar",
                "if-no-files-found": "error", "retention-days": 1, "overwrite": False,
            },
        })
        self.assertIs(steps[12]["with"]["overwrite"], False)
        consumer = workflow["jobs"]["verify-production-bundle"]
        self.assertEqual(set(consumer), {"runs-on", "needs", "steps"})
        self.assertEqual(consumer["runs-on"], "ubuntu-latest")
        self.assertEqual(consumer["needs"], "production-build")
        self.assertEqual(consumer["steps"], [
            {"name": "Require single artifact ID", "id": "artifact-source", "shell": "bash",
             "env": {"ARTIFACT_ID": "${{ needs.production-build.outputs.artifact_id }}"},
             "run": ARTIFACT_ID_RUN},
            {"name": "Download exact production bundle", "uses": EXPECTED_ACTIONS[4],
             "with": {"artifact-ids": "${{ steps.artifact-source.outputs.id }}",
                      "merge-multiple": True,
                      "path": "${{ runner.temp }}/ridefare-transfer-received"}},
            {"name": "Verify production bundle", "shell": "bash", "env": {
                "BUNDLE_MODE": "verify",
                "BUNDLE_DIR": "${{ runner.temp }}/ridefare-transfer-received",
                "EXTRACT_DIR": "${{ runner.temp }}/ridefare-transfer-verified",
                "ARTIFACT_ID": "${{ needs.production-build.outputs.artifact_id }}",
                "ZIP_DIGEST": "${{ needs.production-build.outputs.zip_digest }}",
                "PACKAGE_SHA256": "${{ needs.production-build.outputs.package_sha256 }}",
                "CI_RUN_ID": "${{ inputs.ci_run_id }}",
                "CI_RUN_ATTEMPT": "${{ inputs.ci_run_attempt }}",
                "GH_TOKEN": "${{ github.token }}",
             }, "run": package["run"]},
        ])
        self.assertIs(consumer["steps"][1]["with"]["merge-multiple"], True)
        self.assertTrue(package["run"].startswith("python3 -I -B - <<'PY'\n"))
        self.assertTrue(package["run"].endswith("\nPY\n"))
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

    def test_transfer_policy_rejects_loose_selection_permissions_and_extra_steps(self):
        self.assert_policy(self.workflow)
        for job_name, field, value in (
            ("verify-production-bundle", "environment", "Production"),
            ("verify-production-bundle", "permissions", {"deployments": "write"}),
            ("verify-production-bundle", "needs", []),
        ):
            bad = deepcopy(self.workflow)
            bad["jobs"][job_name][field] = value
            with self.subTest(field=field), self.assertRaises(AssertionError):
                self.assert_policy(bad)
        for change in ({"name": "latest"}, {"pattern": "*"}, {"run-id": "123"}):
            bad = deepcopy(self.workflow)
            bad["jobs"]["verify-production-bundle"]["steps"][1]["with"].update(change)
            with self.subTest(selection=change), self.assertRaises(AssertionError):
                self.assert_policy(bad)
        for field, value in (("overwrite", True), ("retention-days", 90),
                             ("path", "${{ github.workspace }}")):
            bad = deepcopy(self.workflow)
            bad["jobs"]["production-build"]["steps"][-1]["with"][field] = value
            with self.subTest(field=field), self.assertRaises(AssertionError):
                self.assert_policy(bad)

    def test_download_policy_rejects_missing_disabled_or_non_boolean_merge_multiple(self):
        self.assert_policy(self.workflow)
        for value in (None, False, "true", 1):
            bad = deepcopy(self.workflow)
            inputs = bad["jobs"]["verify-production-bundle"]["steps"][1]["with"]
            if value is None:
                del inputs["merge-multiple"]
            else:
                inputs["merge-multiple"] = value
            with self.subTest(value=value), self.assertRaises(AssertionError):
                self.assert_policy(bad)

    def test_artifact_selection_rejects_empty_multiple_and_invalid_ids_before_download(self):
        steps = self.workflow["jobs"].get("verify-production-bundle", {}).get("steps", [])
        source = next((s for s in steps if s.get("id") == "artifact-source"), None)
        self.assertIsNotNone(source, "Validate ID before download-artifact can select anything")
        code = "\n".join(source["run"].splitlines()[1:-1])
        for value in ("", "latest", "789,790", "0", "-1", "1.5", "true"):
            output = mock_open()
            with self.subTest(value=value), \
                    patch.dict(os.environ, {"ARTIFACT_ID": value}, clear=True), \
                    patch("builtins.open", output), self.assertRaises(SystemExit):
                exec(compile(code, "<artifact-source>", "exec"), {})
            output.assert_not_called()
        output = mock_open()
        valid = {"ARTIFACT_ID": "789", "GITHUB_OUTPUT": "result"}
        with patch.dict(os.environ, valid, clear=True), patch("builtins.open", output):
            exec(compile(code, "<artifact-source>", "exec"), {})
        output().write.assert_called_once_with("id=789\n")

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


class TestProductionBundleTransfer(unittest.TestCase):
    """Execute the real inline transfer code, using only tiny temporary fixtures."""

    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[2]
        cls.workflow = yaml.load(
            (root / ".github/workflows/vercel-production.yml").read_text(encoding="utf-8"),
            Loader=ProductionLoader,
        )

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        consumer = self.workflow["jobs"]["verify-production-bundle"]["steps"]
        self.download_inputs = consumer[1]["with"]
        self.bundle_dir = Path(consumer[2]["env"]["BUNDLE_DIR"].replace(
            "${{ runner.temp }}", str(self.root)))
        self.workspace = self.root / "workspace"
        self.output = self.workspace / ".vercel/output"
        (self.output / "static/.well-known").mkdir(parents=True)
        (self.output / "config.json").write_text('{"version":3}\n', encoding="utf-8")
        (self.output / "builds.json").write_text('{"target":"production"}\n', encoding="utf-8")
        (self.output / "static/index.html").write_bytes(b"fixture, never executed\n")
        (self.output / "static/.well-known/data.txt").write_bytes(b"hidden fixture\n")
        (self.workspace / ".vercel/project.json").write_bytes(PROJECT_JSON.encode())
        self.environment = {
            "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REPOSITORY": REPOSITORY,
            "GITHUB_REF": "refs/heads/master", "GITHUB_SHA": SHA,
            "GITHUB_RUN_ID": "456", "GITHUB_RUN_ATTEMPT": "1",
            "GITHUB_WORKSPACE": str(self.workspace), "CI_RUN_ID": "123",
            "CI_RUN_ATTEMPT": "1", "GITHUB_OUTPUT": str(self.root / "job-output"),
        }

    def execute(self, mode, overrides=None, responses=None):
        steps = self.workflow["jobs"]["production-build"]["steps"]
        step = next((s for s in steps if s.get("id") == "bundle"), None)
        self.assertIsNotNone(step, "Missing real verified-transfer implementation")
        script = step["run"]
        self.assertTrue(script.startswith("python3 -I -B - <<'PY'\n"))
        code = "\n".join(script.splitlines()[1:-1])
        environment = self.environment | {
            "BUNDLE_MODE": mode,
            "BUNDLE_DIR": str(self.root / "upload" if mode == "pack" else self.bundle_dir),
            "EXTRACT_DIR": str(self.root / "verified"), "ARTIFACT_ID": "789",
            "ZIP_DIGEST": "b" * 64, "GH_TOKEN": "fixture-only",
        } | (overrides or {})
        requests = []

        def fake_get(request, timeout):
            self.assertEqual(mode, "verify", "Producer must not need GitHub credentials")
            self.assertEqual(request.get_method(), "GET")
            self.assertEqual(timeout, 30)
            self.assertTrue(request.full_url.startswith(API + "/"))
            path = request.full_url.removeprefix(API)
            requests.append(path)
            self.assertIn(path, responses)
            value = responses[path]
            if isinstance(value, Exception):
                raise value
            return io.BytesIO(json.dumps(value).encode())

        with patch.dict(os.environ, environment, clear=True), \
                patch("urllib.request.urlopen", side_effect=fake_get), \
                redirect_stdout(io.StringIO()):
            exec(compile(code, "<production-bundle-transfer>", "exec"), {})
        return requests

    def package_fixture(self):
        self.execute("pack")
        package = self.root / "upload/production-bundle.tar"
        self.assertTrue(package.is_file())
        self.digest = hashlib.sha256(package.read_bytes()).hexdigest()
        self.assertIn(f"package_sha256={self.digest}\n",
                      (self.root / "job-output").read_text(encoding="utf-8"))
        received = Path(self.download_inputs["path"].replace("${{ runner.temp }}", str(self.root)))
        # The pinned action nests ID-selected artifacts unless merge-multiple is true.
        if self.download_inputs.get("merge-multiple", False) is not True:
            received /= self.metadata()["/actions/artifacts/789"]["name"]
        received.mkdir(parents=True)
        self.downloaded_package = received / package.name
        shutil.copyfile(package, self.downloaded_package)
        return self.downloaded_package

    def metadata(self):
        run = {
            "id": 456, "workflow_id": 256058391, "run_attempt": 1,
            "path": ".github/workflows/vercel-production.yml", "event": "workflow_dispatch",
            "head_sha": SHA, "head_branch": "master", "status": "in_progress",
            "conclusion": None, "repository": {"full_name": REPOSITORY, "id": 99},
            "head_repository": {"full_name": REPOSITORY, "id": 99},
        }
        producer = {
            "name": "production-build", "run_id": 456, "run_attempt": 1,
            "head_sha": SHA, "status": "completed", "conclusion": "success",
        }
        return {
            "/git/ref/heads/master": {"object": {"sha": SHA}},
            "/actions/runs/456/attempts/1": run,
            "/actions/runs/456": deepcopy(run),
            "/actions/runs/456/attempts/1/jobs?per_page=100": {
                "total_count": 2, "jobs": [producer, producer | {
                    "name": "verify-production-bundle", "status": "in_progress",
                    "conclusion": None,
                }],
            },
            "/actions/artifacts/789": {
                "id": 789, "name": "production-bundle-456-1", "expired": False,
                "digest": "sha256:" + "b" * 64,
                "workflow_run": {"id": 456, "head_sha": SHA, "head_branch": "master",
                                 "repository_id": 99, "head_repository_id": 99},
            },
        }

    def verify(self, responses=None, overrides=None):
        return self.execute("verify", {"PACKAGE_SHA256": self.digest} | (overrides or {}),
                            self.metadata() if responses is None else responses)

    def rewrite_package(self, transform):
        path = self.downloaded_package
        with tarfile.open(path, "r:") as archive:
            entries = [(deepcopy(m), archive.extractfile(m).read() if m.isfile() else b"")
                       for m in archive.getmembers()]
        entries = transform(entries)
        with tarfile.open(path, "w:", format=tarfile.USTAR_FORMAT) as archive:
            for member, data in entries:
                member.size = len(data) if member.isfile() else 0
                archive.addfile(member, io.BytesIO(data) if member.isfile() else None)
        self.digest = hashlib.sha256(path.read_bytes()).hexdigest()

    def test_download_by_id_layout_matches_verifier(self):
        package = self.package_fixture()
        self.assertEqual(self.download_inputs["artifact-ids"],
                         "${{ steps.artifact-source.outputs.id }}")
        try:
            self.verify()
        except SystemExit as error:
            self.fail(f"Configured download layout does not reach BUNDLE_DIR: {error}")
        self.assertEqual(package.parent, self.bundle_dir)

    def test_round_trip_verifies_real_content_and_metadata_while_run_in_progress(self):
        self.package_fixture()
        requests = self.verify()
        self.assertIn("/actions/artifacts/789", requests)
        restored = self.root / "verified/output"
        for source in self.output.rglob("*"):
            target = restored / source.relative_to(self.output)
            self.assertEqual(target.is_dir(), source.is_dir())
            self.assertEqual(stat.S_IMODE(target.stat().st_mode),
                             stat.S_IMODE(source.stat().st_mode))
            self.assertEqual(int(target.stat().st_mtime), int(source.stat().st_mtime))
            if source.is_file():
                self.assertEqual(target.read_bytes(), source.read_bytes())
        self.assertFalse((self.root / "verified/project.json").exists())

    def test_rejects_context_and_package_hash_before_extraction(self):
        self.package_fixture()
        for field, value in (
            ("GITHUB_REPOSITORY", "other/repo"), ("GITHUB_SHA", "bad"),
            ("GITHUB_REF", "refs/heads/other"), ("GITHUB_EVENT_NAME", "push"),
            ("GITHUB_RUN_ID", "0"), ("GITHUB_RUN_ATTEMPT", "bad"),
            ("CI_RUN_ATTEMPT", "bad"), ("ARTIFACT_ID", "0"),
            ("PACKAGE_SHA256", "0" * 64), ("ZIP_DIGEST", "bad"),
        ):
            with self.subTest(field=field), self.assertRaises(SystemExit):
                self.verify(overrides={field: value})
            self.assertFalse((self.root / "verified").exists())

    def test_rejects_wrong_run_attempt_artifact_and_unsuccessful_producer(self):
        self.package_fixture()
        cases = []
        for path, field, value in (
            ("/actions/runs/456/attempts/1", "id", 999),
            ("/actions/runs/456/attempts/1", "workflow_id", 999),
            ("/actions/runs/456/attempts/1", "head_sha", "c" * 40),
            ("/actions/runs/456/attempts/1", "event", "pull_request"),
            ("/actions/runs/456/attempts/1", "repository", {"full_name": "other/repo"}),
            ("/actions/runs/456", "run_attempt", 2),
            ("/actions/artifacts/789", "id", 999),
            ("/actions/artifacts/789", "name", "latest"),
            ("/actions/artifacts/789", "expired", True),
            ("/actions/artifacts/789", "digest", "sha256:" + "0" * 64),
            ("/actions/artifacts/789", "workflow_run", {"id": 999}),
        ):
            data = self.metadata()
            data[path][field] = value
            cases.append(data)
        job_path = "/actions/runs/456/attempts/1/jobs?per_page=100"
        for field, value in (("conclusion", "failure"), ("status", "in_progress"),
                             ("run_attempt", 2), ("head_sha", "c" * 40)):
            data = self.metadata()
            data[job_path]["jobs"][0][field] = value
            cases.append(data)
        data = self.metadata()
        data[job_path]["total_count"] = 101
        cases.append(data)
        data = self.metadata()
        data["/actions/artifacts/789"] = URLError("unavailable")
        cases.append(data)
        for index, data in enumerate(cases):
            with self.subTest(case=index), self.assertRaises(SystemExit):
                self.verify(data)
            self.assertFalse((self.root / "verified").exists())

    def test_rejects_tampering_even_when_outer_package_hash_is_recomputed(self):
        package = self.package_fixture()
        original = package.read_bytes()
        for mutation in ("content", "mode", "mtime", "missing", "extra", "provenance",
                                 "provenance-type"):
            package.write_bytes(original)

            def change(entries):
                if mutation == "extra":
                    member = tarfile.TarInfo("output/unexpected.txt")
                    return entries + [(member, b"extra")]
                if mutation == "missing":
                    return [(m, b) for m, b in entries if m.name != "output/static/index.html"]
                changed = []
                for member, data in entries:
                    if member.name == "output/static/index.html":
                        if mutation == "content":
                            data = b"altered"
                        elif mutation == "mode":
                            member.mode ^= 0o100
                        elif mutation == "mtime":
                            member.mtime += 1
                    if member.name == "receipt.json" and mutation.startswith("provenance"):
                        receipt = json.loads(data)
                        receipt["provenance"]["ci_run_attempt"] = (
                            True if mutation == "provenance-type" else 2
                        )
                        data = json.dumps(receipt).encode()
                    changed.append((member, data))
                return changed

            self.rewrite_package(change)
            with self.subTest(mutation=mutation), self.assertRaises(SystemExit):
                self.verify()
            self.assertFalse((self.root / "verified").exists())

    def test_rejects_external_paths_links_special_types_and_duplicates_before_extraction(self):
        package = self.package_fixture()
        original = package.read_bytes()
        for name, kind, link in (
            ("../escape", tarfile.REGTYPE, ""), ("/absolute", tarfile.REGTYPE, ""),
            ("output/C:escape", tarfile.REGTYPE, ""),
            ("output/static/link", tarfile.SYMTYPE, "../../../escape"),
            ("output/static/link", tarfile.SYMTYPE, "index.html"),
            ("output/static/link", tarfile.LNKTYPE, "output/static/index.html"),
            ("output/static/pipe", tarfile.FIFOTYPE, ""),
            ("output/config.json", tarfile.REGTYPE, ""),
        ):
            package.write_bytes(original)
            member = tarfile.TarInfo(name)
            member.type, member.linkname = kind, link
            self.rewrite_package(lambda entries: entries + [(member, b"")])
            with self.subTest(name=name, kind=kind), self.assertRaises(SystemExit):
                self.verify()
            self.assertFalse((self.root / "verified").exists())
        self.assertFalse((self.root / "escape").exists())

    def test_unexpected_output_entry_reports_relative_path_before_packaging(self):
        (self.output / "unapproved-fixture.txt").write_bytes(b"fixture contents, never logged")
        with self.assertRaises(SystemExit) as rejected:
            self.execute("pack")
        self.assertFalse((self.root / "upload").exists())
        self.assertFalse((self.root / "job-output").exists())
        self.assertEqual(str(rejected.exception),
                         "Unexpected output entry: output/unapproved-fixture.txt")

    def test_invalid_output_paths_are_not_echoed_in_diagnostics(self):
        package = self.package_fixture()
        original = package.read_bytes()
        for name in (
            "/runner/private.txt", "output/\n::notice::forged", "output/\rforged",
            "output/\x1b[31mforged", "output/" + "x" * 135 + "/" + "y" * 100,
        ):
            package.write_bytes(original)
            member = tarfile.TarInfo(name)
            self.rewrite_package(lambda entries: entries + [(member, b"")])
            with self.subTest(name=name), self.assertRaises(SystemExit) as rejected:
                self.verify()
            self.assertEqual(str(rejected.exception), "External or unsupported output path")
            self.assertFalse((self.root / "verified").exists())

    def test_producer_rejects_unsupported_output_and_sensitive_file_names(self):
        for relative in (".env", "static/.env.local", "static/.npmrc", "cache/file",
                         "unexpected.txt"):
            path = self.output / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"not uploaded")
            with self.subTest(path=relative), self.assertRaises(SystemExit):
                self.execute("pack")
            path.unlink()
            if path.parent.name == "cache":
                path.parent.rmdir()
        settings = self.workspace / ".vercel/project.json"
        settings.write_text("{}", encoding="utf-8")
        with self.assertRaises(SystemExit):
            self.execute("pack")

    def test_rejects_inconsistent_parent_hierarchy_before_creating_destination(self):
        package = self.package_fixture()
        original = package.read_bytes()
        for file_parent in (False, True):
            package.write_bytes(original)

            def change(entries):
                changed = []
                for member, data in entries:
                    if member.name == "output/static":
                        if not file_parent:
                            continue
                        member.type = tarfile.REGTYPE
                    if member.name == "receipt.json":
                        receipt = json.loads(data)
                        if file_parent:
                            for entry in receipt["entries"]:
                                if entry["path"] == "output/static":
                                    entry.update(type="file", size=0,
                                                 sha256=hashlib.sha256(b"").hexdigest())
                        else:
                            receipt["entries"] = [e for e in receipt["entries"]
                                                  if e["path"] != "output/static"]
                        data = json.dumps(receipt).encode()
                    changed.append((member, data))
                return changed

            self.rewrite_package(change)
            with self.subTest(file_parent=file_parent):
                with self.assertRaises((SystemExit, OSError)):
                    self.verify()
                self.assertFalse((self.root / "verified").exists(),
                                 "Hierarchy must be checked before extraction")

    def test_producer_rejects_ustar_unrepresentable_names_before_package_creation(self):
        (self.output / "static" / ("x" * 101)).write_bytes(b"fixture")
        with self.assertRaises((SystemExit, ValueError)):
            self.execute("pack")
        self.assertFalse((self.root / "upload").exists())

    def test_size_limits_abort_without_upload_or_extraction(self):
        huge = self.output / "static/oversized.bin"
        with huge.open("wb") as stream:
            stream.truncate(64 * 1024**2 + 1)
        with self.assertRaisesRegex(SystemExit, "64 MiB"):
            self.execute("pack")
        self.assertFalse((self.root / "upload").exists())
        huge.unlink()
        package = self.package_fixture()
        with package.open("r+b") as stream:
            stream.truncate(80 * 1024**2 + 1)
        with self.assertRaisesRegex(SystemExit, "package size"):
            self.verify()
        self.assertFalse((self.root / "verified").exists())

    def test_verifier_detects_post_extraction_mtime_loss(self):
        self.package_fixture()
        real_utime = os.utime

        def corrupt(path, times):
            if Path(path).name == "index.html":
                times = (times[0], times[1] + 5)
            real_utime(path, times)

        with patch("os.utime", side_effect=corrupt), self.assertRaisesRegex(
            SystemExit, "Restored content or metadata mismatch"
        ):
            self.verify()

    def test_verifier_detects_post_extraction_content_or_metadata_loss(self):
        self.package_fixture()
        real_chmod = os.chmod

        def corrupt(path, mode, **kwargs):
            real_chmod(path, mode, **kwargs)
            if Path(path).name == "index.html":
                Path(path).write_bytes(b"corrupted after extraction")

        with patch("os.chmod", side_effect=corrupt), self.assertRaises(SystemExit):
            self.verify()


if __name__ == "__main__":
    unittest.main(verbosity=2)
