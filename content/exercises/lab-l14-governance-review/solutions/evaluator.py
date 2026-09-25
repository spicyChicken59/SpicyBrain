"""Local evaluator for the tabletop governance review (standard library only).

This is a small, simplified model of documented Unity Catalog privilege rules,
written so that an authored policy table can be checked on paper and on a
laptop. It evaluates the JSON files in fixtures/; it is not Unity Catalog,
connects to nothing and enforces nothing.

Model rules (the lab's own, stated in DATA.md):

* Deny by default: there are no deny entries; a request is allowed only when
  every check below finds a grant or an ownership.
* A principal acts with its own grants and those of every group it belongs to,
  directly or through nested groups.
* Reading or writing an object needs, in this order, USE CATALOG on its
  catalog, USE SCHEMA on its schema (granted on the schema or the catalog), and
  the object privilege granted on the object, its schema or its catalog. The
  first missing check names the denial.
* Ownership gives every privilege on the owned securable itself, and the right
  to grant on it; it does not cascade to children.
* Row filters and column masks never deny: they remove rows or replace values
  for an allowed SELECT.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

DISCLAIMER = (
    "Tabletop evaluation: a locally evaluated policy table is not Unity Catalog "
    "enforcement. Nothing here connects to Databricks or checks a real grant."
)
OBJECT_PRIVILEGES = {
    "table": ("SELECT", "MODIFY"),
    "volume": ("READ VOLUME", "WRITE VOLUME"),
}
DATA_PRIVILEGES = {"SELECT", "MODIFY", "READ VOLUME", "WRITE VOLUME"}
KNOWN_PRIVILEGES = DATA_PRIVILEGES | {"USE CATALOG", "USE SCHEMA", "MANAGE", "ALL PRIVILEGES"}
BROAD_PRIVILEGES = {"MANAGE", "ALL PRIVILEGES"}


class PlanError(ValueError):
    """A plan names something the model does not know."""


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class Model:
    def __init__(self, principals, securables, grants, policies, tables):
        self.users = list(principals["users"])
        self.service_principals = list(principals["servicePrincipals"])
        self.groups = {name: list(members) for name, members in principals["groups"].items()}
        self.catalogs = copy.deepcopy(securables["catalogs"])
        self.schemas = copy.deepcopy(securables["schemas"])
        self.objects = copy.deepcopy(securables["objects"])
        self.grants = [dict(g) for g in grants["grants"]]
        self.policies = copy.deepcopy(policies["policies"])
        self.tables = copy.deepcopy({k: v for k, v in tables.items() if not k.startswith("_")})

    @classmethod
    def load(cls, root: Path) -> "Model":
        f = Path(root) / "fixtures"
        return cls(_read(f / "principals.json"), _read(f / "securables.json"), _read(f / "grants.json"),
                   _read(f / "policies.json"), _read(f / "tables.json"))

    # ---------------------------------------------------------------- identity
    def exists(self, principal: str) -> bool:
        return principal in self.users or principal in self.service_principals or principal in self.groups

    def is_group(self, principal: str) -> bool:
        return principal in self.groups

    def identities(self, principal: str) -> set[str]:
        """The principal itself plus every group it belongs to, directly or nested."""
        found = {principal}
        changed = True
        while changed:
            changed = False
            for group, members in self.groups.items():
                if group not in found and found.intersection(members):
                    found.add(group)
                    changed = True
        return found

    # --------------------------------------------------------------- securables
    def kind(self, securable: str) -> str | None:
        if securable in self.catalogs:
            return "catalog"
        if securable in self.schemas:
            return "schema"
        if securable in self.objects:
            return self.objects[securable]["type"]
        return None

    def owner(self, securable: str) -> str:
        for register in (self.catalogs, self.schemas, self.objects):
            if securable in register:
                return register[securable]["owner"]
        raise KeyError(securable)

    def owns(self, principal: str, securable: str) -> bool:
        return self.owner(securable) in self.identities(principal)

    def holds(self, principal: str, privilege: str, securables) -> bool:
        ids = self.identities(principal)
        return any(g["principal"] in ids and g["privilege"] == privilege and g["securable"] in securables
                   for g in self.grants)

    # ---------------------------------------------------------------- decisions
    def decide(self, principal: str, action: str, securable: str) -> dict:
        if not self.exists(principal):
            return {"decision": "deny", "reason": "unknown-principal"}
        kind = self.kind(securable)
        if kind is None:
            return {"decision": "deny", "reason": "unknown-securable"}
        if action == "GRANT":
            if self.owns(principal, securable):
                return {"decision": "allow", "reason": "owner"}
            return {"decision": "deny", "reason": "not-owner"}
        if kind not in OBJECT_PRIVILEGES or action not in OBJECT_PRIVILEGES[kind]:
            return {"decision": "deny", "reason": "unsupported-action"}
        catalog, schema_name, _ = securable.split(".")
        schema = f"{catalog}.{schema_name}"
        if not (self.holds(principal, "USE CATALOG", {catalog}) or self.owns(principal, catalog)):
            return {"decision": "deny", "reason": "missing-use-catalog"}
        if not (self.holds(principal, "USE SCHEMA", {schema, catalog}) or self.owns(principal, schema)):
            return {"decision": "deny", "reason": "missing-use-schema"}
        if self.owns(principal, securable):
            return {"decision": "allow", "reason": "owner"}
        if self.holds(principal, action, {securable, schema, catalog}):
            return {"decision": "allow", "reason": "granted"}
        return {"decision": "deny", "reason": "missing-" + action.lower().replace(" ", "-")}

    def rows(self, principal: str, table: str) -> dict:
        """What SELECT * returns: a denial, or the filtered and masked rows in stored order."""
        decision = self.decide(principal, "SELECT", table)
        if decision["decision"] == "deny":
            return decision
        ids = self.identities(principal)
        rows = [dict(r) for r in self.tables.get(table, [])]
        for policy in self.policies:
            if policy["table"] != table or policy["type"] != "row_filter":
                continue
            allowed: set[str] = set()
            everything = False
            for rule in policy["rules"]:
                if rule["group"] in ids:
                    if rule["values"] == "*":
                        everything = True
                    else:
                        allowed.update(rule["values"])
            if not everything:
                rows = [r for r in rows if r[policy["column"]] in allowed]
        for policy in self.policies:
            if policy["table"] != table or policy["type"] != "column_mask":
                continue
            if not ids.intersection(policy["unmaskedGroups"]):
                for r in rows:
                    r[policy["column"]] = policy["replacement"]
        return {**decision, "rows": rows}

    # ---------------------------------------------------------------- changes
    def apply(self, plan: dict) -> "Model":
        """A new model with a plan's groups, memberships, grants and policy rules applied."""
        m = copy.deepcopy(self)
        for group in plan.get("newGroups", []):
            if group in m.groups or m.exists(group):
                raise PlanError(f"group already exists: {group}")
            m.groups[group] = []
        for change in plan.get("removeMemberships", []):
            members = m.groups.get(change["group"])
            if members is None or change["member"] not in members:
                raise PlanError(f"no such membership: {change}")
            members.remove(change["member"])
        for change in plan.get("memberships", []):
            if change["group"] not in m.groups:
                raise PlanError(f"unknown group: {change['group']}")
            if not m.exists(change["member"]):
                raise PlanError(f"unknown member: {change['member']}")
            if change["member"] not in m.groups[change["group"]]:
                m.groups[change["group"]].append(change["member"])
        for grant in plan.get("grants", []):
            if not m.exists(grant["principal"]):
                raise PlanError(f"unknown principal in plan: {grant['principal']}")
            if m.kind(grant["securable"]) is None:
                raise PlanError(f"unknown securable in plan: {grant['securable']}")
            if grant["privilege"] not in KNOWN_PRIVILEGES:
                raise PlanError(f"unknown privilege in plan: {grant['privilege']}")
            m.grants.append({"principal": grant["principal"], "privilege": grant["privilege"],
                             "securable": grant["securable"]})
        for rule in plan.get("policyRules", []):
            target = [p for p in m.policies if p["id"] == rule["policy"]]
            if not target:
                raise PlanError(f"unknown policy: {rule['policy']}")
            target[0]["rules"].append({"group": rule["group"], "values": rule["values"]})
        return m

    def review_violations(self, plan: dict) -> list[str]:
        """This lab's review rules for a permission plan (guidance, not a platform rule)."""
        found = []
        for grant in plan.get("grants", []):
            privilege, securable, principal = grant["privilege"], grant["securable"], grant["principal"]
            kind = self.kind(securable)
            if privilege in BROAD_PRIVILEGES:
                found.append("broad-privilege")
            if principal == "account users":
                found.append("all-users-grant")
            elif not self.is_group(principal) and principal not in plan.get("newGroups", []):
                found.append("grant-to-individual")
            if privilege in DATA_PRIVILEGES and kind in ("catalog", "schema"):
                found.append("data-privilege-above-object")
            if privilege == "USE SCHEMA" and kind == "catalog":
                found.append("use-schema-on-catalog")
        owner_groups = {v["owner"] for register in (self.catalogs, self.schemas, self.objects)
                        for v in register.values()}
        for change in plan.get("memberships", []):
            if change["group"] in owner_groups:
                found.append("owner-group-membership")
        return sorted(set(found))


def matrix(model: Model, tests: list[dict]) -> dict:
    """Run a list of test rows (decisions and rowsOf queries) against a model."""
    out = {}
    for t in tests:
        if "rowsOf" in t:
            out[t["id"]] = model.rows(t["principal"], t["rowsOf"])
        else:
            out[t["id"]] = model.decide(t["principal"], t["action"], t["securable"])
    return out


if __name__ == "__main__":
    here = Path(__file__).resolve().parent.parent
    model = Model.load(here)
    requests = _read(here / "fixtures" / "requests.json")["requests"]
    print(DISCLAIMER)
    for r in requests:
        d = model.decide(r["principal"], r["action"], r["securable"])
        print(f"{r['id']}  {r['principal']:<28} {r['action']:<12} {r['securable']:<38} {d['decision']:<6} {d['reason']}")
