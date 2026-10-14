"""Static CI eligibility checks; no workflow commands or application code run here."""

import re
import unittest
from copy import deepcopy
from pathlib import Path

import yaml

EXPECTED_EVENTS = {
    "pull_request": {"branches": ["master"]},
    "push": {"branches": ["master"]},
}


class CILoader(yaml.SafeLoader):
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


CILoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
    list("tTfF"),
)


class TestCIWorkflowPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[2]
        cls.workflow = yaml.load(
            (root / ".github/workflows/ci.yml").read_text(encoding="utf-8"), Loader=CILoader
        )

    def assert_policy(self, workflow):
        self.assertEqual(set(workflow), {"name", "on", "permissions", "jobs"})
        self.assertEqual(workflow["name"], "ci")
        self.assertEqual(workflow["on"], EXPECTED_EVENTS)
        self.assertEqual(workflow["permissions"], {"contents": "read"})
        jobs = workflow["jobs"]
        self.assertEqual(set(jobs), {"python-quality", "web-quality"})
        for job in jobs.values():
            self.assertNotIn("if", job)
        self.assertNotIn("needs", jobs["python-quality"])
        self.assertEqual(jobs["web-quality"]["needs"], "python-quality")

    def valid_candidate(self):
        # Normalize only events in memory so negative cases also run during legacy RED.
        candidate = deepcopy(self.workflow)
        candidate["on"] = deepcopy(EXPECTED_EVENTS)
        self.assert_policy(candidate)
        return candidate

    def assert_rejected(self, candidate):
        parsed = yaml.load(yaml.safe_dump(candidate), Loader=CILoader)
        with self.assertRaises(AssertionError):
            self.assert_policy(parsed)

    def test_workflow_matches_availability_policy(self):
        self.assert_policy(self.workflow)

    def test_rejects_path_filters(self):
        for event in EXPECTED_EVENTS:
            for field in ("paths", "paths-ignore"):
                with self.subTest(event=event, field=field):
                    candidate = self.valid_candidate()
                    candidate["on"][event][field] = ["data/processed/analytics/web/**"]
                    self.assert_rejected(candidate)

    def test_rejects_conditional_jobs_and_dependency_changes(self):
        for name in ("python-quality", "web-quality"):
            for condition in ("false", False, "github.event_name == 'push'"):
                with self.subTest(job=name, condition=condition):
                    candidate = self.valid_candidate()
                    candidate["jobs"][name]["if"] = condition
                    self.assert_rejected(candidate)
        for needs in ("missing-quality", ["python-quality", "other"]):
            with self.subTest(needs=needs):
                candidate = self.valid_candidate()
                candidate["jobs"]["web-quality"]["needs"] = needs
                self.assert_rejected(candidate)
        candidate = self.valid_candidate()
        candidate["jobs"]["python-quality"]["needs"] = "web-quality"
        self.assert_rejected(candidate)

    def test_rejects_event_or_branch_changes(self):
        for event in ("workflow_dispatch", "pull_request_target", "workflow_run", "schedule"):
            with self.subTest(added_event=event):
                candidate = self.valid_candidate()
                candidate["on"][event] = None
                self.assert_rejected(candidate)
        for event in EXPECTED_EVENTS:
            with self.subTest(removed_event=event):
                candidate = self.valid_candidate()
                del candidate["on"][event]
                self.assert_rejected(candidate)
            for field, value in (
                ("branches", ["other"]),
                ("branches", ["master", "other"]),
                ("branches", ["**"]),
                ("branches-ignore", ["master"]),
            ):
                with self.subTest(event=event, field=field, value=value):
                    candidate = self.valid_candidate()
                    candidate["on"][event][field] = value
                    self.assert_rejected(candidate)

    def test_loader_is_safe_and_local(self):
        parsed = yaml.load("on: {}\nflag: true\nkeep: false\n", Loader=CILoader)
        self.assertEqual(parsed["on"], {})
        self.assertIs(parsed["flag"], True)
        self.assertIs(parsed["keep"], False)
        self.assertEqual(yaml.safe_load("on: false\n"), {True: False})
        for text in (
            "on: {}\non: {push: {branches: [other]}}\n",
            "on: {push: {branches: [master], branches: [other]}}\n",
            "jobs: {web-quality: {needs: a, needs: b}}\n",
            "!!python/tuple [blocked]",
        ):
            with self.subTest(yaml=text):
                with self.assertRaises(yaml.constructor.ConstructorError):
                    yaml.load(text, Loader=CILoader)

    def test_static_event_matrix(self):
        # After proving there are no path filters, paths cannot restrict this declaration.
        self.assertEqual(self.workflow["on"], EXPECTED_EVENTS)
        analytics = "data/processed/analytics/web/example.json"
        ml = "data/processed/ml/web/example.json"
        changes = (
            [analytics],
            [ml],
            [analytics, ml],
            ["src/ridefare/cli.py"],
            ["docs/runbooks/deployment.md"],
            [".github/workflows/ci.yml"],
            [analytics, ml, "src/ridefare/cli.py"],
        )
        cases = [(event, "master", paths, True) for event in EXPECTED_EVENTS for paths in changes]
        cases.extend((event, "other", [analytics], False) for event in EXPECTED_EVENTS)
        cases.extend(
            (event, "master", [analytics], False)
            for event in ("workflow_dispatch", "pull_request_target", "workflow_run", "schedule")
        )
        for event, branch, paths, expected in cases:
            with self.subTest(event=event, branch=branch, paths=paths):
                filters = self.workflow["on"].get(event, {})
                self.assertEqual(branch in filters.get("branches", []), expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
