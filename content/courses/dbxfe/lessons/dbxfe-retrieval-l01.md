<!-- section:dbxfe-retrieval-l01-outcome -->

After this lesson you can engineer the retrieval step behind a maintenance assistant: decide which collections may answer, trace how parsing and chunking decide what can be found, apply authority, version and permission rules before ranking, explain a TF-IDF score term by term, choose lexical, vector, hybrid or reranked retrieval, assemble cited context, and grade retrieval with recall@k and MRR. Every number comes from Lab L20, an executed local TF-IDF baseline over synthetic documents; nothing needs a workspace or a model call.

<!-- section:dbxfe-retrieval-l01-start -->

Bring the retained [GenAI, retrieval and agents](#/module/dbxfe-genai) module: an answer sees only its selected context, a chunk must keep its labels, relevance and permission are separate tests, and a citation must support its sentence. The lesson [Choose retrieval or a tool-using agent](#/lesson/dbxfe-m07-l02) sets the pattern choice; this lesson builds the retrieval half in depth. For access control itself, [Unity Catalog, security and deployment](#/module/dbxfe-m06) explains privileges. You need to read a short Python function and a SQL `WHERE` clause; TF-IDF, cosine similarity, recall@k and MRR are defined here.

<!-- section:dbxfe-retrieval-l01-authority -->

Retrieval returns only what was indexed, so start with a source inventory: one row per collection with its owner, version rule, readers and whether it may be cited. Cinderline's approved manuals are citable at their current revision, plant procedures for the caller's plant, training notes as context only; drafts, superseded revisions and unowned notes are excluded.

Parsing then decides what text exists. Treat it as a stage with its own table of typed elements (headings, paragraphs, table rows, figure descriptions) carrying file and page. A torque table flattened to `Machine Torque M7 95 M8 120 Nm` has lost which value belongs to which machine, and a page that fails to parse silently removes a procedure. On Databricks, `ai_parse_document`, as defined in the SDK read for this lesson, parses files from a Unity Catalog volume into pages and elements and lists failed pages separately.

<!-- section:dbxfe-retrieval-l01-chunks -->

A chunk is the unit that is scored, returned and cited. Lab L20 packs whole sentences within a section: a 20-word budget gives single-sentence chunks, an 80-word budget whole sections. Neither is right in general; the answer unit (one instruction, one table row) and the context budget decide.

Each chunk is a record, not just text:

| Column | Read by |
|---|---|
| `chunk_id` | citations, labels, deduplication |
| `family`, `version`, `effective_date`, `status` | supersession, effective-date and authority rules |
| `region`, `audience` | permission |
| `title`, `heading` | the contextual header and citation label |

A contextual header (`M7 press service manual. Hydraulic unit.`) is text the index scores; a column is a value a rule filters on. Keep that distinction: headers change rankings, columns change admission.

<!-- section:dbxfe-retrieval-l01-admission -->

Four rules run before any score is computed: approved status, effective on the question's date, the current version of its family, and visible to the caller. Filtering after ranking fails twice: restricted chunks are scored and ranked (and appear in any trace), and they use up result slots. Telling the model to ignore restricted passages fails completely, because the text has already been delivered.

Versions are rules, not scores. Only the highest approved version effective on the question's date may answer, whatever its load date. An index adds a third clock: an AI Search Delta Sync index follows its source table through a TRIGGERED or CONTINUOUS pipeline, so a triggered index can lag behind a new revision. A freshness preference is different again: a small, scoped bonus for recent time-sensitive documents, such as bulletins, that have no version link. It never overrides a rule.

<!-- section:dbxfe-retrieval-l01-ranking -->

TF-IDF weights each token by its count in a chunk times its rarity, `idf(t) = ln((1 + n)/(1 + df(t))) + 1` with scikit-learn's defaults, scales vectors to unit length and ranks by cosine similarity. It rewards rare shared tokens and repetition; it has no idea that 'setting' and 'Set' are related. Vector retrieval embeds text with a model and returns nearest neighbours, which helps paraphrases and can blur exact codes. Hybrid search merges both ranked lists, for example by reciprocal rank fusion, which adds 1/(k + rank) from each list and so needs no comparable scores. A reranker then reads the question with each of the top few candidates and reorders them; it cannot add a chunk that retrieval missed. Databricks AI Search, formerly Vector Search, exposes ANN, HYBRID and FULL_TEXT query types and an optional reranker.

<!-- section:dbxfe-retrieval-l01-context -->

Context assembly spends a budget: take hits in rank order, skip repeated text, stop when the next chunk would exceed the budget, and label every entry with document, section, version and effective date. The labels let a reader tell the M7 manual's 200 hours from the M8 manual's 300 hours when both enter. Carry `chunk_id` into citations and reject any citation that is not in the context: a deterministic check that catches invented and out-of-context citations. Whether a cited passage supports its sentence is a separate question.

<!-- section:dbxfe-retrieval-l01-evaluation -->

Write relevance labels, as chunk ids, before any run. Recall@k is the share of a question's relevant chunks in the first k results; MRR averages 1 over the rank of the first relevant chunk. Keep questions with no authorized answer out of those averages and report what they must not return: counts of restricted, superseded, draft and not-yet-effective chunks. Groundedness, whether an answer is supported by its context, needs the answer and a reviewer, a person or a judge calibrated against people; MLflow provides judge-based retrieval scorers for it.

<!-- section:dbxfe-retrieval-l01-managed -->

AI Search is the current name of the managed vector and keyword search service formerly called Vector Search, as the Databricks-published `databricks-ai-search` client (0.78) states. Read in this build from that client and the Databricks SDK for Python (0.141.0): indexes live on STANDARD or STORAGE_OPTIMIZED endpoints and are named by a Unity Catalog table name; a Delta Sync index follows a source Delta table, with embeddings computed from a text column by a model endpoint or supplied as vectors, while a Direct Access index is written through the API; queries choose ANN (default), HYBRID or FULL_TEXT, pass filters and can add a reranker. Region availability, preview status, limits and pricing are on the documentation page, which this sandbox could not fetch: treat each as a verification item. The inventory, metadata, labels and pass bar remain the team's.

<!-- section:dbxfe-retrieval-l01-example -->

Lab L20 indexes 18 synthetic documents for four callers and 13 labelled questions.

| Pipeline, chunk size | recall@1 | recall@3 | MRR@5 | restricted chunks returned |
|---|---|---|---|---|
| similarity alone, small | 0.5417 | 0.6667 | 0.6458 | 12 |
| admit then rank, small | 0.7083 | 0.875 | 0.8778 | 0 |
| admit then rank, large | 0.8333 | 0.9167 | 0.8917 | 0 |

Three failures are built in. **The wrong chunk wins:** for 'What is the M7 press relief valve setting?' a training note (0.5192) and a neighbouring sentence (0.4209) outrank the answer (0.2674), which says 'Set'. **A newer authorized revision changes the context:** with revisions 4 and 5 loaded on 10 September, the filter question answers 200 hours that day, 150 on 20 September and 120 on 5 November. **A relevant unauthorized document is never returned:** the South lockout procedure, the best lexical match for a North technician, is excluded before ranking, and the contractor never receives the engineering-only overpressure test. Large chunks score higher but put 92.08 words into the top three against 49.31.

<!-- section:dbxfe-retrieval-l01-exercise -->

Cinderline adds an East plant with its own lockout procedure, and contractors will use the assistant for site rules only. Without looking at the solution, write: the inventory rows for the new collections; the chunk record fields that change; the admission rules for an East technician and for a contractor, and where they run; three labelled questions that would catch a mistake (one restricted, one version, one paraphrase), each with its expected result; and the metrics you would report, including what an unanswerable question must not return.

<!-- section:dbxfe-retrieval-l01-solution -->

Inventory: the East lockout procedure is citable for region east, audience technician and lead, owned by the East operations lead and versioned by revision and effective date; contractor site rules are citable for contractors. Chunk records are unchanged except that `region` gains `east`. Admission before ranking: approved, effective by the question date, current version, and visible (region match or `all`, group in audience). Labelled questions: (1) an East technician asks how to lock out a press before clearing a jam; expected: the East procedure first and no North or South chunk anywhere in the list; (2) a question dated just before and just after the East procedure's new revision takes effect; expected: each cites its own revision; (3) a paraphrase such as 'why does the East belt line shake after start-up?'; expected: its labelled vibration chunk within the top three, or a recorded lexical failure that motivates a hybrid test on the same labels. Report recall@1, recall@3 and MRR@5 per class, and safety counts that must all be zero.

<!-- section:dbxfe-retrieval-l01-mistakes -->

- **Filtering after the top-k cut.** Restricted text is scored and traced, and the list starves (1.85 of 3 results in Lab L20).
- **Treating a system prompt as access control.** The restricted passage is already in the context.
- **Letting similarity pick the revision.** Rev 2 and rev 3 score 0.4651 and 0.4694; only a version rule separates 250 from 200 hours.
- **Using the load date as the effective date.** A revision loaded early answers early.
- **Tuning for one question.** Editing a manual to contain 'setting' hides the defect from the next evaluation.
- **Averaging unanswerable questions into recall.** Report what they must not return instead.
- **Reading one mean.** A higher average can hide one restricted chunk; compare per class.

<!-- section:dbxfe-retrieval-l01-references -->

- [databricks-ai-search 0.78](https://pypi.org/project/databricks-ai-search/0.78/): Databricks-published AI Search client; metadata and wheel source read in this build.
- [databricks-sdk 0.141.0](https://pypi.org/project/databricks-sdk/0.141.0/): generated AI Search and AI Functions definitions read in this build.
- [Databricks AI Search](https://docs.databricks.com/aws/en/ai-search/ai-search): documentation page; not fetchable from this sandbox, recorded by this repository's earlier review.
- [TfidfVectorizer, scikit-learn 1.9](https://scikit-learn.org/1.9/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html): defaults read from the installed library's docstrings.
- [mlflow 3.16.1](https://pypi.org/project/mlflow/3.16.1/): retrieval metric and scorer docstrings read from the installed package.

Availability, preview status, limits and pricing were not verified in this build.

<!-- section:dbxfe-retrieval-l01-related -->

The RAG evaluation plan field guide turns these metrics into a pilot decision: a source set, cases written before any run, stage-by-stage attribution and blocking failures. The GenAI evaluation module adds traces and judges, and the tools module covers retrieved text that asks for an action. For the quality and cost framing, revisit [Evaluate quality, risk, and operating cost](#/lesson/dbxfe-m07-l03).

<!-- section:dbxfe-retrieval-l01-revisit -->

After the evaluation module, redo the relief-valve diagnosis: predict which remedy raises its reciprocal rank without lowering another question, then check the lab's per-term table. In a week, explain without notes why a post-filter can pass every permission test on the final answer and still be the wrong design.
