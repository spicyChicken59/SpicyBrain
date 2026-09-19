<!-- section:why -->

The live page fails, or a customer asks a feature question you cannot verify. Your response can preserve a useful meeting without inventing evidence.

<!-- section:understand -->

When a demo fails, separate the explanation from the execution claim. State what happened in observable terms, avoid guessing the cause, and choose a bounded recovery path. You can use a clearly labeled static walkthrough to explain intended behavior, while retaining that the live path did not complete.

An unknown question needs the same discipline. Restate it precisely, say what you know, identify the uncertain part, and agree how the answer will return. “I will verify the exact source/version support with the specialist and send the documented boundary” is stronger than a confident guess.

For fictional Cinderline, if a sample load errors, do not switch to a prefilled result and let the audience assume it just ran. Say that the load failed, explain what the static example illustrates, and record the failed execution as a follow-up. An honest fallback can still help the customer understand the metric and test design.

<!-- section:see -->

**Fictional recovery dialogue.**

Customer: “Did that correction just run?”

Presenter: “No. The live load did not complete. This is the prepared synthetic output, showing the rule we intended to test. We can still agree the expected result now; I will capture the error and return with a verified run before calling execution validated.”

Customer: “Does this connector support our exact source setup?”

Presenter: “I have not checked that version and topology. Let us record them and have the integration specialist verify the supported path and prerequisites.”

The distinction preserves both the useful explanation and the missing evidence.

<!-- section:deeper -->

Time-box troubleshooting in a meeting. If investigation will consume the decision discussion, use the fallback and take diagnosis offline with an owner. Do not expose logs containing credentials or confidential records while improvising. A follow-up should state impact, observed symptoms, environment context, evidence gathered, open hypotheses, owner, and when the next update will occur. Do not promise a fix date without a basis.

<!-- section:customer -->

For the audience: “The live step failed, so I will not count it as passed. We can use the labeled example to discuss the intended behavior, then I will return the actual execution result and any limitations after investigation.”

<!-- section:try -->

Write a follow-up after a fictional demo failed before producing output. Include what was still agreed, what remains unverified, a proposed owner, and a next update—not a fabricated root cause or fix guarantee.

<!-- section:revisit -->

A useful follow-up: “We agreed the unit-based defect definition and expected correction result. The live sample load failed before output, so source-to-report execution remains unverified. I will coordinate with the integration specialist to inspect the error and environment assumptions; please confirm the source version/topology. We will provide the next update on the agreed date, including a verified rerun or a specific remaining blocker.”

This keeps the meeting's real progress without rewriting failure as success. The update date is a communication commitment; a resolution date would require additional evidence.
