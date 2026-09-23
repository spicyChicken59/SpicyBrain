# Harrowgate Field Services — capstone data pack

Everything in this directory is **fictional**. Harrowgate Field Services, its regions, technicians, equipment lines (Ridgeback R2, Aldercroft AP-7, Brindle B3, Coldwater C40), document ids, policies, ticket ids, part numbers, torque and interval values and the incident are synthetic teaching material authored for the SpicyBrain academy capstone *Service knowledge and controlled actions* (`#/practice/dbxfe-capstone-service-knowledge`). No value here is real equipment or safety guidance; nothing here is to be used on real machinery. No real customer, vendor, technician or employer is described.

The pack contains only Markdown, JSON and CSV. Nothing needs to be installed, and no language model, Databricks workspace or endpoint is executed by the capstone. Any local retrieval experiment you choose to run over these files is your own local execution and should be labelled as such.

## Dictionary

| File | What it is | How the capstone uses it |
|---|---|---|
| `documents/*.md` | Twelve short document excerpts, each with header lines `id`, `title`, `version`, `effective`, `supersedes`, `superseded-by`, `status`, `region`, `audience`, `fictional` | The corpus. Four kinds of trouble are planted: a current manual and a bulletin that disagree for a subset of units (HFS-SM-R2-3.0 §5.1 versus HFS-FB-2026-07); a superseded isolation procedure beside the current one (HFS-ISO-014-v3 / v4); a region-restricted supplement (HFS-CST-022-v1) and a level-restricted section (HFS-SM-AP7-2.0 §6.2); a draft (HFS-SM-C40-DRAFT-2.0), an unofficial wiki tip (HFS-KB-TIP-088) and an irrelevant administrative document (HFS-ADM-011-v1). |
| `stale-content.md` | HFS-SM-R2-2.1, the superseded torque procedure behind fictional incident HFS-INC-0417 | Must be filtered out of current-procedure answers and labelled as history when explicitly asked about. |
| `injection-fixture.md` | A ticket note containing a planted instruction to order parts and close the ticket, with an authored answer key | The benign prompt-injection case. The correct behaviour is to treat the note as content, refuse the action, cite HFS-PR-04-v2 §4, and report the embedded instruction. |
| `questions.json` | 22 labelled questions: asker role and region, whether the asker is authorized, expected source ids, documents that must not be cited, the expected answer property, category and difficulty; plus the list of blocking failures | The labelled set for the retrieval and evaluation design. Extend it in the same shape if you need more cases. |
| `authorization-matrix.csv` | 46 rows of `principal, document_or_action, allowed, reason` | The starting authorization matrix. `allowed` takes `yes`, `no`, `history-only`, `no-authority`, `conditional` or `delegated-only`; the reason names the policy or guide it comes from. Nothing enforces this matrix; your design says where it would be enforced. |
| `templates/discovery-synthesis.md` | Stakeholders, facts/unknowns/assumptions, follow-ups | Requirement 1 of the scenario |
| `templates/evaluation-plan.md` | Corpus metadata, authority rules, metrics on the labelled set, review method | Requirements 2 and 4 |
| `templates/authorization-boundary.md` | Identities, where each fact lives, actions with approval steps, denied-action wording, untrusted content, negative tests | Requirement 5 |
| `templates/recommendation.md` | One-page recommendation with a mixed/negative outcome section and ownership table | Requirements 3, 6 and 9; requirement 8, the pilot charter, has no template in this pack |

## Document header lines

Every document begins with the same header lines so that a submission can reason about metadata rather than prose. `status` is one of `current`, `superseded`, `draft`, `unofficial` or `untrusted content`. `region` is `all`, `north`, `south` or `coastal`. `audience` names the fictional roles defined in `questions.json`, or a group of them: `all technicians` means technician-l1, technician-l2 and technician-coastal; `all staff` and `finance` are wider groups outside the labelled set; an unofficial page's audience is `unknown`. Membership is cumulative: a technician-coastal is also a level-2 technician, and a service supervisor reads what their technicians can read, restricted supplements only with the matching endorsement. Where sections of one document have different audiences (HFS-SM-AP7-2.0), the header names each. Where a document overrides part of another (the bulletin), `supersedes` says which section and under which condition.

## How to use the pack

1. Read the capstone brief in the app first and open the stakeholder disclosures deliberately; the brief is missing things on purpose, and several of them are answered only in the disclosures.
2. Read every document header before any body. Build your own table of what is current, for whom, since when.
3. Work through `questions.json` by hand: for each question decide which documents are eligible for that asker, which one wins, and whether the right outcome is an answer, a clarification, a refusal or an escalation. Compare with the expected property only after you have decided.
4. Use `authorization-matrix.csv` and `injection-fixture.md` for the authorization and state boundary; write the negative tests, not only the allowances.
5. Fill the four templates, then write the executive recommendation and the technical appendix. Reveal the model submission in the app only after your own is complete.

## Provenance

Authored for the SpicyBrain academy. The documents imitate the shape of a versioned service library; they copy no real manual, policy, vendor document or training material. Numeric values are marked synthetic. The incident, the regions, the endorsement and the approval-id formats are inventions that exist to make the exercise concrete.

## Cleanup

The pack creates nothing on your machine. If you copied it to a working directory or built a local index over it, delete only your working copies and your index; keep your written answers. No credentials, environments, accounts or cloud resources are involved.
