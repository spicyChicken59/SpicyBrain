# Retrieval and evaluation plan — template

Fictional engagement: Harrowgate Field Services. Use `questions.json` as the labelled set, or extend it with your own questions in the same shape. No language model, workspace or endpoint is executed by this capstone; the plan describes what would be measured and how, and any local experiment is labelled as local.

## 1. Corpus and metadata

| Document field | Used for | Filter, rank or display? |
|---|---|---|
| id | | |
| version / effective date | | |
| status (current / superseded / draft / unofficial) | | |
| region | | |
| audience | | |
| supersedes / superseded-by | | |

Chunking rule and why:

## 2. Source-authority and freshness rules

Write the rule as the application would apply it, in order.

1. Which documents are eligible at all (status, audience, region, asker identity).
2. Which of two eligible documents wins when they disagree (effective date, bulletin scope, serial condition).
3. When the assistant must ask rather than choose.
4. How a superseded document is shown when history is explicitly requested.

## 3. Labelled set and metrics

| Metric | Definition (numerator / denominator) | Population from questions.json | Proposed threshold | Blocking? |
|---|---|---|---|---|
| Correct-source rate | | authorized questions with expected sources | | |
| Unauthorized disclosure count | | authorized = false questions | 0 | yes |
| Must-not-cite violations | | all questions | 0 | yes |
| Abstention correctness | | questions with empty expectedSourceIds | | |
| Verbatim fidelity for HFS-ISO-014 | | safety-adjacent questions | | yes |
| Denied-action correctness | | denied-action and prompt-injection questions | 0 actions taken | yes |
| Allowed-action correctness | | allowed-action questions | | |

## 4. Review method

Who reviews, against what, how disagreements are handled, and why an automated judge (if any) is calibrated rather than trusted.

## 5. What this plan cannot show

Coverage limits of a 22-question set; what only production questions will reveal; what remains unproven until a live evaluation is authorised.
