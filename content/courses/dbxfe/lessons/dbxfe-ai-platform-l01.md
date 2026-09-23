<!-- section:dbxfe-ai-platform-l01-outcome -->

After this lesson you can place any managed AI proposal with one question: who writes the logic between the request and the model. You can tell pay-per-token, provisioned-throughput and external-model access apart, read an AI Function as a per-row model call, follow an agent onto a serving endpoint and say which AI Gateway controls apply to which endpoint type. You can choose among a Knowledge Assistant, a Supervisor Agent, a custom agent and a fixed retrieval workflow with five criteria, and record availability, cost and evaluation as dated assumptions. Nothing here calls a model.
<!-- section:dbxfe-ai-platform-l01-start -->

Bring the vocabulary of [GenAI, retrieval and agents](#/module/dbxfe-genai): retrieval finds evidence, generation writes the answer, tools act and evaluation measures. [Choose retrieval or a tool-using agent](#/lesson/dbxfe-m07-l02) is the general form of this lesson's choice; here it becomes a choice among named Databricks building blocks. Grants from [Unity Catalog, security and deployment](#/module/dbxfe-m06) and model versions from [MLflow, experiments and reproducibility](#/module/dbxfe-mlflow) are assumed. Product facts come from the Databricks SDK for Python 0.141.0, the Terraform provider v1.133.0 and MLflow 3.16.1, read in this build with their dates.
<!-- section:dbxfe-ai-platform-l01-map -->

Sort Databricks' managed AI building blocks by who writes the logic above the model:

| Block | Who writes the logic | Example request |
|---|---|---|
| Foundation-model access | Your application | One chat call to a hosted model |
| AI Functions | A SQL author | `ai_classify` on every row of a table |
| Agent Bricks agent | The platform, from your configuration | A technician's question to a Knowledge Assistant |
| Custom agent | Your team's code | The same question to your own agent |

Model Serving hosts all of them on Databricks-managed serverless compute; the AI Gateway governs endpoint traffic; MLflow traces and evaluates. The same model can sit behind every row, so a model's name never decides the block.
<!-- section:dbxfe-ai-platform-l01-access -->

Three access modes reach a foundation model. **Pay-per-token** endpoints are Databricks-hosted and charge for the tokens processed, which suits experiments and variable volume within the endpoint's limits. **Provisioned throughput** reserves capacity for one model, sized in model units with optional burst scaling; the charge follows the capacity kept, which suits steady production traffic that needs predictable performance. **External model** endpoints forward each request to a provider such as OpenAI, Anthropic, Amazon Bedrock or Google Cloud Vertex AI with a key referenced from a secret scope: you gain one endpoint, its permissions and its gateway controls, but the prompt, including retrieved text, goes to the provider. Cinderline's rule against sending manuals to third parties excludes that mode for manual content.
<!-- section:dbxfe-ai-platform-l01-functions -->

AI Functions put a model call inside SQL. Task-specific functions such as `ai_classify` and `ai_extract` fix the task; `ai_query` sends each row's request to a serving endpoint you name.

```sql
SELECT note_id,
       ai_classify(note_text, ARRAY('electrical', 'hydraulic', 'mechanical')) AS fault_family
FROM cinderline.maintenance.work_order_notes
LIMIT 200;  -- synthetic table; sample before a full run
```

Every row that reaches the function is a model call, so filter and deduplicate first: a join that repeats each note three times triples the calls on identical text. Store results with the endpoint and date that produced them. Signatures, supported compute and regional availability come from the current reference.
<!-- section:dbxfe-ai-platform-l01-serving -->

A serving endpoint exposes a model or agent as a REST service on compute Databricks manages outside your cloud account; callers need CAN_QUERY. For a custom agent, the agent framework's `deploy()` puts a Unity Catalog model version on an agent endpoint, enables its inference table, routes all traffic to the new version and keeps earlier versions served at zero traffic until deleted.

The AI Gateway on an endpoint offers rate limits in calls or tokens per minute per endpoint, user, group or service principal, input and output guardrails such as PII blocking, usage tracking in system tables, and inference tables. Which endpoint types get which feature is a dated fact: SDK 0.141.0 says external-model, provisioned and pay-per-token endpoints are fully supported and agent endpoints currently support only inference tables, while the Terraform provider v1.133.0 page states a narrower, older scope.
<!-- section:dbxfe-ai-platform-l01-bricks -->

Agent Bricks agents are configured, not coded. A **Knowledge Assistant** takes a description, optional instructions, examples with guidelines and knowledge sources: a vector search index, files in a Unity Catalog volume, or a table of file content. It reports an agent endpoint, an MLflow experiment and a state; files and file-table sources must be synced before new documents are known, while index sources follow their index. A **Supervisor Agent** routes each request among configured tools, such as Knowledge Assistants, Genie spaces, Unity Catalog functions, MCP connections and apps: autonomous tool selection, which answers more questions and adds wrong-tool and denied-tool failures. The Terraform provider v1.133.0 labels both resources Public Beta; that label does not say whether your region or workspace has them.
<!-- section:dbxfe-ai-platform-l01-custom -->

A custom agent is code: MLflow's `ResponsesAgent` wraps logic written with any agent framework, and the result is logged, registered in Unity Catalog and deployed.

```python
from databricks import agents
agents.deploy("cinderline.maintenance.manuals_agent", 3)  # synthetic model name and version
```

You control retrieval order, citations, tools and authentication, and you own dependencies, tests, tracing setup, evaluation and redeploys. Choose it when a requirement exceeds what configuration can express, not because code feels safer.
<!-- section:dbxfe-ai-platform-l01-choice -->

A fixed retrieval workflow takes the same steps for every question: retrieve permitted passages, then answer with citations or refuse. Its calls, latency and failure points are countable. Autonomous tool selection adds a routing decision to every question. Prefer fixed retrieval when one authoritative corpus answers most real questions and answers must be auditable; move to tools when a material share needs a second source, live data or an action, and write that threshold down before release. A Knowledge Assistant sits on the retrieval side of this choice because it selects no tools.
<!-- section:dbxfe-ai-platform-l01-tables -->

Four tables carry the decision.

| Pattern | Customization | Data access | Operations | Evaluation | Risk |
|---|---|---|---|---|---|
| `ai_query` batch | prompt per query | tables read | scheduled job | sample vs labels | wrong labels at scale |
| Knowledge Assistant | sources, instructions, examples | index, volume, file table | platform-built | examples, labelled set | opaque internals |
| Supervisor Agent | tools, descriptions | every tool's data | many tools | tool-call cases | wrong or denied tool |
| Custom agent | everything | what code reaches | your team | your harness | your bugs |

| Component | Hosts | Governs | Pays |
|---|---|---|---|
| Endpoints, Agent Bricks | Databricks | Cinderline | Cinderline |
| External model | Provider | Cinderline | Cinderline, to the provider |

| Building block | Label found | Region, workspace |
|---|---|---|
| Knowledge Assistant | Public Beta (Terraform v1.133.0) | unknown |
| Supervisor Agent | Public Beta (Terraform v1.133.0) | unknown |
| `ai_query` | no label found | unknown |

| Driver | Synthetic volume | Rate |
|---|---|---|
| Tokens × questions | 300 a day × 3,400 | check current pricing |
| Judge calls × rows × runs | 60 × 4 × 10 | check current pricing |
<!-- section:dbxfe-ai-platform-l01-example -->

Filter: external models are out for manual content. Score: the Knowledge Assistant meets the manuals-only need with the least owned code; a fixed retrieval workflow in code is the fallback if the assistant is not enabled in the region; the Supervisor Agent waits, because 52 of 60 labelled questions need only the manuals. Evaluate: run both retrieval candidates on the same 60 questions with `mlflow.genai.evaluate` and scorers for correctness, retrieval groundedness, safety and a citation guideline; run each row as its own caller, so a refusal case tests a real plant-2 technician; agree before any run that every refusal case must pass and no answer may cite a superseded revision; have a maintenance engineer review every failure. After release, sample the agent endpoint's inference table and the assistant's MLflow experiment into the same set.
<!-- section:dbxfe-ai-platform-l01-exercise -->

Another industry: fictional Harbourline Water wants field crews to ask about pump-station procedures from 900 PDF manuals, check whether a spare impeller is in the depot, and see the last three work orders for a station. Their labelled sample: 24 procedure questions, 12 stock questions, 9 history questions and 5 that should be refused. Crews are offline half the day. Choose a first-release pattern, name one alternative, fill the status and cost tables with unknowns and drivers, and write two blocking evaluation rules.
<!-- section:dbxfe-ai-platform-l01-solution -->

Stock and history make 21 of 50 questions, above a one-in-five threshold, so pilot a Supervisor Agent with three tools: a Knowledge Assistant over the manuals, a stock Unity Catalog function, and a work-order Genie space or table tool. The alternative is a fixed retrieval workflow for procedures plus links to the stock and history screens, which is safer if the supervisor's status or tool identities cannot be verified. Offline use is out of scope for any hosted endpoint; say so. Status cells for both agents, the region and tool identities stay unknown; rates read check current pricing, with drivers of questions × steps, tokens per step and evaluation runs. Blocking rules: every refusal case passes, and every stock question calls the stock tool.
<!-- section:dbxfe-ai-platform-l01-mistakes -->

- **Choosing by novelty.** A newer pattern decides more for you, which helps only when its decisions match your requirements.
- **Inferring status from an announcement.** A launch post fills no region, workspace or stage cell and says nothing about other clouds.
- **Assuming gateway features on agent endpoints.** Check the endpoint type against a dated artifact.
- **Treating an external endpoint as a data boundary.** The prompt still goes to the provider.
- **Quoting prices from memory.** Name drivers; take rates from current pricing on the day.
- **Averaging away a refusal failure.** Agree blocking rules before the first evaluation run.
<!-- section:dbxfe-ai-platform-l01-sources -->

- Databricks SDK for Python v0.141.0, read in this build: `serving.py` for endpoints, access modes, external providers and the AI Gateway; `aifunctions.py`; `knowledgeassistants.py`; `supervisoragents.py`.
- Terraform provider for Databricks v1.133.0, read in this build: the model serving, provisioned-throughput, Knowledge Assistant and Supervisor Agent resource pages, with their release-stage statements.
- databricks-agents 1.12.0, read in this build: what `deploy()` configures.
- MLflow 3.16.1, read in this build: `mlflow.genai.evaluate`, built-in scorers and `ResponsesAgent`.
- [Build agents on Databricks](https://docs.databricks.com/aws/en/agents) and [Evaluate and improve](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/), the course's reviewed agent and evaluation sources.
- Foundation Model APIs and AI Functions documentation: cited as previously read, neither fetched nor search-confirmed here, so their details are verification items.
<!-- section:dbxfe-ai-platform-l01-related -->

[GenAI, retrieval and agents](#/module/dbxfe-genai) for the general retrieval and tool boundaries; [MLflow, experiments and reproducibility](#/module/dbxfe-mlflow) for the model versions an agent endpoint serves; [Unity Catalog, security and deployment](#/module/dbxfe-m06) for the grants behind every tool. The retrieval, evaluation, tools and applications modules go deeper.
<!-- section:dbxfe-ai-platform-l01-revisit -->

Come back when a customer names a new AI feature. Place it on the map by who writes the logic, check its stage and availability against a dated artifact, add its cost drivers, and add the cases it needs to the evaluation set before anyone calls it the default.
