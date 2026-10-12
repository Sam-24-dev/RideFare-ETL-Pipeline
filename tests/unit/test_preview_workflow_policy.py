"""Static Preview boundary checks; these do not validate the application."""

import unittest
from copy import deepcopy
from pathlib import Path

import yaml

NOTICE = (
    "Automatic PR previews are not deployed by this workflow. "
    "This is an informational notice, not application validation."
)
EXPECTED_WORKFLOW = {
    "name": "vercel-preview",
    "on": {
        "pull_request": {
            "branches": ["master"],
            "types": ["opened", "synchronize", "reopened"],
        }
    },
    "permissions": {},
    "jobs": {
        "preview-policy": {
            "runs-on": "ubuntu-latest",
            "steps": [{"shell": "bash", "run": f'echo "{NOTICE}"'}],
        }
    },
}


class PreviewLoader(yaml.SafeLoader):
    # Keep YAML 1.1's boolean resolver from consuming `on`, without global changes.
    yaml_implicit_resolvers = {
        key: [(tag, pattern) for tag, pattern in resolvers if tag != "tag:yaml.org,2002:bool"]
        for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
    }

    def construct_mapping(self, node, deep=False):
        self.flatten_mapping(node)
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise yaml.constructor.ConstructorError(
                    None, None, "workflow keys must be strings", key_node.start_mark
                )
            if key in mapping:
                raise yaml.constructor.ConstructorError(
                    None, None, f"duplicate YAML key: {key}", key_node.start_mark
                )
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


class TestPreviewWorkflowPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[2]
        cls.workflow = yaml.load(
            (root / ".github/workflows/vercel-preview.yml").read_text(encoding="utf-8"),
            Loader=PreviewLoader,
        )

    def assert_policy(self, workflow):
        # Exact equality closes every level, including the entire command string.
        self.assertEqual(workflow, EXPECTED_WORKFLOW)

    def assert_rejected(self, workflow):
        parsed = yaml.load(yaml.safe_dump(workflow), Loader=PreviewLoader)
        with self.assertRaises(AssertionError):
            self.assert_policy(parsed)

    def test_workflow_matches_closed_policy(self):
        self.assert_policy(self.workflow)

    def test_workflow_permissions_are_empty(self):
        self.assertEqual(self.workflow.get("permissions"), {})

    def test_jobs_have_no_credentials_or_permission_overrides(self):
        for name, job in self.workflow["jobs"].items():
            for field in ("env", "environment", "secrets", "permissions"):
                with self.subTest(job=name, field=field):
                    self.assertNotIn(
                        field, job.keys(), f"{name}.{field} is forbidden: {job.get(field)!r}"
                    )

    def test_rejects_credentials_permissions_and_surface_extensions(self):
        mutations = (
            ("workflow", "permissions", {"contents": "write"}),
            ("workflow", "env", {"NOTICE": "fixed"}),
            ("workflow", "defaults", {"run": {"shell": "bash"}}),
            ("job", "permissions", {"pull-requests": "write"}),
            ("job", "env", {"TOKEN": "${{ secrets.VERCEL_TOKEN }}"}),
            ("job", "environment", "preview"),
            ("job", "secrets", "inherit"),
            ("job", "if", "false"),
            ("job", "container", "alpine"),
            ("job", "services", {"database": {"image": "postgres"}}),
            ("job", "strategy", {"matrix": {"version": ["3.13"]}}),
            ("job", "needs", "another-job"),
            ("job", "continue-on-error", True),
            ("job", "runs-on", "windows-latest"),
            ("step", "uses", "actions/checkout@v5"),
            ("step", "uses", "actions/setup-python@v6"),
            ("step", "env", {"NOTICE": "fixed"}),
            ("step", "continue-on-error", True),
            ("step", "working-directory", "."),
            ("step", "shell", "pwsh"),
        )
        for scope, field, value in mutations:
            with self.subTest(scope=scope, field=field, value=value):
                candidate = deepcopy(EXPECTED_WORKFLOW)
                job = candidate["jobs"]["preview-policy"]
                target = {"workflow": candidate, "job": job, "step": job["steps"][0]}[scope]
                target[field] = value
                self.assert_rejected(candidate)

    def test_rejects_reusable_workflow_additional_job_or_step(self):
        for change in ("reusable", "additional-job", "additional-step"):
            with self.subTest(change=change):
                candidate = deepcopy(EXPECTED_WORKFLOW)
                job = candidate["jobs"]["preview-policy"]
                if change == "reusable":
                    candidate["jobs"]["preview-policy"] = {"uses": "./.github/workflows/ci.yml"}
                elif change == "additional-job":
                    candidate["jobs"]["another-job"] = deepcopy(job)
                else:
                    job["steps"].append(deepcopy(job["steps"][0]))
                self.assert_rejected(candidate)

    def test_rejects_any_other_run_command(self):
        for command in (
            "pwd",
            f'echo "{NOTICE}"; pwd',
            f'echo "{NOTICE}"\ntrue',
            'echo "${{ secrets.VERCEL_TOKEN }}"',
            'echo "${{ github.event.pull_request.title }}"',
            'echo "$HOME"',
            'echo "$(pwd)"',
            'echo "`pwd`"',
        ):
            with self.subTest(command=command):
                candidate = deepcopy(EXPECTED_WORKFLOW)
                candidate["jobs"]["preview-policy"]["steps"][0]["run"] = command
                self.assert_rejected(candidate)

    def test_rejects_other_triggers(self):
        for event in ("pull_request_target", "workflow_run", "push", "workflow_dispatch"):
            for replace in (False, True):
                with self.subTest(event=event, replace=replace):
                    candidate = deepcopy(EXPECTED_WORKFLOW)
                    candidate["on"] = {event: {}} if replace else {**candidate["on"], event: {}}
                    self.assert_rejected(candidate)

    def test_rejects_duplicate_yaml_keys(self):
        for text in (
            "permissions: {}\npermissions: {contents: write}\n",
            "jobs:\n  preview-policy:\n    env: {}\n    env: {TOKEN: blocked}\n",
            "jobs:\n  preview-policy:\n    steps:\n      - run: echo safe\n        run: pwd\n",
        ):
            with self.subTest(yaml=text):
                with self.assertRaisesRegex(
                    yaml.constructor.ConstructorError, "duplicate YAML key"
                ):
                    yaml.load(text, Loader=PreviewLoader)

    def test_loader_preserves_on_without_changing_safe_loader(self):
        self.assertEqual(yaml.load("on: {}\n", Loader=PreviewLoader), {"on": {}})
        self.assertEqual(yaml.safe_load("on: {}\n"), {True: {}})

    def test_loader_rejects_python_tags(self):
        with self.assertRaises(yaml.constructor.ConstructorError):
            yaml.load("!!python/tuple [blocked]", Loader=PreviewLoader)

    def test_static_event_matrix_uses_loaded_yaml_filters(self):
        # Filters only: no claim about GitHub execution, fork approval or effective secrets.
        self.assertEqual(self.workflow["on"], EXPECTED_WORKFLOW["on"])
        cases = (
            ("pull_request", "master", "opened", True),
            ("pull_request", "master", "synchronize", True),
            ("pull_request", "master", "reopened", True),
            ("pull_request", "another-branch", "opened", False),
            ("pull_request", "master", "closed", False),
            ("push", "master", "opened", False),
        )
        for origin in ("same-repository", "fork", "dependabot"):
            for event, branch, action, expected in cases:
                with self.subTest(origin=origin, event=event, branch=branch, action=action):
                    filters = self.workflow["on"].get(event, {})
                    admitted = branch in filters.get("branches", []) and action in filters.get(
                        "types", []
                    )
                    self.assertEqual(admitted, expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
