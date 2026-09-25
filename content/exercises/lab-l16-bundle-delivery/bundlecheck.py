#!/usr/bin/env python3
"""Local checks for the Lab L16 bundle configuration: no workspace, no network.

For one BUNDLE.md, in order:
  1. extract the fenced yaml blocks; each block's first line is "# file: <path>";
  2. parse each block with a PyYAML safe loader that also refuses duplicate
     keys (local syntax check);
  3. apply the lab's structure rules to the assembled configuration (local
     schema and structure check);
  4. resolve variables, paths and task parameters per target, for the part of
     the interpolation that needs no workspace.

This is not `databricks bundle validate`. The Databricks CLI reads the same
files, authenticates, asks the workspace who the current user is, resolves
lookups and applies its complete schema and target-mode rules; none of that
happens here. Rules tagged "mirrors CLI" restate behaviour read in the
Databricks CLI v1.17.0 source and are re-implemented here as a small subset
(no CLI code is copied). Rules tagged "house" are this lab's own review policy.

Usage, from the lab directory:
  python bundlecheck.py solutions/project/BUNDLE.md
  python bundlecheck.py solutions/project/BUNDLE.md --resolve
  python bundlecheck.py solutions/project/BUNDLE.md --materialize <new directory>
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import argparse  # noqa: E402
import copy  # noqa: E402
import fnmatch  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import tomllib  # noqa: E402
from dataclasses import asdict, dataclass  # noqa: E402
from pathlib import Path  # noqa: E402

import yaml  # noqa: E402

ROOT_FILE = "databricks.yml"
FENCE = re.compile(r"^```yaml[ \t]*\n(.*?)^```[ \t]*$", re.S | re.M)
FILE_MARKER = re.compile(r"^# file: (\S+)[ \t]*$")
VAR_REF = re.compile(r"\$\{var\.([A-Za-z0-9_]+)\}")
ANY_REF = re.compile(r"\$\{[^}]+\}")
CURRENT_USER_REF = "${workspace.current_user."
MODES = ("development", "production")
WORKSPACE_KEYS = {
    "host", "profile", "auth_type", "client_id", "google_service_account",
    "azure_workspace_resource_id", "azure_use_msi", "azure_client_id",
    "azure_tenant_id", "azure_environment", "azure_login_app_id",
    "experimental_is_unified_host", "account_id", "workspace_id",
    "root_path", "file_path", "resource_path", "artifact_path", "state_path",
}
AUTH_FIELDS = ("host", "profile", "auth_type", "client_id", "account_id", "workspace_id")
PATH_KEYS = ("root_path", "file_path", "resource_path", "artifact_path", "state_path")
CREDENTIAL_KEYS = {
    "token", "password", "client_secret", "secret", "access_token", "api_key", "pat",
}
REQUIRED_TARGETS = ("dev", "test", "prod")
SERVICE_TARGETS = ("test", "prod")
PRODUCTION_BRANCH = "main"
BUSINESS_RULE = "Business rule."
PINNED = re.compile(r"^[A-Za-z0-9_.\-\[\]]+==[A-Za-z0-9_.\-+]+$")
WHEEL_DEPENDENCY = "../dist/*.whl"
DEFAULT_ROOT = "~/.bundle/${bundle.name}/${bundle.target}"

RULES = {
    "SYNTAX": ("local syntax", "each block parses as one YAML mapping with no duplicate key"),
    "D1": ("mirrors CLI", "a target's mode is development or production"),
    "D2": ("mirrors CLI", "a target assigns only variables declared at the top level"),
    "D3": ("mirrors CLI", "a variable without a default gets a value in every target"),
    "D4": ("mirrors CLI", "a production target sets workspace.root_path explicitly"),
    "D5": ("mirrors CLI", "a development target's workspace paths start with ~/ or name the current user"),
    "D6": ("mirrors CLI", "a development target does not unpause triggers by preset"),
    "D7": ("mirrors CLI", "every ${var.name} reference names a declared variable"),
    "D8": ("mirrors CLI", "at most one target is marked default"),
    "D9": ("mirrors CLI", "workspace keys are ones the bundle schema defines; credentials are not among them"),
    "D10": ("mirrors CLI", "an include entry without wildcards names a file that exists"),
    "D11": ("mirrors CLI", "workspace authentication fields contain no ${...} interpolation"),
    "H1": ("house", "targets dev, test and prod exist and dev is the default"),
    "H2": ("house", "prod deploys only from branch main (git.branch)"),
    "H3": ("house", "test and prod run as a service principal (run_as)"),
    "H4": ("house", "test and prod root_path is fixed, not derived from whoever deploys"),
    "H5": ("house", "no credential value appears anywhere in the configuration"),
    "H6": ("house", "a variable described as a business rule is not overridden by any target"),
    "H7": ("house", "job environment dependencies are the project wheel or pinned with =="),
    "H8": ("house", "task keys are unique and depends_on names an existing task"),
    "H9": ("house", "a wheel task's package and entry point exist in pyproject.toml"),
    "H10": ("house", "an include wildcard matches at least one file (the CLI accepts an empty match silently)"),
}


@dataclass(frozen=True)
class Finding:
    rule: str
    where: str
    message: str


class BlockError(ValueError):
    """A BUNDLE.md whose blocks cannot be located or named."""


class _UniqueKeyLoader(yaml.SafeLoader):
    """Safe loader that refuses a repeated mapping key instead of keeping the last one."""


def _construct_unique_mapping(loader, node, deep=False):
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping", node.start_mark,
                f"found duplicate key {key!r}", key_node.start_mark,
            )
        seen.add(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping
)


# ---------------------------------------------------------------- 1. blocks
def extract_blocks(text: str) -> dict[str, str]:
    """Map "<path>" to the YAML text of each fenced block, marker line included."""
    blocks: dict[str, str] = {}
    for match in FENCE.finditer(text):
        body = match.group(1)
        marker = FILE_MARKER.match(body.partition("\n")[0])
        line = text.count("\n", 0, match.start()) + 1
        if not marker:
            raise BlockError(f"yaml block at line {line} does not start with '# file: <path>'")
        path = marker.group(1)
        if path in blocks:
            raise BlockError(f"two yaml blocks claim {path}")
        blocks[path] = body
    if ROOT_FILE not in blocks:
        raise BlockError(f"no yaml block names {ROOT_FILE}")
    return blocks


# ----------------------------------------------------------------- 2. parse
def parse_blocks(blocks: dict[str, str]) -> tuple[dict[str, dict], list[Finding]]:
    docs: dict[str, dict] = {}
    findings: list[Finding] = []
    for path, body in blocks.items():
        try:
            value = yaml.load(body, Loader=_UniqueKeyLoader)  # noqa: S506 - safe subclass
        except yaml.MarkedYAMLError as error:
            mark = error.problem_mark or error.context_mark
            where = f"{path}:{mark.line + 1}" if mark else path
            findings.append(Finding("SYNTAX", where, (error.problem or str(error)).strip()))
            continue
        except yaml.YAMLError as error:  # pragma: no cover - unmarked parser errors
            findings.append(Finding("SYNTAX", path, str(error).strip()))
            continue
        if not isinstance(value, dict):
            findings.append(Finding("SYNTAX", path, "the file is not a YAML mapping"))
            continue
        docs[path] = value
    return docs, findings


def load_markdown(path: Path) -> tuple[dict[str, dict], list[Finding]]:
    return parse_blocks(extract_blocks(path.read_text(encoding="utf-8")))


# -------------------------------------------------------------- 3. structure
def _walk(value, prefix=""):
    """Yield (dotted path, value) for every node of a parsed document."""
    yield prefix, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk(child, f"{prefix}.{key}" if prefix else str(key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{prefix}[{index}]")


def _include_matches(root: dict, docs: dict[str, dict]) -> list[tuple[int, str, list[str]]]:
    others = sorted(p for p in docs if p != ROOT_FILE)
    result = []
    for index, pattern in enumerate(root.get("include") or []):
        result.append((index, pattern, [p for p in others if fnmatch.fnmatch(p, pattern)]))
    return result


def included_resources(docs: dict[str, dict]) -> list[tuple[str, str, str, dict]]:
    """(file, resource type, key, definition) for the root file and every included file."""
    root = docs.get(ROOT_FILE, {})
    files = [ROOT_FILE]
    for _, _, matched in _include_matches(root, docs):
        files.extend(p for p in matched if p not in files)
    found = []
    for path in files:
        for kind, entries in (docs.get(path, {}).get("resources") or {}).items():
            for key, definition in (entries or {}).items():
                found.append((path, kind, key, definition or {}))
    return found


def _declared(root: dict) -> dict[str, dict]:
    return {name: (spec or {}) for name, spec in (root.get("variables") or {}).items()}


def _target_value(assigned):
    """A target may assign a variable as a scalar or as a mapping with 'default'."""
    if isinstance(assigned, dict):
        return assigned.get("default")
    return assigned


def _pyproject_scripts(project_dir: Path | None) -> tuple[str | None, set[str]]:
    if project_dir is None or not (project_dir / "pyproject.toml").exists():
        return None, set()
    data = tomllib.loads((project_dir / "pyproject.toml").read_text(encoding="utf-8"))
    project = data.get("project", {})
    return project.get("name"), set((project.get("scripts") or {}).keys())


def check(docs: dict[str, dict], project_dir: Path | None = None) -> list[Finding]:
    """Apply the structure rules; an empty list means none fired."""
    findings: list[Finding] = []

    def add(rule, where, message):
        findings.append(Finding(rule, where, message))

    root = docs.get(ROOT_FILE)
    if root is None:
        return [Finding("SYNTAX", ROOT_FILE, "no parsed databricks.yml")]
    declared = _declared(root)
    targets = root.get("targets") or {}

    # Includes (D10, H10).
    for index, pattern, matched in _include_matches(root, docs):
        if not matched:
            where = f"{ROOT_FILE}:include[{index}]"
            if any(ch in pattern for ch in "*?["):
                add("H10", where, f"include wildcard {pattern!r} matches no file, so nothing from it is deployed")
            else:
                add("D10", where, f"{pattern} defined in 'include' does not match any file")

    # Targets present and defaults (H1, D8).
    for name in REQUIRED_TARGETS:
        if name not in targets:
            add("H1", f"{ROOT_FILE}:targets.{name}", f"target {name} is missing")
    defaults = sorted(n for n, t in targets.items() if (t or {}).get("default") is True)
    if len(defaults) > 1:
        add("D8", f"{ROOT_FILE}:targets", "multiple targets are marked as default (" + ", ".join(defaults) + ")")
    if "dev" in targets and (targets["dev"] or {}).get("default") is not True:
        add("H1", f"{ROOT_FILE}:targets.dev.default", "dev is not the default target")

    workspaces = [("workspace", root.get("workspace") or {})]
    workspaces += [(f"targets.{n}.workspace", (t or {}).get("workspace") or {}) for n, t in targets.items()]
    for prefix, workspace in workspaces:
        for key, value in workspace.items():
            if key not in WORKSPACE_KEYS:
                add("D9", f"{ROOT_FILE}:{prefix}.{key}", f"unknown field: {key}")
            if key in AUTH_FIELDS and isinstance(value, str) and ANY_REF.search(value):
                add("D11", f"{ROOT_FILE}:{prefix}.{key}", "variable interpolation is not supported for fields that configure authentication")

    for name, target in targets.items():
        target = target or {}
        base = f"{ROOT_FILE}:targets.{name}"
        mode = target.get("mode")
        workspace = target.get("workspace") or {}
        assigned = target.get("variables") or {}
        if mode is not None and mode not in MODES:
            add("D1", f"{base}.mode", f"unsupported value {mode!r} for mode: must be development or production")
        for variable in assigned:
            if variable not in declared:
                add("D2", f"{base}.variables.{variable}", f"variable {variable} is not defined but is assigned a value")
        for variable, spec in declared.items():
            if "default" not in spec and "lookup" not in spec and _target_value(assigned.get(variable)) is None:
                add("D3", f"{base}.variables.{variable}", f"no value assigned to required variable {variable}")
            if str(spec.get("description", "")).startswith(BUSINESS_RULE) and variable in assigned:
                add("H6", f"{base}.variables.{variable}", f"business rule {variable} is overridden in target {name}")
        if mode == "production" and not workspace.get("root_path"):
            add("D4", f"{base}.workspace.root_path", "target with mode: production must set workspace.root_path")
        if mode == "development":
            for key in PATH_KEYS:
                value = workspace.get(key)
                if value and not (str(value).startswith("~/") or CURRENT_USER_REF in str(value)):
                    add("D5", f"{base}.workspace.{key}", f"{key} must start with '~/' or contain the current user in mode: development")
            if str((target.get("presets") or {}).get("trigger_pause_status", "")).upper() == "UNPAUSED":
                add("D6", f"{base}.presets.trigger_pause_status", "mode: development cannot set trigger pause status to UNPAUSED")
        if name in SERVICE_TARGETS:
            run_as = target.get("run_as") or {}
            if not run_as.get("service_principal_name"):
                add("H3", f"{base}.run_as", f"target {name} does not run as a service principal")
            root_path = str(workspace.get("root_path") or "")
            if root_path and (CURRENT_USER_REF in root_path or root_path.startswith("~")):
                add("H4", f"{base}.workspace.root_path", f"root_path of {name} depends on who deploys, so two deployers make two copies")
        if name == "prod" and ((target.get("git") or {}).get("branch") != PRODUCTION_BRANCH):
            add("H2", f"{base}.git.branch", f"prod is not pinned to branch {PRODUCTION_BRANCH}")

    # Every document: credentials (H5) and variable references (D7).
    for path in sorted(docs):
        for dotted, value in _walk(docs[path]):
            leaf = dotted.rsplit(".", 1)[-1].split("[", 1)[0]
            if leaf.lower() in CREDENTIAL_KEYS and value not in (None, "", {}, []):
                add("H5", f"{path}:{dotted}", f"{leaf} holds a value; credentials come from the environment, never from this file")
            if isinstance(value, str):
                for variable in VAR_REF.findall(value):
                    if variable not in declared:
                        add("D7", f"{path}:{dotted}", f"reference to ${{var.{variable}}}, which is not declared")

    # Jobs (H7, H8, H9).
    package, scripts = _pyproject_scripts(project_dir)
    for path, kind, key, job in included_resources(docs):
        if kind != "jobs":
            continue
        base = f"{path}:resources.jobs.{key}"
        tasks = job.get("tasks") or []
        keys = [task.get("task_key") for task in tasks]
        for index, task in enumerate(tasks):
            if keys.count(task.get("task_key")) > 1:
                add("H8", f"{base}.tasks[{index}]", f"task_key {task.get('task_key')!r} is not unique")
            for dependency in task.get("depends_on") or []:
                if dependency.get("task_key") not in keys:
                    add("H8", f"{base}.tasks[{index}]", f"depends_on names missing task {dependency.get('task_key')!r}")
            wheel = task.get("python_wheel_task")
            if wheel and project_dir is not None:
                if wheel.get("package_name") != package or wheel.get("entry_point") not in scripts:
                    add("H9", f"{base}.tasks[{index}].python_wheel_task",
                        f"package {wheel.get('package_name')!r} / entry point {wheel.get('entry_point')!r} not found in pyproject.toml")
        for e_index, environment in enumerate(job.get("environments") or []):
            spec = environment.get("spec") or {}
            for d_index, dependency in enumerate(spec.get("dependencies") or []):
                if dependency != WHEEL_DEPENDENCY and not PINNED.match(str(dependency)):
                    add("H7", f"{base}.environments[{e_index}].spec.dependencies[{d_index}]",
                        f"dependency {dependency!r} is neither the project wheel nor pinned with ==")
    return sorted(findings, key=lambda f: (f.rule, f.where, f.message))


# --------------------------------------------------------------- 4. resolve
def _substitute(text, values: dict[str, str], bundle_name: str, target: str):
    if not isinstance(text, str):
        return text
    text = text.replace("${bundle.name}", bundle_name).replace("${bundle.target}", target)
    return VAR_REF.sub(lambda m: str(values.get(m.group(1), m.group(0))), text)


def resolve(docs: dict[str, dict]) -> dict[str, dict]:
    """Per target: the values the lab can resolve without a workspace.

    Precedence follows the CLI's documented order for the two sources present
    in a reviewed file (a target's value, then the variable's default); --var,
    BUNDLE_VAR_<name> and a variable-overrides file are run-time sources the
    lab does not read. ${workspace.current_user.*} and "~" need a workspace and
    are left in place and listed under needs_workspace.
    """
    root = docs[ROOT_FILE]
    bundle_name = root["bundle"]["name"]
    declared = _declared(root)
    jobs = [(key, job) for _, kind, key, job in included_resources(docs) if kind == "jobs"]
    resolved = {}
    for name, target in (root.get("targets") or {}).items():
        target = target or {}
        assigned = target.get("variables") or {}
        values = {}
        for variable, spec in declared.items():
            value = _target_value(assigned.get(variable))
            values[variable] = str(value if value is not None else spec.get("default", "<unassigned>"))
        values = {k: _substitute(v, values, bundle_name, name) for k, v in values.items()}
        workspace = target.get("workspace") or {}
        root_path = _substitute(workspace.get("root_path") or DEFAULT_ROOT, values, bundle_name, name)
        parameters = {}
        for key, job in jobs:
            for task in job.get("tasks") or []:
                wheel = task.get("python_wheel_task") or {}
                parameters[f"{key}.{task.get('task_key')}"] = [
                    _substitute(str(p), values, bundle_name, name) for p in wheel.get("parameters") or []
                ]
        needs = sorted(
            ([f"variables.{k}" for k, v in values.items() if CURRENT_USER_REF in v])
            + (["root_path"] if root_path.startswith("~") or CURRENT_USER_REF in root_path else [])
        )
        mode = target.get("mode")
        pause = (target.get("presets") or {}).get("trigger_pause_status")
        if mode == "development":
            schedule = "paused by mode: development"
        elif pause:
            schedule = f"{str(pause).lower()} by presets.trigger_pause_status"
        else:
            schedule = "as written in the job"
        resolved[name] = {
            "mode": mode,
            "default": target.get("default") is True,
            "host": workspace.get("host"),
            "root_path": root_path,
            "variables": values,
            "task_parameters": parameters,
            "run_as": (target.get("run_as") or {}).get("service_principal_name"),
            "git_branch": (target.get("git") or {}).get("branch"),
            "schedule": schedule,
            "needs_workspace": needs,
        }
    return resolved


# ------------------------------------------------------------- materialize
def materialize(bundle_md: Path, destination: Path) -> list[str]:
    """Copy the project beside BUNDLE.md into a new directory and write each block as a real file."""
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(f"{destination} is not empty")
    project = bundle_md.parent
    shutil.copytree(project, destination, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "BUNDLE.md"))
    written = []
    for path, body in extract_blocks(bundle_md.read_text(encoding="utf-8")).items():
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        written.append(path)
    return sorted(written)


def load_files(project: Path) -> tuple[dict[str, dict], list[Finding]]:
    """Parse a materialized project's databricks.yml and the files it includes."""
    blocks = {ROOT_FILE: (project / ROOT_FILE).read_text(encoding="utf-8")}
    for path in sorted(project.rglob("*.yml")):
        relative = path.relative_to(project).as_posix()
        if relative != ROOT_FILE:
            blocks[relative] = path.read_text(encoding="utf-8")
    return parse_blocks(blocks)


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("bundle_md", type=Path)
    parser.add_argument("--resolve", action="store_true", help="print resolved targets")
    parser.add_argument("--materialize", type=Path, help="write the project with real .yml files")
    args = parser.parse_args(argv)
    docs, findings = load_markdown(args.bundle_md)
    if args.materialize:
        print(json.dumps({"written": materialize(args.bundle_md, args.materialize)}, indent=2))
        return 0
    if not findings:
        findings = check(docs, args.bundle_md.parent)
    if args.resolve and not findings:
        print(json.dumps(resolve(docs), indent=2, sort_keys=True))
        return 0
    print(json.dumps([asdict(f) | {"kind": RULES[f.rule][0]} for f in findings], indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
