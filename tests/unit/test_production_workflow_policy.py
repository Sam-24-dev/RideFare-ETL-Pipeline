"""Static build-boundary policy; mocked GitHub reads, no application or Vercel execution."""

import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
import unittest
from contextlib import redirect_stdout
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
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
    'node "$RUNNER_TEMP/ridefare-vercel-cli/node_modules/vercel/dist/vc.js" '
    'build --prod --global-config "$RUNNER_TEMP/ridefare-vercel-build"\n'
)
TOOLING_DIRECTORY = "${{ runner.temp }}/ridefare-vercel-cli"
TOOLING_PREPARE_RUN = (
    'test ! -e "$RUNNER_TEMP/ridefare-vercel-cli"\n'
    'mkdir "$RUNNER_TEMP/ridefare-vercel-cli"\n'
    'cp "$GITHUB_WORKSPACE/scripts/vercel-cli/package.json" '
    '"$GITHUB_WORKSPACE/scripts/vercel-cli/package-lock.json" '
    '"$RUNNER_TEMP/ridefare-vercel-cli/"\n'
)
TOOLING_INSTALL_STEP = {
    "name": "Install Vercel CLI", "shell": "bash", "working-directory": TOOLING_DIRECTORY,
    "run": "npm ci --ignore-scripts --no-audit --no-fund --registry=https://registry.npmjs.org/",
}
TOOLING_CHECK_RUN = """node --input-type=commonjs - <<'JS'
const fs = require('node:fs');
const path = require('node:path');
const { createRequire } = require('node:module');
const root = fs.realpathSync(path.join(process.env.RUNNER_TEMP, 'ridefare-vercel-cli'));
function metadata(directory, name, version) {
  const value = JSON.parse(fs.readFileSync(path.join(directory, 'package.json'), 'utf8'));
  if (value.name !== name || value.version !== version
      || fs.realpathSync(directory) !== directory) {
    throw new Error('Unexpected isolated tooling package');
  }
  return value;
}
const cli = path.join(root, 'node_modules/vercel');
const cliMetadata = metadata(cli, 'vercel', '50.39.0');
const bin = path.join(cli, 'dist/vc.js');
if (cliMetadata.bin.vercel !== 'dist/vc.js' || fs.realpathSync(bin) !== bin) {
  throw new Error('Unexpected isolated CLI bin');
}
const fromCli = createRequire(path.join(cli, 'package.json'));
const fun = path.join(root, 'node_modules/@vercel/fun');
const funManifest = path.join(fun, 'package.json');
if (fs.realpathSync(fromCli.resolve('@vercel/fun/package.json')) !== funManifest) {
  throw new Error('Unexpected fun resolution');
}
if (metadata(fun, '@vercel/fun', '1.3.6').dependencies.tar !== '7.5.22') {
  throw new Error('Unexpected fun tar dependency');
}
const tar = path.join(root, 'node_modules/tar');
metadata(tar, 'tar', '7.5.22');
const tarEntry = path.join(tar, 'dist/commonjs/index.min.js');
for (const helper of ['install-node.js', 'install-python.js']) {
  const helperPath = path.join(fun, 'dist/src', helper);
  if (!fs.lstatSync(helperPath, { throwIfNoEntry: false })?.isFile()
      || fs.realpathSync(helperPath) !== helperPath) {
    throw new Error('Unexpected fun helper file');
  }
  const fromFun = createRequire(helperPath);
  if (fs.realpathSync(fromFun.resolve('tar')) !== tarEntry
      || typeof fromFun('tar').extract !== 'function') {
    throw new Error('Unexpected tar resolution from fun helper');
  }
}
console.log('Isolated Vercel CLI 50.39.0; @vercel/fun 1.3.6; tar 7.5.22');
JS
"""


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
        self.assertEqual(len(steps), 15)
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
            {"name": "Prepare isolated Vercel CLI", "shell": "bash", "run": TOOLING_PREPARE_RUN},
            TOOLING_INSTALL_STEP,
            {"name": "Verify isolated Vercel CLI", "shell": "bash",
             "working-directory": TOOLING_DIRECTORY, "run": TOOLING_CHECK_RUN},
            {"name": "Prepare public Vercel settings", "shell": "bash", "run": SETTINGS_RUN},
            {"name": "Build production bundle", "shell": "bash", "run": BUILD_RUN},
        ]
        self.assertEqual(steps[1:13], expected)
        self.assertIs(steps[1]["with"]["persist-credentials"], False)
        self.assertEqual(job["outputs"], {
            "artifact_id": "${{ steps.bundle-upload.outputs.artifact-id }}",
            "zip_digest": "${{ steps.bundle-upload.outputs.artifact-digest }}",
            "package_sha256": "${{ steps.bundle.outputs.package_sha256 }}",
        })
        package = steps[13]
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
        self.assertEqual(steps[14], {
            "name": "Upload production bundle", "id": "bundle-upload",
            "uses": EXPECTED_ACTIONS[3],
            "with": {
                "name": "production-bundle-${{ github.run_id }}-${{ github.run_attempt }}",
                "path": "${{ runner.temp }}/ridefare-transfer-upload/production-bundle.tar",
                "if-no-files-found": "error", "retention-days": 1, "overwrite": False,
            },
        })
        self.assertIs(steps[14]["with"]["overwrite"], False)
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

    def test_tooling_manifest_and_lock_are_frozen(self):
        root = Path(__file__).resolve().parents[2] / "scripts/vercel-cli"
        expected = {
            "package.json": (
                213, "30d8dfadbac1f455b3e3d28929ae0b18ea4efacd16bc13d564655e18b56e523b"
            ),
            "package-lock.json": (
                149198, "84e18b74050fe736779437bc6a90a4a605c6bef2acad09e9017568c39fc909db"
            ),
        }
        documents = {}
        for name, (size, digest) in expected.items():
            data = (root / name).read_bytes().replace(b"\r\n", b"\n")
            self.assertEqual(len(data), size)
            self.assertEqual(hashlib.sha256(data).hexdigest(), digest)
            documents[name] = json.loads(data)
        self.assertEqual(documents["package.json"], {
            "name": "ridefare-vercel-fun-probe", "version": "0.0.0", "private": True,
            "dependencies": {"vercel": "50.39.0"},
            "overrides": {"vercel@50.39.0": {"@vercel/fun": "1.3.6"}},
        })
        lock = documents["package-lock.json"]
        self.assertEqual(lock["lockfileVersion"], 3)
        packages = lock["packages"]
        self.assertEqual(packages[""]["dependencies"], {"vercel": "50.39.0"})
        for name, version in (("vercel", "50.39.0"), ("@vercel/fun", "1.3.6"), ("tar", "7.5.22")):
            self.assertEqual(packages[f"node_modules/{name}"]["version"], version)
        self.assertEqual(packages["node_modules/vercel"]["dependencies"]["@vercel/fun"], "1.3.0")
        self.assertEqual(packages["node_modules/@vercel/fun"]["dependencies"]["tar"], "7.5.22")
        self.assertFalse(any(package.get("link") for package in packages.values()))
        self.assertFalse(any(
            package.get("resolved", "").startswith("file:") for package in packages.values()
        ))

    def test_tooling_identity_accepts_lf_and_crlf_checkouts(self):
        root = Path(__file__).resolve().parents[2] / "scripts/vercel-cli"
        canonical = {
            root / name: (root / name).read_bytes().replace(b"\r\n", b"\n")
            for name in ("package.json", "package-lock.json")
        }
        for manifest_crlf, lock_crlf in (
            (False, False), (True, False), (False, True), (True, True)
        ):
            simulated = {}
            for name, crlf, size in (
                ("package.json", manifest_crlf, 226 if manifest_crlf else 213),
                ("package-lock.json", lock_crlf, 153328 if lock_crlf else 149198),
            ):
                path = root / name
                simulated[path] = (
                    canonical[path].replace(b"\n", b"\r\n") if crlf else canonical[path]
                )
                self.assertEqual(len(simulated[path]), size)
            with self.subTest(manifest_crlf=manifest_crlf, lock_crlf=lock_crlf):
                with patch.object(Path, "read_bytes", autospec=True,
                                  side_effect=lambda path: simulated[path]):
                    self.test_tooling_manifest_and_lock_are_frozen()

    def test_tooling_identity_rejects_other_byte_changes(self):
        root = Path(__file__).resolve().parents[2] / "scripts/vercel-cli"
        canonical = {
            root / name: (root / name).read_bytes().replace(b"\r\n", b"\n")
            for name in ("package.json", "package-lock.json")
        }
        for path, data in canonical.items():
            mutations = {
                "BOM": b"\xef\xbb\xbf" + data,
                "isolated CR": b"\r" + data,
                "extra byte": data + b"x",
                "extra space": data + b" ",
                "extra newline": data + b"\n",
                "same-size whitespace": data.replace(b"  ", b"\t ", 1),
                "same-size content": data.replace(b"0.0.0", b"0.0.1", 1),
            }
            for name, changed in mutations.items():
                for crlf in (False, True):
                    simulated = dict(canonical)
                    simulated[path] = changed.replace(b"\n", b"\r\n") if crlf else changed
                    with self.subTest(file=path.name, mutation=name, crlf=crlf):
                        with patch.object(Path, "read_bytes", autospec=True,
                                          side_effect=lambda path: simulated[path]):
                            with self.assertRaises(AssertionError):
                                self.test_tooling_manifest_and_lock_are_frozen()

    def test_tooling_installation_is_isolated(self):
        step = next(step for step in self.workflow["jobs"]["production-build"]["steps"]
                    if step["name"] == "Install Vercel CLI")
        self.assertEqual(step, TOOLING_INSTALL_STEP)

    def test_tooling_build_uses_explicit_cli_bin(self):
        step = next(step for step in self.workflow["jobs"]["production-build"]["steps"]
                    if step["name"] == "Build production bundle")
        self.assertEqual(step, {
            "name": "Build production bundle", "shell": "bash",
            "run": BUILD_RUN,
        })

    def test_tooling_copy_uses_validated_checkout(self):
        steps = self.workflow["jobs"]["production-build"]["steps"]
        self.assertEqual(steps[8], {
            "name": "Prepare isolated Vercel CLI", "shell": "bash", "run": TOOLING_PREPARE_RUN,
        })
        self.assertEqual(steps[10], {
            "name": "Verify isolated Vercel CLI", "shell": "bash",
            "working-directory": TOOLING_DIRECTORY, "run": TOOLING_CHECK_RUN,
        })
        self.assertEqual(steps[7], {
            "name": "Install workspace dependencies",
            "run": "corepack pnpm install --frozen-lockfile",
        })

    def test_rejects_tooling_installation_and_executable_bypasses(self):
        mutations = [
            (8, "run", TOOLING_PREPARE_RUN.replace("$GITHUB_WORKSPACE", "$RUNNER_TEMP")),
            (8, "run", TOOLING_PREPARE_RUN.replace("package-lock.json", "other-lock.json")),
            (9, "run", "npm install --global vercel@50.39.0"),
            (9, "run", TOOLING_INSTALL_STEP["run"].replace("--ignore-scripts", "")),
            (9, "run", TOOLING_INSTALL_STEP["run"] + " --prefix ."),
            (9, "working-directory", "apps/web"),
            (10, "working-directory", "${{ github.workspace }}"),
            (10, "run", TOOLING_CHECK_RUN.replace("fromFun.resolve", "fromCli.resolve")),
            (12, "run", BUILD_RUN.replace(
                'node "$RUNNER_TEMP/ridefare-vercel-cli/node_modules/vercel/dist/vc.js"', "vercel"
            )),
            (12, "run", BUILD_RUN.replace("node ", "npx ")),
            (12, "run", BUILD_RUN.replace("vercel/dist/vc.js", "vercel/other.js")),
            (12, "run", BUILD_RUN + "vercel build --prod\n"),
        ]
        for index, key, value in mutations:
            bad = deepcopy(self.workflow)
            bad["jobs"]["production-build"]["steps"][index][key] = value
            with self.subTest(step=index, key=key), self.assertRaises(AssertionError):
                self.assert_policy(bad)

    def run_tooling_check(self, mutation=None):
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node is required for the inline tooling-check fixtures")
        step = self.workflow["jobs"]["production-build"]["steps"][10]
        script = step["run"].split("\n", 1)[1].removesuffix("JS\n")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "ridefare-vercel-cli"
            modules = root / "node_modules"
            packages = {
                "vercel": {"name": "vercel", "version": "50.39.0", "bin": {"vercel": "dist/vc.js"}},
                "@vercel/fun": {"name": "@vercel/fun", "version": "1.3.6",
                                "dependencies": {"tar": "7.5.22"}},
                "tar": {"name": "tar", "version": "7.5.22", "main": "dist/commonjs/index.min.js"},
            }
            for name, data in packages.items():
                directory = modules / name
                directory.mkdir(parents=True)
                (directory / "package.json").write_text(json.dumps(data), encoding="utf-8")
            files = {
                "vercel/dist/vc.js": "throw new Error('CLI must not execute');\n",
                "@vercel/fun/dist/src/install-node.js": "throw new Error('Do not execute');\n",
                "@vercel/fun/dist/src/install-python.js": "throw new Error('Do not execute');\n",
                "tar/dist/commonjs/index.min.js": "exports.extract = function () {};\n",
            }
            for name, content in files.items():
                file = modules / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text(content, encoding="utf-8")
            if mutation:
                mutation(modules)
            environment = {
                key: os.environ[key] for key in ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATH")
                if key in os.environ
            }
            environment["RUNNER_TEMP"] = temp
            return subprocess.run(
                [node, "--input-type=commonjs", "-"], input=script, cwd=root,
                env=environment, capture_output=True, encoding="utf-8", timeout=10, check=False,
            )

    def test_inline_tooling_check_accepts_expected_resolution(self):
        result = self.run_tooling_check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout.strip(),
                         "Isolated Vercel CLI 50.39.0; @vercel/fun 1.3.6; tar 7.5.22")

    def test_inline_tooling_check_rejects_absent_or_directory_helpers(self):
        for helper in ("install-node.js", "install-python.js"):
            for directory in (False, True):
                def mutate(modules, helper=helper, directory=directory):
                    file = modules / "@vercel/fun/dist/src" / helper
                    file.unlink()
                    if directory:
                        file.mkdir()

                with self.subTest(helper=helper, directory=directory):
                    result = self.run_tooling_check(mutate)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("Unexpected fun helper file", result.stderr)
                    self.assertEqual(result.stdout, "")

    def test_inline_tooling_check_rejects_wrong_versions_dependencies_and_bin(self):
        for name, field, value, error in (
            ("vercel", "version", "50.39.1", "Unexpected isolated tooling package"),
            ("@vercel/fun", "version", "1.3.0", "Unexpected isolated tooling package"),
            ("tar", "version", "7.5.7", "Unexpected isolated tooling package"),
            ("@vercel/fun", "dependencies", {"tar": "7.5.7"}, "Unexpected fun tar dependency"),
            ("vercel", "bin", {"vercel": "other.js"}, "Unexpected isolated CLI bin"),
        ):
            def mutate(modules, name=name, field=field, value=value):
                file = modules / name / "package.json"
                data = json.loads(file.read_text(encoding="utf-8"))
                data[field] = value
                file.write_text(json.dumps(data), encoding="utf-8")

            with self.subTest(package=name, field=field):
                result = self.run_tooling_check(mutate)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(error, result.stderr)
                self.assertEqual(result.stdout, "")

    def test_inline_tooling_check_rejects_shadow_copies_and_invalid_exports(self):
        def shadow_fun(modules):
            shutil.copytree(modules / "@vercel/fun", modules / "vercel/node_modules/@vercel/fun")

        def shadow_tar(modules):
            shutil.copytree(modules / "tar", modules / "@vercel/fun/dist/src/node_modules/tar")

        def invalid_tar(modules):
            (modules / "tar/dist/commonjs/index.min.js").write_text(
                "exports.extract = null;\n", encoding="utf-8"
            )

        for mutation, error in (
            (shadow_fun, "Unexpected fun resolution"),
            (shadow_tar, "Unexpected tar resolution from fun helper"),
            (invalid_tar, "Unexpected tar resolution from fun helper"),
        ):
            with self.subTest(mutation=mutation.__name__):
                result = self.run_tooling_check(mutation)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(error, result.stderr)
                self.assertEqual(result.stdout, "")

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
        (self.output / "builds.json").write_text(
            '{"target":"production","cliVersion":"50.39.0","builds":[{}]}\n', encoding="utf-8")
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
                redirect_stdout(io.StringIO()) as output:
            exec(compile(code, "<production-bundle-transfer>", "exec"), {})
        self.report = json.loads(output.getvalue())
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

    def test_projects_builds_json_without_changing_source(self):
        source = self.output / "builds.json"
        original, before = source.read_bytes(), source.lstat()
        package = self.package_fixture()
        with tarfile.open(package, "r:") as archive:
            self.assertEqual(archive.extractfile("output/builds.json").read(),
                             b'{"target":"production"}')
        self.assertEqual(source.read_bytes(), original)
        for key in ("st_ino", "st_nlink", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns"):
            self.assertEqual(getattr(source.lstat(), key), getattr(before, key))
        self.verify()
        self.assertEqual((self.root / "verified/output/builds.json").read_bytes(),
                         b'{"target":"production"}')

    def test_omits_only_static_trace_and_preserves_routing(self):
        trace = self.output / "static/_next/__private/trace"
        trace.parent.mkdir(parents=True)
        trace.write_bytes(b"synthetic diagnostic fixture")
        neighbor = trace.with_name("trace-extra")
        neighbor.write_bytes(b"selected neighbor")
        config = self.output / "config.json"
        routing = b'{"version":3,"routes":[{"src":"/_next/__private/trace",' \
                  b'"dest":"/404","status":404,"continue":true}]}\n'
        config.write_bytes(routing)
        package = self.package_fixture()
        with tarfile.open(package, "r:") as archive:
            self.assertNotIn("output/static/_next/__private/trace", archive.getnames())
            self.assertEqual(archive.extractfile("output/config.json").read(), routing)
            self.assertEqual(archive.extractfile("output/static/_next/__private/trace-extra").read(),
                             b"selected neighbor")
        self.assertTrue(trace.is_file())
        self.assertEqual(config.read_bytes(), routing)
        self.verify()
        self.assertEqual((self.root / "verified/output/config.json").read_bytes(), routing)
        self.assertFalse((self.root / "verified/output/static/_next/__private/trace").exists())

    def rewrite_payload_file(self, name, data, kind=tarfile.REGTYPE):
        def transform(entries):
            receipt = json.loads(next(d for m, d in entries if m.name == "receipt.json"))
            result = [(m, d) for m, d in entries if m.name not in (name, "receipt.json")]
            receipt["entries"] = [e for e in receipt["entries"] if e["path"] != name]
            if data is not None:
                member = tarfile.TarInfo(name)
                member.type, member.mode = kind, 0o644
                receipt["entries"].append({
                    "path": name, "type": "directory" if kind == tarfile.DIRTYPE else "file",
                    "mode": member.mode, "mtime": 0, "size": len(data),
                    "sha256": None if kind == tarfile.DIRTYPE else hashlib.sha256(data).hexdigest(),
                })
                result.append((member, data))
            receipt["entries"].sort(key=lambda e: e["path"])
            header = next(m for m, _ in entries if m.name == "receipt.json")
            return [(header, json.dumps(receipt).encode()), *result]
        self.rewrite_package(transform)

    def test_opaque_build_metadata_is_discarded_without_public_fingerprint(self):
        source = self.output / "builds.json"
        marker = "SYNTHETIC_DISCARDED_METADATA"
        original = json.dumps({
            "target": "production", "cliVersion": "50.39.0",
            "builds": [{"apiVersion": [], "use": 7, "config": {"error": marker},
                        "requirePath": {"opaque": marker}}, {}],
            "argv": {"opaque": marker}, "features": [marker], "//": None,
            "future_metadata": {"error": marker},
        }).encode()
        source.write_bytes(original)
        before = source.lstat()
        package = self.package_fixture()
        public = json.dumps(self.report) + (self.root / "job-output").read_text(encoding="utf-8")
        for discarded in (marker, hashlib.sha256(original).hexdigest()):
            self.assertNotIn(discarded, public)
            self.assertNotIn(discarded.encode(), package.read_bytes())
        self.assertEqual(source.read_bytes(), original)
        for field in ("st_ino", "st_nlink", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns"):
            self.assertEqual(getattr(source.lstat(), field), getattr(before, field))
        with tarfile.open(package, "r:") as archive:
            self.assert_selection(json.load(archive.extractfile("receipt.json")), "absent")
            member = archive.getmember("output/builds.json")
            self.assertEqual(member.mode, stat.S_IMODE(before.st_mode))
            self.assertEqual(member.mtime, int(before.st_mtime))
            self.assertEqual(archive.extractfile(member).read(), b'{"target":"production"}')
        self.verify()

    def test_invalid_original_build_metadata_fails_closed(self):
        valid = {"target": "production", "cliVersion": "50.39.0", "builds": [{}]}
        cases = [b"", b"{", b"[]", b"null", b"false", b"1", b'"text"',
                 b"\xef\xbb\xbf" + json.dumps(valid).encode(), b"\xff",
                 json.dumps(valid).encode() + b" {}",
                 b'{"target":"preview","target":"production"}',
                 b'{"target":"production","targ\\u0065t":"production"}',
                 b'{"target":"production","cliVersion":"50.39.0","builds":[{}],'
                 b'"opaque":{"same":1,"same":2}}']
        for field, values in (("target", (None, True, 0, [], {}, "preview", "production ")),
                              ("cliVersion", (None, True, 50.39, [], {}, "50.39.1")),
                              ("builds", (None, False, {}, [], [None], [False], [1], ["builder"]))):
            cases.append(json.dumps({k: v for k, v in valid.items() if k != field}).encode())
            cases.extend(json.dumps(valid | {field: value}).encode() for value in values)
        for token in (b"NaN", b"Infinity", b"-Infinity", b"1e999"):
            cases.append(json.dumps(valid).encode()[:-1] + b',"opaque":' + token + b"}")
        for index, data in enumerate(cases):
            (self.output / "builds.json").write_bytes(data)
            with self.subTest(case=index), self.assertRaises(SystemExit) as error:
                self.execute("pack")
            self.assertIn(str(error.exception), ("Invalid metadata JSON", "Duplicate JSON key",
                                                 "Invalid original build controls"))
            self.assertFalse((self.root / "upload").exists())
            self.assertFalse((self.root / "job-output").exists())

    def test_every_original_error_key_is_rejected_even_when_falsey(self):
        valid = {"target": "production", "cliVersion": "50.39.0", "builds": [{}]}
        for value in (None, False, 0, "", [], {}, "SYNTHETIC_ERROR"):
            candidates = [valid | {"error": value}, valid | {"builds": [{"error": value}]},
                          valid | {"builds": [{}, {"error": value}]},
                          valid | {"builds": [{"error": value}, {"error": "later error"}]}]
            for index, candidate in enumerate(candidates):
                (self.output / "builds.json").write_bytes(json.dumps(candidate).encode())
                with self.subTest(value=value, position=index), self.assertRaisesRegex(
                    SystemExit, "^Invalid original build controls$"
                ):
                    self.execute("pack")
                self.assertFalse((self.root / "upload").exists())
                self.assertFalse((self.root / "job-output").exists())

    def test_original_build_metadata_is_required_readable_and_regular(self):
        source = self.output / "builds.json"
        original = source.read_bytes()
        source.unlink()
        with self.assertRaises(SystemExit):
            self.execute("pack")
        source.mkdir()
        with self.assertRaisesRegex(SystemExit, "Build metadata must be a regular file"):
            self.execute("pack")
        source.rmdir()
        source.write_bytes(original)
        real_open, real_lstat = os.open, Path.lstat
        for operation in ("open", "lstat"):
            def denied(path, *args, **kwargs):
                if Path(path) == source:
                    raise PermissionError("SYNTHETIC_UNDISCLOSED_DETAIL")
                return (real_open if operation == "open" else real_lstat)(path, *args, **kwargs)
            with self.subTest(operation=operation), patch.object(
                os if operation == "open" else Path,
                "open" if operation == "open" else "lstat", denied
            ), self.assertRaises(SystemExit) as error:
                self.execute("pack")
            self.assertNotIn("SYNTHETIC_UNDISCLOSED_DETAIL", str(error.exception))
        self.assertFalse((self.root / "upload").exists())
        self.assertFalse((self.root / "job-output").exists())

    def test_original_change_with_identical_projection_aborts_before_hash(self):
        source = self.output / "builds.json"
        original = b'{"target":"production","cliVersion":"50.39.0","builds":[{}],"opaque":1}'
        real_addfile, real_lstat, real_fstat = tarfile.TarFile.addfile, Path.lstat, os.fstat
        for phase in ("receipt.json", "output/static/index.html"):
            source.write_bytes(original)
            before = source.lstat()
            changed = False

            def lstat(path, *args, **kwargs):
                return before if path == source else real_lstat(path, *args, **kwargs)

            def fstat(fd):
                info = real_fstat(fd)
                same_file = (info.st_dev, info.st_ino) == (before.st_dev, before.st_ino)
                return before if same_file else info

            def mutate(archive, member, stream=None):
                nonlocal changed
                result = real_addfile(archive, member, stream)
                if member.name == phase:
                    source.write_bytes(original.replace(b'"opaque":1', b'"opaque":2'))
                    changed = True
                return result

            output = self.root / ("job-" + phase.replace("/", "-"))
            with self.subTest(phase=phase), patch.object(Path, "lstat", lstat), \
                    patch("os.fstat", side_effect=fstat), \
                    patch.object(tarfile.TarFile, "addfile", mutate), self.assertRaises(SystemExit):
                self.execute("pack", {"BUNDLE_DIR": str(output) + "-bundle",
                                      "GITHUB_OUTPUT": str(output)})
            self.assertTrue(changed)
            self.assertFalse(output.exists())

    def test_static_trace_is_metadata_only_and_absence_is_not_omission(self):
        trace = self.output / "static/_next/__private/trace"
        trace.parent.mkdir(parents=True)
        trace.write_bytes(b"not opened by producer")
        before = trace.lstat()
        real_open, real_os_open = Path.open, os.open

        def guard(operation):
            def checked(path, *args, **kwargs):
                self.assertNotEqual(Path(path), trace, "Excluded trace bytes must not be read")
                return operation(path, *args, **kwargs)
            return checked

        with patch.object(Path, "open", guard(real_open)), \
                patch("os.open", side_effect=guard(real_os_open)):
            self.package_fixture()
            self.assertEqual(self.report["selection"]["static_trace"]["state"], "omitted")
            self.verify()
        after = trace.lstat()
        for field in ("st_ino", "st_nlink", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns"):
            self.assertEqual(getattr(after, field), getattr(before, field))
        trace.unlink()
        self.execute("pack", {"BUNDLE_DIR": str(self.root / "absent-trace")})
        self.assertEqual(self.report["selection"]["static_trace"]["state"], "absent")

    def test_static_trace_invalid_metadata_or_access_never_becomes_absent(self):
        trace = self.output / "static/_next/__private/trace"
        trace.parent.mkdir(parents=True)
        trace.write_bytes(b"unread fixture")
        real_lstat = Path.lstat
        changes = [{"st_mode": mode} for mode in (stat.S_IFDIR | 0o755,
                   stat.S_IFLNK | 0o777, stat.S_IFIFO | 0o600, stat.S_IFREG | 0o4644)]
        changes += [{"st_nlink": value} for value in (0, -1, True, 1.5)]
        for index, fields in enumerate([*changes, None]):
            def metadata(path, *args, **kwargs):
                if path == trace:
                    if fields is None:
                        raise PermissionError("private fixture detail")
                    return self.changed_stat(real_lstat(path), **fields)
                return real_lstat(path, *args, **kwargs)
            with self.subTest(case=index), patch.object(Path, "lstat", metadata), \
                    self.assertRaises(SystemExit):
                self.execute("pack")
            self.assertFalse((self.root / "upload").exists())
            self.assertFalse((self.root / "job-output").exists())

    def test_static_trace_metadata_change_during_packaging_aborts(self):
        trace = self.output / "static/_next/__private/trace"
        trace.parent.mkdir(parents=True)
        trace.write_bytes(b"unread fixture")
        real_lstat = Path.lstat
        calls = 0

        def metadata(path, *args, **kwargs):
            nonlocal calls
            info = real_lstat(path, *args, **kwargs)
            if path == trace:
                calls += 1
                if calls == 2:
                    return self.changed_stat(info, st_nlink=info.st_nlink + 1)
            return info

        with patch.object(Path, "lstat", metadata), self.assertRaises(SystemExit):
            self.execute("pack")
        self.assertEqual(calls, 2)
        self.assertFalse((self.root / "job-output").exists())

    def test_consumer_requires_canonical_build_metadata_despite_coherent_hashes(self):
        package = self.package_fixture()
        original = package.read_bytes()
        for value in (None, b"{}", b'{"target":"preview"}', b'{"target":"Production"}',
                      b'{"target":"production"}\n',
                      b'{"target":"production","argv":[]}',
                      b'{"target":"production","target":"production"}'):
            package.write_bytes(original)
            self.rewrite_payload_file("output/builds.json", value)
            with self.subTest(value=value), self.assertRaises(SystemExit):
                self.verify()
            self.assertFalse((self.root / "verified").exists())

    def test_consumer_rejects_trace_and_descendants_with_coherent_inventory(self):
        trace = "output/static/_next/__private/trace"
        (self.output / "static/_next/__private").mkdir(parents=True)
        package = self.package_fixture()
        original = package.read_bytes()
        for state in ("absent", "omitted"):
            for descendant in (False, True):
                package.write_bytes(original)
                self.rewrite_payload_file(trace, b"" if descendant else b"fixture",
                                          tarfile.DIRTYPE if descendant else tarfile.REGTYPE)
                if descendant:
                    self.rewrite_payload_file(trace + "/child", b"fixture")
                def declaration(entries):
                    for member, data in entries:
                        if member.name == "receipt.json":
                            receipt = json.loads(data)
                            receipt["selection"]["static_trace"]["state"] = state
                            data = json.dumps(receipt).encode()
                        yield member, data
                self.rewrite_package(lambda entries: list(declaration(entries)))
                with self.subTest(state=state, descendant=descendant), self.assertRaisesRegex(
                    SystemExit, "Excluded static trace"
                ):
                    self.verify()
                self.assertFalse((self.root / "verified").exists())

    def test_original_size_limit_is_checked_before_projection_or_read(self):
        source = self.output / "builds.json"
        real_lstat, real_open = Path.lstat, os.open

        def metadata(path, *args, **kwargs):
            info = real_lstat(path, *args, **kwargs)
            return self.changed_stat(info, st_size=64 * 1024**2 + 1) if path == source else info

        def guarded_open(path, *args, **kwargs):
            self.assertNotEqual(Path(path), source)
            return real_open(path, *args, **kwargs)

        with patch.object(Path, "lstat", metadata), patch("os.open", side_effect=guarded_open), \
                self.assertRaisesRegex(SystemExit, "64 MiB"):
            self.execute("pack")
        self.assertFalse((self.root / "upload").exists())
        self.assertFalse((self.root / "job-output").exists())

    def test_source_hardlinks_round_trip_as_independent_regular_files(self):
        source = self.output / "static/index.html"
        second = self.output / "static/second.html"
        second.hardlink_to(source)
        os.utime(source, (1700000000, 1700000000))
        before = source.lstat()
        contents = source.read_bytes()
        self.assertTrue(os.path.samefile(source, second))
        self.assertEqual(before.st_nlink, 2)
        try:
            package = self.package_fixture()
        except SystemExit as error:
            self.fail(f"Expected independent regular bytes from real hard links, got: {error}")
        self.assertEqual(self.report["source_regular_files_with_multiple_links"], 2)
        self.assertEqual(self.report["payload_links"], 0)
        with tarfile.open(package, "r:") as archive:
            receipt = json.load(archive.extractfile("receipt.json"))
            self.assertEqual(receipt["version"], 5)
            self.assertEqual(receipt["selection"]["regular_files"], "independent-bytes")
            self.assertFalse(any(m.islnk() for m in archive))
            for path in ("output/static/index.html", "output/static/second.html"):
                member = archive.getmember(path)
                self.assertEqual(member.type, tarfile.REGTYPE)
                self.assertEqual(member.size, len(contents))
                self.assertEqual(archive.extractfile(member).read(), contents)
        self.verify()
        restored = self.root / "verified/output/static"
        self.assertFalse(os.path.samefile(restored / source.name, restored / second.name))
        for path in (source, second):
            target = restored / path.name
            self.assertEqual(target.read_bytes(), contents)
            self.assertEqual(target.lstat().st_nlink, 1)
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), stat.S_IMODE(before.st_mode))
            self.assertEqual(int(target.stat().st_mtime), int(before.st_mtime))
            after = path.lstat()
            for key in ("st_dev", "st_ino", "st_nlink", "st_mode", "st_size",
                        "st_mtime_ns", "st_ctime_ns"):
                self.assertEqual(getattr(after, key), getattr(before, key))
            self.assertEqual(path.read_bytes(), contents)
        self.assertTrue(os.path.samefile(source, second))

    def test_source_hardlink_counterpart_outside_payload_is_never_accessed(self):
        source = self.output / "static/index.html"
        outside = self.root / "unselected-counterpart.bin"
        outside.hardlink_to(source)
        before = outside.lstat()
        original_open, original_os_open = Path.open, os.open
        original_lstat, original_iterdir = Path.lstat, Path.iterdir

        def guard(operation):
            def checked(path, *args, **kwargs):
                self.assertNotEqual(Path(path), outside, "No lookup of an unselected inode name")
                return operation(path, *args, **kwargs)
            return checked

        with patch.object(Path, "open", guard(original_open)), \
                patch("os.open", side_effect=guard(original_os_open)), \
                patch.object(Path, "lstat", guard(original_lstat)), \
                patch.object(Path, "iterdir", guard(original_iterdir)):
            try:
                package = self.package_fixture()
            except SystemExit as error:
                self.fail(f"Expected selected-path-only materialization, got: {error}")
            self.assertEqual(self.report["source_regular_files_with_multiple_links"], 1)
            self.verify()
        with tarfile.open(package, "r:") as archive:
            self.assertNotIn(outside.name, archive.getnames())
        self.assertTrue(os.path.samefile(source, outside))
        for key in ("st_dev", "st_ino", "st_nlink", "st_mode", "st_size",
                    "st_mtime_ns", "st_ctime_ns"):
            self.assertEqual(getattr(outside.lstat(), key), getattr(before, key))

    def test_materialized_size_limit_counts_each_selected_path_not_inodes(self):
        source = self.output / "static/large.bin"
        with source.open("wb") as stream:
            stream.truncate(32 * 1024**2 + 1)
        (source.parent / "second-large.bin").hardlink_to(source)
        with self.assertRaisesRegex(SystemExit, "64 MiB"):
            self.execute("pack")
        self.assertFalse((self.root / "upload").exists())
        self.assertFalse((self.root / "job-output").exists())

    @staticmethod
    def changed_stat(info, **changes):
        fields = ("st_dev", "st_ino", "st_mode", "st_nlink", "st_size",
                  "st_mtime", "st_mtime_ns", "st_ctime_ns")
        return SimpleNamespace(**({k: getattr(info, k) for k in fields} | changes))

    def test_regular_source_invalid_link_counts_fail_before_open(self):
        source = self.output / "static/index.html"
        original_lstat, original_open = Path.lstat, os.open
        for value in (0, -1, True, 1.5):
            def metadata(path, *args, **kwargs):
                info = original_lstat(path, *args, **kwargs)
                return self.changed_stat(info, st_nlink=value) if path == source else info

            def guarded_open(path, *args, **kwargs):
                self.assertNotEqual(Path(path), source)
                return original_open(path, *args, **kwargs)

            with self.subTest(nlink=value), patch.object(Path, "lstat", metadata), \
                    patch("os.open", side_effect=guarded_open), self.assertRaises(SystemExit):
                self.execute("pack")
            self.assertFalse((self.root / "upload").exists())
            self.assertFalse((self.root / "job-output").exists())

    def test_regular_source_fstat_identity_and_metadata_must_stay_stable(self):
        source = self.output / "static/index.html"
        info = source.lstat()
        real_fstat = os.fstat
        changes = {"st_nlink": 2, "st_dev": info.st_dev + 1, "st_ino": info.st_ino + 1,
                   "st_mode": stat.S_IFLNK | 0o777, "st_size": info.st_size + 1,
                   "st_mtime_ns": info.st_mtime_ns + 1, "st_ctime_ns": info.st_ctime_ns + 1}
        for phase in (1, 2, 3, 4):  # Before/after inventory hashing and package reading.
            for field, value in changes.items():
                calls = 0

                def changed(fd):
                    nonlocal calls
                    current = real_fstat(fd)
                    if (current.st_dev, current.st_ino) == (info.st_dev, info.st_ino):
                        calls += 1
                        if calls == phase:
                            return self.changed_stat(current, **{field: value})
                    return current

                label = f"{phase}-{field}"
                output = self.root / f"job-{label}"
                with self.subTest(phase=phase, field=field), \
                        patch("os.fstat", side_effect=changed), self.assertRaises(SystemExit):
                    self.execute("pack", {"BUNDLE_DIR": str(self.root / label),
                                          "GITHUB_OUTPUT": str(output)})
                self.assertFalse(output.exists(), "No usable hash after source instability")

    def test_regular_source_replacement_by_symlink_or_new_inode_fails_before_read(self):
        source = self.output / "static/index.html"
        saved = source.parent / "original.bin"
        outside = self.root / "unselected.bin"
        outside.write_bytes(b"never read by packaging")
        real_open = os.open
        contents = source.read_bytes()
        for symlink in (True, False):
            def replace(path, *args, **kwargs):
                if Path(path) == source:
                    source.rename(saved)
                    if symlink:
                        os.symlink(outside, source)
                    else:
                        source.write_bytes(contents)
                return real_open(path, *args, **kwargs)

            with self.subTest(symlink=symlink), patch("os.open", side_effect=replace), \
                    self.assertRaises(SystemExit):
                self.execute("pack")
            self.assertFalse((self.root / "upload").exists())
            self.assertFalse((self.root / "job-output").exists())
            source.unlink()
            saved.rename(source)

    def test_regular_source_content_changes_during_read_or_packaging_abort(self):
        source = self.output / "static/index.html"
        contents = source.read_bytes()
        real_fstat, real_addfile = os.fstat, tarfile.TarFile.addfile
        for phase in ("read", "pack"):
            changed = False
            calls = 0

            def mutate():
                nonlocal changed
                times = source.stat()
                source.write_bytes(b"X" * len(contents))
                os.utime(source, ns=(times.st_atime_ns, times.st_mtime_ns))
                changed = True

            def after_read(fd):
                nonlocal calls
                if os.path.samestat(real_fstat(fd), source.lstat()):
                    calls += 1
                    if phase == "read" and calls == 2:
                        mutate()
                return real_fstat(fd)

            def packaging(archive, member, stream=None):
                result = real_addfile(archive, member, stream)
                if phase == "pack" and member.name == "output/static/index.html":
                    mutate()
                return result

            output = self.root / f"job-{phase}"
            with self.subTest(phase=phase), patch("os.fstat", side_effect=after_read), \
                    patch.object(tarfile.TarFile, "addfile", packaging), \
                    self.assertRaises(SystemExit):
                self.execute("pack", {"BUNDLE_DIR": str(self.root / phase),
                                      "GITHUB_OUTPUT": str(output)})
            self.assertTrue(changed)
            self.assertFalse(output.exists())
            source.write_bytes(contents)

    def test_consumer_rejects_tar_hardlink_with_matching_declared_inventory(self):
        self.package_fixture()
        name, target = "output/static/index.html", "output/config.json"

        def adulterate(entries):
            for member, data in entries:
                if member.name == name:
                    member.type, member.linkname = tarfile.LNKTYPE, target
                if member.name == "receipt.json":
                    receipt = json.loads(data)
                    for entry in receipt["entries"]:
                        if entry["path"] == name:
                            entry.update(type="hardlink", size=0, sha256=None, target=target)
                    data = json.dumps(receipt).encode()
                yield member, data

        self.rewrite_package(lambda entries: list(adulterate(entries)))
        with self.assertRaisesRegex(SystemExit, "Unsupported archive link"):
            self.verify()
        self.assertFalse((self.root / "verified").exists())

    def test_consumer_rejects_reconstructed_regular_file_with_multiple_links(self):
        self.package_fixture()
        restored = self.root / "verified/output/static/index.html"
        real_chmod = os.chmod

        def link_after_write(path, mode):
            real_chmod(path, mode)
            if Path(path) == restored:
                (self.root / "outside-restored.bin").hardlink_to(path)

        with patch("os.chmod", side_effect=link_after_write), self.assertRaises(SystemExit):
            self.verify()
        self.assertEqual(restored.lstat().st_nlink, 2)

    def test_internal_func_alias_round_trip_without_traversal_or_source_changes(self):
        functions = self.output / "functions"
        target = functions / "canonical.func"
        target.mkdir(parents=True)
        code = target / "code.bin"
        code.write_bytes(b"synthetic function bytes, never executed")
        alias = functions / "nested/alias.func"
        alias.parent.mkdir()
        os.symlink("../canonical.func", alias, target_is_directory=True)
        sources = (functions, target, code, alias.parent, alias)
        before = [(p.lstat().st_mode, p.lstat().st_size, p.lstat().st_mtime_ns) for p in sources]
        original_open, original_iterdir = Path.open, Path.iterdir
        original_chmod, original_utime = os.chmod, os.utime
        restored_alias = self.root / "verified/output/functions/nested/alias.func"

        def no_alias_access(path):
            for link in (alias, restored_alias):
                self.assertFalse(path == link or link in path.parents, "Do not traverse aliases")

        def guarded_open(path, *args, **kwargs):
            no_alias_access(path)
            return original_open(path, *args, **kwargs)

        def guarded_iterdir(path):
            no_alias_access(path)
            return original_iterdir(path)

        def guarded_chmod(path, mode):
            no_alias_access(Path(path))
            original_chmod(path, mode)

        def guarded_utime(path, times):
            no_alias_access(Path(path))
            original_utime(path, times)

        with patch.object(Path, "open", guarded_open), \
                patch.object(Path, "iterdir", guarded_iterdir), \
                patch("os.chmod", side_effect=guarded_chmod), \
                patch("os.utime", side_effect=guarded_utime):
            try:
                package = self.package_fixture()
            except SystemExit as error:
                self.fail(f"Expected internal .func alias packaging, got: {error}")
            self.verify()
        with tarfile.open(package, "r:") as archive:
            stream = archive.extractfile("receipt.json")
            assert stream is not None
            receipt = json.load(stream)
            self.assertEqual(receipt["version"], 5)
            member = archive.getmember("output/functions/nested/alias.func")
            self.assertTrue(member.issym())
            self.assertEqual(member.linkname, "../canonical.func")
            self.assertFalse(any(n.startswith(member.name + "/") for n in archive.getnames()))
            entry = next(e for e in receipt["entries"] if e["path"] == member.name)
            self.assertEqual(entry, {
                "path": member.name, "type": "func-alias", "target": "../canonical.func",
                "mode": 0o777, "size": 0, "mtime": 0, "sha256": None,
            })
        self.assertTrue(restored_alias.is_symlink())
        self.assertEqual(os.readlink(restored_alias), "../canonical.func")
        self.assertEqual(before, [(p.lstat().st_mode, p.lstat().st_size, p.lstat().st_mtime_ns)
                                  for p in sources])
        restored_code = self.root / "verified/output/functions/canonical.func/code.bin"
        self.assertEqual(restored_code.read_bytes(), code.read_bytes())
        self.assertEqual(stat.S_IMODE(restored_code.stat().st_mode),
                         stat.S_IMODE(code.stat().st_mode))
        self.assertEqual(int(restored_code.stat().st_mtime), int(code.stat().st_mtime))

    def func_alias_fixture(self):
        target = self.output / "functions/real.func"
        target.mkdir(parents=True)
        (target / "code.bin").write_bytes(b"synthetic function, never executed")
        alias = target.parent / "alias.func"
        os.symlink("real.func", alias, target_is_directory=True)
        return alias, target

    def test_producer_rejects_unsafe_func_alias_targets_before_packaging(self):
        alias, target = self.func_alias_fixture()
        (target.parent / "file.func").write_bytes(b"not a directory")
        cases = ("/absolute.func", "../../outside.func", "../diagnostics", "../static",
                 "missing.func", "file.func", "alias.func", "./real.func",
                 "real.func/../real.func", "real.func/", "C:/outside.func",
                 "real\\func", "bad\n.func", "x" * 96 + ".func")
        original_lstat = Path.lstat

        def confined_lstat(path, *args, **kwargs):
            self.assertTrue(path == self.workspace or self.workspace in path.parents)
            return original_lstat(path, *args, **kwargs)

        for value in cases:
            alias.unlink()
            os.symlink(value, alias, target_is_directory=True)
            with self.subTest(target=value), patch.object(Path, "lstat", confined_lstat), \
                    self.assertRaises(SystemExit):
                self.execute("pack")
            self.assertFalse((self.root / "upload").exists())
            self.assertFalse((self.root / "job-output").exists())

    def test_producer_rejects_alias_chains_cycles_and_symbolic_intermediate_components(self):
        alias, target = self.func_alias_fixture()
        (target / "nested.func").mkdir()
        bridge = target.parent / "bridge.func"
        original_lstat = Path.lstat

        def no_bridge_traversal(path, *args, **kwargs):
            self.assertNotIn(bridge, path.parents)
            return original_lstat(path, *args, **kwargs)

        for link, bridge_link in (("bridge.func", "real.func"),
                                  ("bridge.func", "alias.func"),
                                  ("bridge.func/nested.func", "real.func")):
            alias.unlink()
            os.symlink(link, alias, target_is_directory=True)
            os.symlink(bridge_link, bridge, target_is_directory=True)
            with self.subTest(target=link, bridge=bridge_link), \
                    patch.object(Path, "lstat", no_bridge_traversal), self.assertRaises(SystemExit):
                self.execute("pack")
            bridge.unlink()
            self.assertFalse((self.root / "upload").exists())
            self.assertFalse((self.root / "job-output").exists())

    def test_producer_rejects_other_symlinks_and_special_types(self):
        target = self.output / "functions/real.func"
        target.mkdir(parents=True)
        moved = self.output / "static/real-functions"
        for relative in ("static/alias.func", "functions/alias.txt", "functions"):
            alias = self.output / relative
            if relative == "functions":
                # A symbolic functions root must not be used as a traversal entry point.
                target.parent.rename(moved)
                os.symlink("static/real-functions", alias, target_is_directory=True)
            else:
                os.symlink("real.func", alias, target_is_directory=True)
            with self.subTest(path=relative), self.assertRaises(SystemExit):
                self.execute("pack")
            self.assertFalse((self.root / "upload").exists())
            alias.unlink()
            if relative == "functions":
                moved.rename(target.parent)
        code = target / "code.bin"
        code.write_bytes(b"fixture")
        original_lstat = Path.lstat

        def special(path, *args, **kwargs):
            info = original_lstat(path, *args, **kwargs)
            return self.changed_stat(info, st_mode=stat.S_IFIFO | 0o600) if path == code else info

        with patch.object(Path, "lstat", special), self.assertRaises(SystemExit):
            self.execute("pack")
        self.assertFalse((self.root / "upload").exists())

    def test_consumer_rejects_adulterated_alias_metadata_and_targets_before_extraction(self):
        alias, target = self.func_alias_fixture()
        os.symlink("real.func", target.parent / "second.func", target_is_directory=True)
        (target.parent / "file.func").write_bytes(b"not a directory")
        package = self.package_fixture()
        original = package.read_bytes()
        cases = [("target", value) for value in (
            "/absolute.func", "../../outside.func", "../diagnostics", "../static",
            "missing.func", "file.func", "alias.func", "second.func",
            "second.func/nested.func", "./real.func", "real.func/../real.func",
        )] + [("mode", 0o600), ("mtime", 1), ("sha256", "a" * 64),
             ("target_only_in_header", "missing.func"), ("extra", True), ("cycle", True)]
        for field, value in cases:
            package.write_bytes(original)

            def change(entries):
                for member, data in entries:
                    if member.name == "output/functions/alias.func":
                        if field in {"target", "target_only_in_header"}:
                            member.linkname = value
                        elif field in {"mode", "mtime"}:
                            setattr(member, field, value)
                        elif field == "cycle":
                            member.linkname = "second.func"
                    if field == "cycle" and member.name == "output/functions/second.func":
                        member.linkname = "alias.func"
                    if member.name == "receipt.json":
                        receipt = json.loads(data)
                        for entry in receipt["entries"]:
                            if entry["path"] == "output/functions/alias.func":
                                if field == "cycle":
                                    entry["target"] = "second.func"
                                elif field != "target_only_in_header":
                                    entry[field] = value
                            if field == "cycle" and entry["path"] == "output/functions/second.func":
                                entry["target"] = "alias.func"
                        data = json.dumps(receipt).encode()
                    yield member, data

            self.rewrite_package(lambda entries: list(change(entries)))
            with self.subTest(field=field, value=value), self.assertRaises(SystemExit):
                self.verify()
            self.assertFalse((self.root / "verified").exists())
        self.assertEqual(os.readlink(alias), "real.func")

    def test_consumer_rejects_members_under_alias_even_with_consistent_inventory(self):
        self.func_alias_fixture()
        self.package_fixture()

        def add_child(entries):
            member = tarfile.TarInfo("output/functions/alias.func/child.bin")
            data = b"must not be extracted through an alias"
            for header, contents in entries:
                if header.name == "receipt.json":
                    receipt = json.loads(contents)
                    receipt["entries"].append({
                        "path": member.name, "type": "file", "mode": member.mode,
                        "size": len(data), "mtime": 0, "sha256": hashlib.sha256(data).hexdigest(),
                    })
                    contents = json.dumps(receipt).encode()
                yield header, contents
            yield member, data

        self.rewrite_package(lambda entries: list(add_child(entries)))
        with self.assertRaises(SystemExit):
            self.verify()
        self.assertFalse((self.root / "verified").exists())

    def test_consumer_rejects_ustar_unrepresentable_alias_target(self):
        self.func_alias_fixture()
        package = self.package_fixture()
        with tarfile.open(package, "r:") as archive:
            entries = []
            for member in archive.getmembers():
                data = b""
                if member.isfile():
                    stream = archive.extractfile(member)
                    assert stream is not None
                    data = stream.read()
                entries.append((deepcopy(member), data))
        with tarfile.open(package, "w:", format=tarfile.PAX_FORMAT) as archive:
            for member, data in entries:
                if member.issym():
                    member.linkname = "x" * 96 + ".func"
                archive.addfile(member, io.BytesIO(data) if member.isfile() else None)
        self.digest = hashlib.sha256(package.read_bytes()).hexdigest()
        with self.assertRaises(SystemExit):
            self.verify()
        self.assertFalse((self.root / "verified").exists())

    def test_verifier_detects_changed_alias_text_after_materialization(self):
        self.func_alias_fixture()
        self.package_fixture()
        original_symlink = os.symlink

        def corrupt(link, path, **kwargs):
            original_symlink("missing.func", path, **kwargs)

        with patch("os.symlink", side_effect=corrupt), self.assertRaises(SystemExit):
            self.verify()

    def assert_selection(self, receipt, state):
        self.assertEqual(receipt["version"], 5)
        self.assertEqual(set(receipt), {"version", "provenance", "selection", "entries"})
        self.assertEqual(receipt["selection"], {
            "source": ".vercel/output", "payload": "output",
            "regular_files": "independent-bytes",
            "diagnostics": {"path": "output/diagnostics", "state": state,
                            "reason": "auxiliary diagnostics excluded for privacy"},
            "builds_json": {"path": "output/builds.json", "representation": "target-only"},
            "static_trace": {"path": "output/static/_next/__private/trace", "state": "absent",
                             "reason": "auxiliary static trace excluded for privacy"},
        })

    def test_omits_diagnostics_without_accessing_contents_or_changing_source(self):
        diagnostics = self.output / "diagnostics"
        private = diagnostics / "private"
        private.mkdir(parents=True)
        trace = private / ".env"
        trace.write_bytes(b"synthetic private contents, never read by the producer")
        paths = (diagnostics, private, trace)
        before = [(p.lstat().st_mode, p.lstat().st_size, p.lstat().st_mtime_ns) for p in paths]
        original_iterdir, original_open, original_lstat = Path.iterdir, Path.open, Path.lstat
        checked = []

        def guarded_iterdir(path):
            self.assertFalse(path == diagnostics or diagnostics in path.parents)
            return original_iterdir(path)

        def guarded_open(path, *args, **kwargs):
            self.assertFalse(path == diagnostics or diagnostics in path.parents)
            return original_open(path, *args, **kwargs)

        def guarded_lstat(path, *args, **kwargs):
            self.assertNotIn(diagnostics, path.parents)
            if path == diagnostics:
                checked.append(path)
            return original_lstat(path, *args, **kwargs)

        with patch.object(Path, "iterdir", guarded_iterdir), \
                patch.object(Path, "open", guarded_open), \
                patch.object(Path, "lstat", guarded_lstat):
            try:
                package = self.package_fixture()
            except SystemExit as error:
                self.fail(f"Expected selected-payload packaging, got: {error}")
        self.assertEqual(checked, [diagnostics, diagnostics])
        self.assertEqual(before, [(p.lstat().st_mode, p.lstat().st_size, p.lstat().st_mtime_ns)
                                  for p in paths])
        self.assertEqual(trace.read_bytes(),
                         b"synthetic private contents, never read by the producer")
        with tarfile.open(package, "r:") as archive:
            receipt = json.loads(archive.extractfile("receipt.json").read())
            self.assertFalse(any(n == "output/diagnostics" or n.startswith("output/diagnostics/")
                                 for n in archive.getnames()))
        self.assert_selection(receipt, "omitted")
        self.verify()
        restored = self.root / "verified/output"
        self.assertFalse((restored / "diagnostics").exists())
        selected = [self.output, self.output / "config.json", self.output / "builds.json",
                    self.output / "static", *(self.output / "static").rglob("*")]
        for source in selected:
            target = restored / source.relative_to(self.output)
            self.assertEqual(target.is_dir(), source.is_dir())
            self.assertEqual(stat.S_IMODE(target.stat().st_mode),
                             stat.S_IMODE(source.stat().st_mode))
            self.assertEqual(int(target.stat().st_mtime), int(source.stat().st_mtime))
            if source.is_file():
                expected = (b'{"target":"production"}' if source == self.output / "builds.json"
                            else source.read_bytes())
                self.assertEqual(target.read_bytes(), expected)

    def test_absent_diagnostics_is_recorded_without_observed_omission(self):
        package = self.package_fixture()
        self.assertEqual(self.report["source_regular_files_with_multiple_links"], 0)
        with tarfile.open(package, "r:") as archive:
            receipt = json.loads(archive.extractfile("receipt.json").read())
        self.assert_selection(receipt, "absent")
        self.verify()

    def test_diagnostics_requires_real_directory_and_valid_mode_before_packaging(self):
        diagnostics = self.output / "diagnostics"
        diagnostics.write_bytes(b"fixture, not a directory")
        original_lstat = Path.lstat
        # Exercise lstat types without requiring Windows symlink/FIFO privileges.
        for mode in (stat.S_IFREG | 0o600, stat.S_IFLNK | 0o777,
                     stat.S_IFIFO | 0o600, stat.S_IFDIR | 0o1700):
            checked = []

            def metadata(path, *args, **kwargs):
                if path == diagnostics:
                    checked.append(path)
                    return os.stat_result((mode, 0, 0, 2, 0, 0, 0, 0, 0, 0))
                return original_lstat(path, *args, **kwargs)

            with self.subTest(mode=mode), patch.object(Path, "lstat", metadata), \
                    self.assertRaises(SystemExit):
                self.execute("pack")
            self.assertEqual(checked, [diagnostics])
            self.assertFalse((self.root / "upload").exists())
            self.assertFalse((self.root / "job-output").exists())

    def test_nested_diagnostics_is_selected_and_round_trips(self):
        nested = self.output / "static/diagnostics"
        nested.mkdir()
        (nested / "trace.json").write_bytes(b"selected fixture")
        self.package_fixture()
        self.verify()
        self.assertEqual((self.root / "verified/output/static/diagnostics/trace.json").read_bytes(),
                         b"selected fixture")

    def test_other_unknown_entry_still_fails_with_diagnostics_present(self):
        (self.output / "diagnostics").mkdir()
        (self.output / "diagnostics-extra").write_bytes(b"not an approved exception")
        with self.assertRaisesRegex(
            SystemExit, "Unexpected output entry: output/diagnostics-extra"
        ):
            self.execute("pack")
        self.assertFalse((self.root / "upload").exists())
        self.assertFalse((self.root / "job-output").exists())

    def test_consumer_rejects_diagnostics_members_despite_declared_omission(self):
        (self.output / "diagnostics").mkdir()
        package = self.package_fixture()
        with tarfile.open(package, "r:") as archive:
            self.assert_selection(json.loads(archive.extractfile("receipt.json").read()), "omitted")
        original = package.read_bytes()
        for name, kind in (("output/diagnostics", tarfile.DIRTYPE),
                           ("output/diagnostics", tarfile.REGTYPE),
                           ("output/diagnostics/cli_traces.json", tarfile.REGTYPE),
                           ("output/diagnostics/nested/trace", tarfile.REGTYPE)):
            package.write_bytes(original)
            member = tarfile.TarInfo(name)
            member.type = kind
            self.rewrite_package(lambda entries: entries + [(member, b"")])
            with self.subTest(name=name, kind=kind), self.assertRaises(SystemExit):
                self.verify()
            self.assertFalse((self.root / "verified").exists())

    def test_consumer_rejects_adulterated_selection_and_receipt_schema(self):
        package = self.package_fixture()
        with tarfile.open(package, "r:") as archive:
            receipt = json.loads(archive.extractfile("receipt.json").read())
        self.assert_selection(receipt, "absent")
        selection = receipt["selection"]
        invalid_selections = [None, [], selection | {"extra": True},
                              selection | {"source": "workspace"},
                              selection | {"payload": "source"},
                              selection | {"diagnostics": {}}, selection | {"diagnostics": []}]
        for field, value in (("path", "output/static"), ("path", "output/diagnostics/*"),
                             ("state", True), ("state", "ignored"), ("state", []),
                             ("reason", "optional"), ("extra", True)):
            invalid_selections.append(selection | {"diagnostics": selection["diagnostics"] |
                                                   {field: value}})
        for key in ("builds_json", "static_trace"):
            invalid_selections.extend(selection | {key: value} for value in (None, [], {}))
            for field, value in (("path", "output/other"), ("source_sha256", "0" * 64),
                                 ("validated", True), ("extra", {})):
                invalid_selections.append(selection | {key: selection[key] | {field: value}})
        invalid_selections.append(selection | {"builds_json": selection["builds_json"] |
                                               {"representation": "original"}})
        for field, value in (("state", True), ("state", "ignored"), ("state", []),
                             ("reason", "optional")):
            invalid_selections.append(selection | {"static_trace": selection["static_trace"] |
                                                   {field: value}})
        cases = [receipt | {"selection": value} for value in invalid_selections]
        cases += [receipt | {"source_sha256": "0" * 64}, receipt | {"validated": True}]
        cases += [receipt | {"version": value} for value in (1, 2, 3, 4, 6, True, "5")]
        cases += [receipt | {"selection": selection | {"regular_files": value}}
                  for value in (None, True, [], "hard-links", "independent-bytes ")]
        cases += [receipt | {"selection": {k: v for k, v in selection.items()
                                          if k != "regular_files"}}]
        cases += [receipt | {"omissions": []},
                  {k: v for k, v in receipt.items() if k != "selection"}]
        original = package.read_bytes()
        for index, candidate in enumerate(cases):
            package.write_bytes(original)
            self.rewrite_package(lambda entries: [
                (m, json.dumps(candidate).encode() if m.name == "receipt.json" else data)
                for m, data in entries
            ])
            with self.subTest(case=index), self.assertRaises(SystemExit):
                self.verify()
            self.assertFalse((self.root / "verified").exists())

    def test_selection_declaration_is_bound_to_expected_package_hash(self):
        package = self.package_fixture()
        with tarfile.open(package, "r:") as archive:
            receipt = json.loads(archive.extractfile("receipt.json").read())
        self.assert_selection(receipt, "absent")
        expected_hash = self.digest
        receipt["selection"]["diagnostics"]["state"] = "omitted"
        self.rewrite_package(lambda entries: [
            (m, json.dumps(receipt).encode() if m.name == "receipt.json" else data)
            for m, data in entries
        ])
        with self.assertRaisesRegex(SystemExit, "Package SHA-256 mismatch"):
            self.verify(overrides={"PACKAGE_SHA256": expected_hash})
        self.assertFalse((self.root / "verified").exists())

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
                expected = (b'{"target":"production"}' if source == self.output / "builds.json"
                            else source.read_bytes())
                self.assertEqual(target.read_bytes(), expected)
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
