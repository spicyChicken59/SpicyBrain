<!-- section:dbxfe-apps-l01-outcome -->

After this lesson you can trace one request from a reviewer's browser through a Databricks App's front end and back end to a warehouse, Lakebase, an endpoint or a tool, naming who authenticates and whose permissions apply at each hop; choose the app's identity or the reviewer's per request; bind resources and secrets without credentials in code; place state where it survives; validate before grants are spent; and write a replayable deployment. Nothing here is deployed or added to SpicyBrain's own runtime.

<!-- section:dbxfe-apps-l01-start -->

Bring the boundary idea from [Draw the cloud and trust boundaries](#/lesson/dbxfe-m06-l03) and the request path in [Cloud responsibilities and request paths](#/lesson/dbxfe-cloud-bridge); Unity Catalog privileges come from [Unity Catalog, security and deployment](#/module/dbxfe-m06). The example is the one in the *Application state design* field guide: Cinderline's quality exception review app, where reviewers claim quarantined inspection records and record a disposition. The module [Lakebase, Postgres and operational state](#/module/dbxfe-lakebase) designs those records' transactions; here you decide which state needs them.

<!-- section:dbxfe-apps-l01-path -->

A Databricks App is a web application Databricks hosts on serverless compute it manages. The documentation lists Python frameworks (Streamlit, Dash, Gradio, Flask, FastAPI) and Node.js frameworks (React, Angular, Svelte, Express). The **front end** runs in the reviewer's browser and holds no data credential. The **back end** is the server process your code defines, and it alone calls the SQL warehouse, Lakebase, a serving endpoint or an outside tool. Three trust boundaries follow: browser to the platform's sign-in, platform to the back end (identity headers forwarded), back end to each service (an identity the app chooses).

```python
# server.py (synthetic teaching example; not executed)
from types import SimpleNamespace
from fastapi import FastAPI, HTTPException, Request
app = FastAPI()
deps = SimpleNamespace(claims=None, plants_of=None, plant_of_item=None)   # wired at start-up

def reviewer_of(request: Request) -> str:
    email = request.headers.get("x-forwarded-email")    # set by the platform after sign-in
    if not email:
        raise HTTPException(status_code=401, detail={"reason": "identity"})
    return email.split("@")[0]
```

<!-- section:dbxfe-apps-l01-identity -->

Every app gets a dedicated **service principal**, unique to it; Databricks injects its credentials as `DATABRICKS_CLIENT_ID` and `DATABRICKS_CLIENT_SECRET`. Under **app authorization** the warehouse and Lakebase evaluate that principal, so Leo, who holds no grant on `quality.raw.quarantine`, sees what the app's grant returns unless the handler narrows it. Under **user authorization** (on-behalf-of-user) the platform forwards the reviewer's token in `X-Forwarded-Access-Token`, and a warehouse call made with it is evaluated as Imani, row filters included. The app declares **scopes** such as `sql`, and access outside them is blocked even when Imani could do it in a notebook. User authorization has carried a Public Preview label; confirm its status. Choose per request: reads over data with per-user rules may use the token; claims stay with the app. Never store, log or share the token, and refuse a request whose token is missing rather than falling back to the app.

<!-- section:dbxfe-apps-l01-resources -->

A **resource** replaces a pasted credential: it grants the app's principal a permission and gives the object a key that `app.yaml` maps to a variable.

| Resource | Key | Permission for the app | Variable |
|---|---|---|---|
| SQL warehouse `wh-quality` | `sql-warehouse` | Can use | `QUALITY_WAREHOUSE_ID` |
| Lakebase database `quality_ops` | `quality-db` | CONNECT and CREATE | `PGHOST` and related |
| Secret `quality-app/manuals-token` | `manuals-token` | Can read | `MANUALS_TOKEN` |
| Serving endpoint `disposition-suggest` | `suggest-endpoint` | Can query | `SUGGEST_ENDPOINT` |

```yaml
# app.yaml (synthetic teaching example; not deployed)
command: ["uvicorn", "server:app"]   # add host and port per the environment page
env:
  - name: QUALITY_WAREHOUSE_ID
    valueFrom: sql-warehouse
```

A binding is not every grant: the quarantine table still needs Unity Catalog privileges for the app's principal. A **secret** is read when the process starts, so restart after a rotation, and never print the environment, which also holds the app's own client secret. **User context** arrives in headers the platform sets, such as `X-Forwarded-Email` (verify the current list); the back end fills the guide's `reviewer` field from it and refuses a body naming someone else.

<!-- section:dbxfe-apps-l01-state -->

Classify state by what must be true after the request ends. Claims and dispositions must be visible to anyone, on any process, after any redeploy, so they live in Lakebase; a claim kept in a dictionary is invisible to a second process and gone after the next deployment or restart.

| State | Class | Lives in | After a redeploy |
|---|---|---|---|
| Queue filter | session | browser | may reset |
| Claim on `A-2031` rev 2 | operational | Lakebase `quality_ops` | still there |
| Disposition | operational, append-only | Lakebase `quality_ops` | still there |
| Reviewer token | per-request | request header only | never kept |
| Morning summary | derived analytical | Delta table via warehouse | as of 07:00 |
| Manual text | cache | process memory, with expiry | rebuilt |

<!-- section:dbxfe-apps-l01-runtime -->

Databricks manages the compute; you own what runs on it. At deployment the build installs Python **dependencies** from `requirements.txt` and Node.js packages from `package.json`, runs a build script if one is defined, then runs the `app.yaml` command. Laptop packages do not travel: pin each direct dependency to the tested version. The app environment page, not confirmed in this build, documents versions, pre-installed libraries, compute size and the port variable. Each deployment or restart starts a new process with empty memory.

<!-- section:dbxfe-apps-l01-validation -->

The app's principal holds grants the reviewer lacks, so every body is a lever on them. **Request validation** runs first: a schema with a pattern per field, allowed values, a size limit, no unknown fields; then every value reaches SQL as a bound parameter.

```python
# Synthetic teaching example; not executed.
from pydantic import BaseModel, ConfigDict, Field

class ClaimRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    inspection_key: str = Field(pattern=r"^[A-Z]-\d{4}$")
    revision: int = Field(ge=1, le=999)
    reviewer: str | None = None      # must match the header if sent
```

The key `A-2031' OR '1'='1` fails the pattern; FastAPI answers 422 naming the field before any identity is used. Concatenated into SQL instead, it would widen the predicate and the warehouse would return every plant's rows under the app's grant. Permission to act on the item is the handler's separate check.

<!-- section:dbxfe-apps-l01-operations -->

The app team owns code, manifest, `app.yaml`, validation, handler checks, state placement and logs; the data owner owns grants and row filters; the warehouse owner owns queuing; the platform team owns the workspace and support. An incident belongs to the layer whose evidence changed: a failed install is in the deployment log, a crash in the app log, a denial naming the app is a grant, and a slow queue starts with the handler's timing. Log request id, reviewer and timings, never a token.

<!-- section:dbxfe-apps-l01-deploy -->

Syncing files changes nothing a reviewer sees; the **deployment** builds and starts the new code, through the UI or the CLI:

```bash
# Not executed in this build; flags checked against the current CLI reference first.
databricks sync ./quality-review /Workspace/Users/<you>/quality-review
databricks apps deploy quality-review --source-code-path /Workspace/Users/<you>/quality-review
```

The sequence: bind, sync, deploy, build, start, verify with one named reviewer's claim, share, record. Declarative Automation Bundles, formerly Databricks Asset Bundles, declare the app and its resources per target. Every step here is labelled *not deployed*.

<!-- section:dbxfe-apps-l01-example -->

Imani presses **Claim** on `A-2031` revision 2. The browser posts `{"inspection_key": "A-2031", "revision": 2}` to `/v1/claims`; the platform authenticates her and forwards `X-Forwarded-Email: imani.q@cinderline.example`. The schema accepts the body, the handler takes `imani.q` from the header, and she and the item are both in plant `P2`. One claim is written in `quality_ops` under the app's principal with `reviewer = 'imani.q'`: `{"status": "claimed"}`. Leo, also in `P2`, claims a second later on another process; the store's one-claim rule rejects his insert and he receives `{"status": "conflict", "claimed_by": "imani.q"}` as a normal response. Tomas from `P1` gets 403, reason `plant`; nothing is written.

<!-- section:dbxfe-apps-l01-task -->

Write the blueprint for the quality app's architecture review: traces for view queue, claim and record disposition with who authenticates and whose permissions apply at each hop; the resource table; the state classification; validation rules per request; the ownership matrix; local mocked contract tests shown as Python and labelled not executed here; a deployment guide labelled *not deployed*; every unverified fact as an owned unknown. Nothing is added to SpicyBrain's own runtime.

<!-- section:dbxfe-apps-l01-solution -->

Traces: browser → sign-in → back end → warehouse and Lakebase under the app's principal, plant check in the handler; the queue read moves to the reviewer's token with the `sql` scope only if a per-plant row filter exists. Two of the mocked contract tests, shown and not executed here:

```python
# test_contract.py (synthetic teaching example; not executed in this build)
import pytest
from fastapi.testclient import TestClient
import server

class FakeClaims:
    def __init__(self):
        self.rows = {}
    def claim(self, key, revision, reviewer):
        holder = self.rows.setdefault((key, revision), reviewer)
        if holder != reviewer:
            return {"status": "conflict", "claimed_by": holder}
        return {"status": "claimed"}

@pytest.fixture
def client():
    server.deps.claims = FakeClaims()
    server.deps.plants_of = lambda r: {"P1"} if r == "tomas.b" else {"P2"}
    server.deps.plant_of_item = lambda key: "P2"
    return TestClient(server.app)

IMANI = {"X-Forwarded-Email": "imani.q@cinderline.example"}
TOMAS = {"X-Forwarded-Email": "tomas.b@cinderline.example"}
BODY = {"inspection_key": "A-2031", "revision": 2}

def test_injected_key_refused(client):
    r = client.post("/v1/claims", json={**BODY, "inspection_key": "A-2031' OR '1'='1"}, headers=IMANI)
    assert r.status_code == 422 and server.deps.claims.rows == {}

def test_other_plant_refused(client):
    assert client.post("/v1/claims", json=BODY, headers=TOMAS).status_code == 403
```

Deployment guide, *not deployed*: create the app, bind resources, sync, deploy, read the install step and first log lines, make one test claim as Imani and read it back, share with the reviewers' group, record the deployment. Unknowns: Lakebase region availability and user authorization status (platform lead), row filters and database-side enforcement (data lead), CLI flags (app team).

<!-- section:dbxfe-apps-l01-limits -->

A green mocked suite proves your handler's contract against fakes. It cannot prove the app's grants, the headers the platform sends, that the build resolves your pins, the port, or one active claim under concurrent inserts. Common mistakes: trusting a reviewer named in the body; claims in process memory; a warehouse binding treated as a data grant; printing the environment; rotating a secret without restarting; caching user-authorized results across reviewers. A hidden button or a system prompt is not access control.

<!-- section:dbxfe-apps-l01-sources -->

Four Apps pages (overview, authorization, resources, deployment) are cited as supplied in the build's source list and as previously read: the search budget was exhausted and the documentation host is blocked, so no title was re-confirmed and no page fetched. The Lakebase app-resource page was search-confirmed earlier in this build; two pages keep their original review dates. Header and environment details are marked for verification.

<!-- section:dbxfe-apps-l01-links -->

[GenAI, retrieval and agents](#/module/dbxfe-genai) chooses the model an app might call and contrasts app and user identity for agents. The module [Lakebase, Postgres and operational state](#/module/dbxfe-lakebase) turns claims and dispositions into constraints and concurrency tests; *Tools, MCP and action authorization* validates model output that proposes an action; the *Application state design* field guide is this lesson's template.

<!-- section:dbxfe-apps-l01-revisit -->

Redraw the three traces for the applied task's changed case, then review the cards. Reading or revealing the solution records no completion; mark completion only when you choose.
