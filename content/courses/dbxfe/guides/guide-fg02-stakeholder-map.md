<!-- section:action -->

Build the map after the first two conversations and revise it after every later one; a stakeholder map that never changes was not being used.

1. **List every person who can fund, accept, operate or block** the outcome. Include the people nobody has introduced you to yet, such as the DBA or the security reviewer, and mark them as not yet met.
2. **Write each person's interest in their own words**, not in yours. "A trusted number by 8 a.m." is an interest; "digital transformation" is not.
3. **Rate influence on the decision separately from influence on delivery.** A plant analyst may have no budget authority and still decide whether the new report is used.
4. **Record what evidence each person needs to see** before they will support the next step, and in what form: a reconciled count, a permission test, a cost worksheet, a rehearsed failure.
5. **Plan the next conversation per person**: the one question you need answered, who should be in the room, and what you will bring.
6. **Mark conflicts** between interests explicitly, and do not resolve them on paper; name who has to.

Evidence to collect: names and roles as the customer states them, dated notes of who said what, any approval or sign-off each person has already given, and the disclosures still owed to you.

Go deeper: [the customer decision journey](#/module/dbxfe-m01) and [work with the account team](#/lesson/dbxfe-m01-l02) for responsibilities you share, [discovery and qualification](#/module/dbxfe-m02) for neutral questioning, and [field execution and communication](#/module/dbxfe-m12) for turning the map into owners and dates.

<!-- section:example -->

### Stakeholder map: Cinderline Components (fictional), quality-data engagement

Scope: the choice of which line to investigate at the 8 a.m. meeting; reflects the calls of 4 and 5 March and the plant visit of 9 March. Influence ratings are your judgement from those conversations, not facts.

| Person (role) | Interest, in their words | Influence: decision / delivery | Evidence they need | Next conversation |
|---|---|---|---|---|
| Operations director | "Which line do we investigate at 8 a.m., and can I trust the number" | High / Medium | Two reports agreeing for five days; a named operator | With the data lead: confirm the daily cadence is enough; ask who covers a failed feed |
| Quality lead | "Defective units over inspected units, corrections in approved order" | Medium / High | The metric contract written down; conflict handling shown on a sample | With the plant analyst: agree the business-day boundary and whether history is restated |
| Data lead | "We can give you synthetic records now; two engineers, part time" | Medium / High | A design the team can run without continuous support | Walk through the operating runbook; ask what they will not take on |
| DBA (not yet met) | Unknown; relayed as "CDC permission needs the DBA" | Low / High | Unknown until asked | Introduction via the data lead; SQL Server version, topology, change-capture permission |
| Security lead | "Classify the data, name the identities, review the source-to-cloud path" | High / Medium | Classification of inspection fields; identity list; a drawn request path | With the network owner: bring the request-path map and the access matrix; ask which fields are restricted |
| Sponsor | "Evidence for an expansion decision within a planning ceiling I have not approved" | High / Low | A readout with pass, fail and blocked separated; usage reported against the ceiling | Agree the readout format before the pilot, not after |
| Plant analyst | "Stop spending my week reconciling" | Low / High | The new report matching what they already know to be right | Ask which disagreements they trust their own workbook on, and why |
| Maintenance lead | "A read-only manual assistant later; keep the quality pilot bounded" | Low / Low | None for this pilot | None now; record the deferred request |

#### Conflicts recorded, not resolved

The operations director needs two reports agreeing for five days, which only real data can show; the security lead will not permit real data before a specialist review. Neither can be talked round by you, and the map says so. The sponsor wants evidence "within a planning ceiling I have not approved", and the data lead offers "two engineers, part time"; if the review delays the pilot, neither the ceiling nor that capacity stretches on its own, and the sponsor has to choose, not the data team.

#### Whose evidence is missing entirely

The DBA has been referred to twice and never spoken to. Every ingestion option depends on what they say about change capture and topology, so the next conversation with the data lead exists mainly to arrange that introduction. The security lead has stated requirements but not seen a drawing; the request-path map is the artefact that turns their requirements into a review they can perform.

#### Conclusion

Four people can stop this engagement: the operations director and the sponsor, who fund it, the security lead and, in practice, the plant analyst, who will not use a report that disagrees with a workbook they trust. The next three conversations, in order: the quality lead on the metric contract, the DBA through the data lead, and the security lead with a drawing. The operations director gets an update after those, not a meeting before them. Revise this map after each conversation and keep the previous version, because who was influential when is itself evidence about the account.

#### Revision log

9 March: first version, after the plant visit; the DBA added as not yet met.

<!-- section:template -->

### Stakeholder map

#### Scope

- The decision this map serves and the date of the conversations it reflects.

| Person (role) | Interest, in their words | Influence: decision / delivery | Evidence they need before supporting the next step | Next conversation: question, attendees, what you bring |
|---|---|---|---|---|
| Role first, name if known; "not yet met" if you have only heard of them | A quotation or close paraphrase from a dated note | Two ratings, each High, Medium or Low, with the reason in the note | A concrete artefact: a count, a test, a drawing, a worksheet, a rehearsal | One question you must have answered |

#### Conflicts recorded

- Each pair of interests that cannot both be satisfied as stated, and the person whose call it is.

#### Whose evidence is missing

- People referred to but not met, and which design choices wait on them.

#### Blockers and enablers

- Who can stop the engagement and on what grounds; who can unblock it and what they need.

#### Revision log

- Date, what changed on the map, and what conversation caused the change.

<!-- section:limits -->

The map records interests as people have expressed them to you and your judgement of their influence; it cannot establish organisational authority, hidden agendas or how people will behave under a budget decision. Influence ratings are opinions and should be dated and revised. The map does not replace the discovery brief, the requirements contract or an approval trail, and a person listed as an acceptor has not accepted anything until they do so in writing. Escalate when the decision owner and the budget owner name different next steps, when a required reviewer cannot be reached after two attempts through the customer, or when a stakeholder asks you to omit another stakeholder's stated constraint from what you present.
