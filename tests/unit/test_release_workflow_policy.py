"""Static Release Please policy checks; never run the action or publish a release."""

import re
import unittest
from copy import deepcopy
from pathlib import Path

import yaml

ACTION = "googleapis/release-please-action@5c625bfb5d1ff62eadeeb3772007f7f66fdcf071"
EXPECTED_WORKFLOW = {
    "name": "release-please",
    "on": {"push": {"branches": ["master"]}},
    "permissions": {"contents": "write", "pull-requests": "write"},
    "concurrency": {"group": "release-please-master", "cancel-in-progress": False},
    "jobs": {
        "release-please": {
            "runs-on": "ubuntu-latest",
            "steps": [
                {
                    "name": "Run release-please",
                    "uses": ACTION,
                    "with": {
                        "config-file": "release-please-config.json",
                        "manifest-file": ".release-please-manifest.json",
                        "skip-github-release": True,
                    },
                }
            ],
        }
    },
}


class ReleaseLoader(yaml.SafeLoader):
    # Keep `on` and real booleans without modifying SafeLoader's global resolvers.
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


ReleaseLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
    list("tTfF"),
)


class TestReleaseWorkflowPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[2]
        cls.workflow = yaml.load(
            (root / ".github/workflows/release-please.yml").read_text(encoding="utf-8"),
            Loader=ReleaseLoader,
        )

    def assert_policy(self, workflow):
        self.assertEqual(workflow, EXPECTED_WORKFLOW)
        inputs = workflow["jobs"]["release-please"]["steps"][0]["with"]
        # Mapping equality alone treats True/False as equal to 1/0.
        self.assertIs(inputs["skip-github-release"], True)
        self.assertIs(workflow["concurrency"]["cancel-in-progress"], False)

    def assert_rejected(self, candidate):
        parsed = yaml.load(yaml.safe_dump(candidate), Loader=ReleaseLoader)
        with self.assertRaises(AssertionError):
            self.assert_policy(parsed)

    def test_workflow_matches_closed_pr_only_policy(self):
        step = self.workflow["jobs"]["release-please"]["steps"][0]
        self.assertEqual(step["uses"], ACTION)
        self.assert_policy(self.workflow)

    def test_rejects_mutable_or_different_action_references(self):
        for reference in (
            "googleapis/release-please-action@v4",
            "googleapis/release-please-action@v4.4.1",
            "googleapis/release-please-action@main",
            "googleapis/release-please-action@" + "a" * 40,
            ACTION[:-1],
            ACTION.replace("googleapis/", "other-owner/"),
        ):
            with self.subTest(reference=reference):
                candidate = deepcopy(EXPECTED_WORKFLOW)
                candidate["jobs"]["release-please"]["steps"][0]["uses"] = reference
                self.assert_rejected(candidate)

    def test_rejects_missing_false_or_non_boolean_release_flag(self):
        candidate = deepcopy(EXPECTED_WORKFLOW)
        del candidate["jobs"]["release-please"]["steps"][0]["with"]["skip-github-release"]
        self.assert_rejected(candidate)
        for value in (False, 0, 1, "true", "false", None, []):
            with self.subTest(value=value):
                candidate = deepcopy(EXPECTED_WORKFLOW)
                candidate["jobs"]["release-please"]["steps"][0]["with"][
                    "skip-github-release"
                ] = value
                self.assert_rejected(candidate)

    def test_rejects_missing_or_changed_concurrency(self):
        candidate = deepcopy(EXPECTED_WORKFLOW)
        del candidate["concurrency"]
        self.assert_rejected(candidate)
        for field, value in (
            ("group", "other"),
            ("group", "${{ github.ref }}"),
            ("cancel-in-progress", True),
            ("cancel-in-progress", 0),
            ("cancel-in-progress", "false"),
            ("cancel-in-progress", None),
        ):
            with self.subTest(field=field, value=value):
                candidate = deepcopy(EXPECTED_WORKFLOW)
                candidate["concurrency"][field] = value
                self.assert_rejected(candidate)

    def test_rejects_event_or_branch_changes(self):
        for event in ("pull_request", "pull_request_target", "workflow_dispatch", "release"):
            with self.subTest(event=event):
                candidate = deepcopy(EXPECTED_WORKFLOW)
                candidate["on"][event] = None
                self.assert_rejected(candidate)
        for filters in (
            {"branches": ["master", "other"]},
            {"branches": ["other"]},
            {"branches": ["**"]},
            {"branches-ignore": ["master"]},
            {"branches": ["master"], "paths": ["**"]},
        ):
            with self.subTest(filters=filters):
                candidate = deepcopy(EXPECTED_WORKFLOW)
                candidate["on"]["push"] = filters
                self.assert_rejected(candidate)

    def test_rejects_permissions_credentials_inputs_and_extra_fields(self):
        for scope, field, value in (
            ("workflow", "permissions", {"contents": "read", "pull-requests": "write"}),
            (
                "workflow", "permissions",
                {"contents": "write", "pull-requests": "write", "issues": "write"},
            ),
            ("workflow", "env", {"GH_TOKEN": "${{ secrets.TOKEN }}"}),
            ("workflow", "defaults", {"run": {"shell": "bash"}}),
            ("job", "permissions", {"contents": "write"}),
            ("job", "runs-on", "self-hosted"),
            ("job", "if", "false"),
            ("job", "environment", "production"),
            ("job", "secrets", "inherit"),
            ("step", "env", {"GH_TOKEN": "${{ secrets.TOKEN }}"}),
            ("step", "if", "false"),
            ("step", "continue-on-error", True),
            ("inputs", "token", "${{ secrets.TOKEN }}"),
            ("inputs", "skip-github-pull-request", False),
            ("inputs", "config-file", "other.json"),
            ("inputs", "manifest-file", "other.json"),
            ("inputs", "release-as", "9.0.0"),
        ):
            with self.subTest(scope=scope, field=field):
                candidate = deepcopy(EXPECTED_WORKFLOW)
                job = candidate["jobs"]["release-please"]
                step = job["steps"][0]
                targets = {"workflow": candidate, "job": job, "step": step, "inputs": step["with"]}
                targets[scope][field] = value
                self.assert_rejected(candidate)

    def test_rejects_additional_jobs_or_steps(self):
        extra = {"uses": "actions/checkout@v5"}
        candidate = deepcopy(EXPECTED_WORKFLOW)
        candidate["jobs"]["release-please"]["steps"].append(extra)
        self.assert_rejected(candidate)
        candidate = deepcopy(EXPECTED_WORKFLOW)
        candidate["jobs"]["publish"] = {"runs-on": "ubuntu-latest", "steps": [extra]}
        self.assert_rejected(candidate)

    def test_rejects_tag_release_and_publication_commands(self):
        for command in (
            "git tag v9.0.0", "git push --tags", "gh release create v9.0.0", "npm publish",
        ):
            with self.subTest(command=command):
                for additional_step in (False, True):
                    candidate = deepcopy(EXPECTED_WORKFLOW)
                    steps = candidate["jobs"]["release-please"]["steps"]
                    if additional_step:
                        steps.append({"run": command})
                    else:
                        steps[0]["run"] = command
                    self.assert_rejected(candidate)

    def test_loader_is_safe_and_local(self):
        parsed = yaml.load("on: {}\nyes: true\nno: false\n", Loader=ReleaseLoader)
        self.assertEqual(parsed["on"], {})
        self.assertIs(parsed["yes"], True)
        self.assertIs(parsed["no"], False)
        self.assertEqual(yaml.safe_load("on: false\n"), {True: False})
        for text in ("!!python/tuple [blocked]", "!untrusted blocked"):
            with self.subTest(yaml=text):
                with self.assertRaises(yaml.constructor.ConstructorError):
                    yaml.load(text, Loader=ReleaseLoader)

    def test_rejects_duplicate_yaml_keys(self):
        for text in (
            "permissions: {}\npermissions: {contents: write}\n",
            "on: {push: {branches: [master], branches: [other]}}\n",
            "with: {skip-github-release: true, skip-github-release: false}\n",
            "concurrency: {group: release-please-master, group: other}\n",
            "steps: [{uses: pinned, uses: mutable}]\n",
        ):
            with self.subTest(yaml=text):
                with self.assertRaisesRegex(
                    yaml.constructor.ConstructorError, "duplicate YAML key"
                ):
                    yaml.load(text, Loader=ReleaseLoader)


if __name__ == "__main__":
    unittest.main(verbosity=2)
