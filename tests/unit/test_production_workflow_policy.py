"""Static Production Action pins only; not credential, promotion or deployment safety."""

import re
import unittest
from copy import deepcopy
from pathlib import Path

import yaml

EXPECTED_ACTIONS = [
    "actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09",
    "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1",
    "actions/setup-node@249970729cb0ef3589644e2896645e5dc5ba9c38",
]


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
            for step in workflow["jobs"]["production-deploy"]["steps"]
            if "uses" in step
        ]
        self.assertEqual(actual, EXPECTED_ACTIONS)

    def test_workflow_matches_approved_action_pins(self):
        self.assert_action_pins(self.workflow)

    def test_rejects_unapproved_action_references(self):
        # Normalize only references in memory so negatives also run during legacy RED.
        candidate = deepcopy(self.workflow)
        steps = candidate["jobs"]["production-deploy"]["steps"]
        actions = [step for step in steps if "uses" in step]
        for step, reference in zip(actions, EXPECTED_ACTIONS, strict=True):
            step["uses"] = reference
        self.assert_action_pins(candidate)
        for index, step in enumerate(steps):
            if "uses" not in step:
                continue
            repository, sha = step["uses"].split("@")
            references = [
                f"{repository}@{ref}"
                for ref in ("v5", "v6", "v5.1.0", "v6.3.0", "v6.5.0", "main", sha[:12], "0" * 40)
            ]
            references.append(f"other/{repository.split('/')[1]}@{sha}")
            for reference in references:
                with self.subTest(step=index, reference=reference):
                    invalid = deepcopy(candidate)
                    invalid["jobs"]["production-deploy"]["steps"][index]["uses"] = reference
                    parsed = yaml.load(yaml.safe_dump(invalid), Loader=ProductionLoader)
                    with self.assertRaises(AssertionError):
                        self.assert_action_pins(parsed)

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
