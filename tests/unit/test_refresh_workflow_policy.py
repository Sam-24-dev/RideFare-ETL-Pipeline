"""Static Refresh policy checks; never execute the pipeline or publish outputs."""

import re
import unittest
from copy import deepcopy
from pathlib import Path

import yaml

EXPECTED_WORKFLOW = {
    "name": "pipeline-refresh",
    "on": {
        "workflow_dispatch": None,
        "push": {
            "branches": ["master"],
            "paths": [
                "src/ridefare/**",
                "dbt/**",
                "data/samples/raw/**",
                "pyproject.toml",
                "scripts/refresh-public-artifacts.ps1",
                "apps/web/lib/data/**",
            ],
        },
    },
    "permissions": {"contents": "read"},
    "jobs": {
        "refresh-public-artifacts": {
            "runs-on": "ubuntu-latest",
            "steps": [
                {
                    "name": "Checkout repository",
                    "uses": "actions/checkout@v5",
                    "with": {"fetch-depth": 0, "persist-credentials": False},
                },
                {
                    "name": "Set up Python",
                    "uses": "actions/setup-python@v6",
                    "with": {"python-version": "3.13"},
                },
                {
                    "name": "Install Python dependencies",
                    "run": (
                        "python -m pip install --upgrade pip\n"
                        "python -m pip install -e .[data,ml,dev]\n"
                    ),
                },
                {
                    "name": "Refresh public artifacts",
                    "shell": "pwsh",
                    "run": "./scripts/refresh-public-artifacts.ps1 -RunId refresh-public",
                },
                {
                    "name": "Summarize artifact changes",
                    "shell": "bash",
                    "run": (
                        "git diff --stat -- data/processed/analytics/web data/processed/ml/web"
                    ),
                },
            ],
        }
    },
}


class RefreshLoader(yaml.SafeLoader):
    # Copy resolvers locally: YAML 1.1's bool pattern would consume the key `on`.
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


RefreshLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
    list("tTfF"),
)


class TestRefreshWorkflowPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[2]
        cls.workflow = yaml.load(
            (root / ".github/workflows/pipeline-refresh.yml").read_text(encoding="utf-8"),
            Loader=RefreshLoader,
        )

    def assert_policy(self, workflow):
        self.assertEqual(workflow, EXPECTED_WORKFLOW)
        checkout = workflow["jobs"]["refresh-public-artifacts"]["steps"][0]["with"]
        # Dict equality alone considers False equal to 0; require the actual YAML types.
        self.assertIs(checkout["persist-credentials"], False)
        self.assertIs(type(checkout["fetch-depth"]), int)

    def assert_rejected(self, workflow):
        parsed = yaml.load(yaml.safe_dump(workflow), Loader=RefreshLoader)
        with self.assertRaises(AssertionError):
            self.assert_policy(parsed)

    def test_workflow_matches_closed_policy(self):
        self.assert_policy(self.workflow)

    def test_workflow_permissions_are_read_only(self):
        self.assertEqual(self.workflow["permissions"], {"contents": "read"})

    def test_checkout_does_not_persist_credentials(self):
        checkout = self.workflow["jobs"]["refresh-public-artifacts"]["steps"][0]
        self.assertIs(checkout["with"].get("persist-credentials"), False)

    def test_run_commands_are_only_approved_operations(self):
        allowed = EXPECTED_WORKFLOW["jobs"]["refresh-public-artifacts"]["steps"]
        commands = [step["run"] for step in allowed if "run" in step]
        for step in self.workflow["jobs"]["refresh-public-artifacts"]["steps"]:
            if "run" in step:
                with self.subTest(step=step.get("name")):
                    self.assertIn(step["run"], commands)

    def test_loader_preserves_on_and_real_booleans_without_global_changes(self):
        self.assertEqual(
            yaml.load("on: {}\nyes: true\nno: false\n", Loader=RefreshLoader),
            {"on": {}, "yes": True, "no": False},
        )
        self.assertEqual(yaml.safe_load("on: false\n"), {True: False})
        with self.assertRaises(yaml.constructor.ConstructorError):
            yaml.load("!!python/tuple [blocked]", Loader=RefreshLoader)

    def test_rejects_permissions_credentials_and_extra_fields(self):
        mutations = (
            ("workflow", "permissions", {"contents": "write"}),
            ("workflow", "env", {"TOKEN": "${{ secrets.TOKEN }}"}),
            ("workflow", "defaults", {"run": {"shell": "bash"}}),
            ("job", "permissions", {"contents": "write"}),
            ("job", "secrets", "inherit"),
            ("job", "environment", "production"),
            ("job", "env", {"TOKEN": "${{ secrets.TOKEN }}"}),
            ("job", "continue-on-error", True),
            ("checkout", "with", {"fetch-depth": 0}),
            (
                "checkout", "with",
                {"fetch-depth": 0, "persist-credentials": False, "token": "${{ secrets.TOKEN }}"},
            ),
            ("checkout", "env", {"GH_TOKEN": "${{ secrets.TOKEN }}"}),
            ("summary", "if", "false"),
            ("summary", "id", "artifact-diff"),
            ("summary", "continue-on-error", True),
        )
        for scope, field, value in mutations:
            with self.subTest(scope=scope, field=field):
                candidate = deepcopy(EXPECTED_WORKFLOW)
                job = candidate["jobs"]["refresh-public-artifacts"]
                targets = {
                    "workflow": candidate,
                    "job": job,
                    "checkout": job["steps"][0],
                    "summary": job["steps"][-1],
                }
                targets[scope][field] = value
                self.assert_rejected(candidate)
        for value in (True, "false", 0, None):
            with self.subTest(persist_credentials=value):
                candidate = deepcopy(EXPECTED_WORKFLOW)
                candidate["jobs"]["refresh-public-artifacts"]["steps"][0]["with"][
                    "persist-credentials"
                ] = value
                self.assert_rejected(candidate)

    def test_rejects_publication_commands_and_additional_steps(self):
        for command in (
            "git config user.name bot",
            "git add data/processed",
            'git commit -m "refresh [skip ci]"',
            "git push",
            "gh api --method POST repos/owner/repo/releases",
            "curl --request POST https://example.invalid/publish",
            'echo "[skip ci]"',
            "git diff --stat; git push",
        ):
            with self.subTest(command=command):
                candidate = deepcopy(EXPECTED_WORKFLOW)
                candidate["jobs"]["refresh-public-artifacts"]["steps"][-1]["run"] = command
                self.assert_rejected(candidate)
        for step in (
            {"uses": "actions/upload-artifact@v4"},
            {"uses": "actions/github-script@v8"},
            {"run": "git push"},
        ):
            with self.subTest(step=step):
                candidate = deepcopy(EXPECTED_WORKFLOW)
                candidate["jobs"]["refresh-public-artifacts"]["steps"].append(step)
                self.assert_rejected(candidate)

    def test_rejects_expanded_triggers_or_filters(self):
        for event in ("pull_request", "pull_request_target", "workflow_run", "schedule"):
            with self.subTest(event=event):
                candidate = deepcopy(EXPECTED_WORKFLOW)
                candidate["on"][event] = {}
                self.assert_rejected(candidate)
        for field, value in (("branches", ["master", "other"]), ("paths", ["**"])):
            with self.subTest(field=field):
                candidate = deepcopy(EXPECTED_WORKFLOW)
                candidate["on"]["push"][field] = value
                self.assert_rejected(candidate)

    def test_rejects_duplicate_yaml_keys(self):
        for text in (
            "permissions: {contents: read}\npermissions: {contents: write}\n",
            "on:\n  push:\n    branches: [master]\n    branches: ['**']\n",
            "with:\n  persist-credentials: false\n  persist-credentials: true\n",
        ):
            with self.subTest(yaml=text):
                with self.assertRaisesRegex(
                    yaml.constructor.ConstructorError, "duplicate YAML key"
                ):
                    yaml.load(text, Loader=RefreshLoader)

    def test_static_event_matrix_uses_loaded_filters(self):
        # Only these fixed recursive-directory/exact-file filters, not an Actions engine.
        self.assertEqual(self.workflow["on"], EXPECTED_WORKFLOW["on"])
        cases = [
            ("workflow_dispatch", "master", [], True),
            ("workflow_dispatch", "other", [], True),
            ("push", "other", ["pyproject.toml"], False),
            ("pull_request", "master", ["pyproject.toml"], False),
            ("workflow_run", "master", ["pyproject.toml"], False),
            ("push", "master", [], False),
            ("push", "master", ["README.md", "pyproject.toml"], True),
        ]
        included = (
            "src/ridefare/cli.py",
            "dbt/models/example.sql",
            "data/samples/raw/PFDA_rides.csv",
            "pyproject.toml",
            "scripts/refresh-public-artifacts.ps1",
            "apps/web/lib/data/example.ts",
        )
        excluded = (
            "README.md",
            "docs/runbooks/deployment.md",
            ".github/workflows/pipeline-refresh.yml",
            "tests/unit/test_refresh_workflow_policy.py",
            "data/processed/analytics/web/result.json",
            "data/processed/ml/web/result.json",
            "apps/web/app/page.tsx",
        )
        cases.extend(("push", "master", [path], True) for path in included)
        cases.extend(("push", "master", [path], False) for path in excluded)
        for event, branch, paths, expected in cases:
            with self.subTest(event=event, branch=branch, paths=paths):
                filters = self.workflow["on"].get("push", {})
                matched = any(
                    path.startswith(pattern[:-2]) if pattern.endswith("**") else path == pattern
                    for path in paths
                    for pattern in filters.get("paths", [])
                )
                admitted = event == "workflow_dispatch" and event in self.workflow["on"]
                admitted |= event == "push" and branch in filters.get("branches", []) and matched
                self.assertEqual(admitted, expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
