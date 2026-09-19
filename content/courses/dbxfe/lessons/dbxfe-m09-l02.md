<!-- section:why -->

A polished result can be unconvincing if the audience cannot tell where it came from. Show the chain from question to evidence without drowning the listener in every implementation detail.

<!-- section:understand -->

A useful technical narrative has a beginning, a change, and a consequence. Begin with the customer question. Introduce a representative input or event. Show the rule that interprets it. Show the resulting output and what decision it supports. At each point, distinguish observed behavior from expected behavior and synthetic examples from customer data.

For fictional Cinderline, use inspection A changing from version 1 to version 2. The story is not “watch me click these screens.” It is “a correction should update the accepted inspection once, preserve the raw evidence, and change the unit-weighted total correctly.” That makes each screen or diagram serve a question.

Pause for explain-back. Ask the analyst which denominator the report uses, or ask operations what action the updated number would change. If the response reveals a different understanding, clarify the definition before continuing. Agreement cannot be inferred from silence or a friendly reaction.

<!-- section:see -->

**Authored demo script using synthetic data.**

1. “North plant currently has accepted A = 10/1 and C = 8/0, so the unit defect rate is 1/18, about 5.56%.”
2. “An approved correction changes A to 12 inspected units, still 1 defective unit. We preserve the input and select version 2.”
3. “Accepted totals become 20 inspected and 1 defective: 5%. Replaying the same correction should leave those totals unchanged.”
4. “This is the behavior we would test with your approved sample. Does the unit-based definition match your decision?”

All values are fictional. This script explains expected behavior; a live execution would need its own observed evidence.

<!-- section:deeper -->

Keep a visible evidence basis: input version, calculation rule, output, and limitation. If you use a screenshot or static example, label it as such. A schematic is not captured product UI. Avoid showing an expected result beside a spinner in a way that implies it has already been produced. The narrative can be concise while still exposing enough detail for a technical listener to challenge the reasoning.

<!-- section:customer -->

For a mixed audience: “The correction changes the accepted total once, and the report uses the same agreed denominator. Here are the input and expected result. In the pilot, we will compare actual output and replay behavior against this rule.”

<!-- section:try -->

Write a four-step narration for the duplicate delivery of ev1. Include the raw evidence, the identity rule, the expected unchanged accepted output, and a customer question that checks understanding.

<!-- section:revisit -->

A clear narration says: “This is the same event ID and payload arriving again. We retain delivery evidence, recognize the repeat, and avoid creating another accepted inspection. The accepted total should remain unchanged; the test compares exact rows and totals. Is repeated delivery a case your current process encounters, and does this handling match your source contract?”

The question invites correction of the assumption. If the source reuses event IDs for different payloads, the demo's simple rule is insufficient; stop and refine the contract rather than insisting the example proves correctness.
