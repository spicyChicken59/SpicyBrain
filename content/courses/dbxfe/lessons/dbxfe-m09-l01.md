<!-- section:why -->

You have 15 minutes in a customer meeting. A successful session does not require showing every feature; it requires helping the audience understand the next decision.

<!-- section:understand -->

Define who is attending, what they already know, what decision follows the demo, and what uncertainty blocks that decision. An operations sponsor may need to see a trusted quality number and its freshness. A data engineer may need to inspect correction handling. A security lead may need to understand identity and boundary assumptions.

These interests can share one narrative if the demo follows a single data story. Start with the business question, show the relevant result, reveal enough of the technical path to explain it, and return to the decision. Do not begin with an unrelated interface tour and hope the audience connects it later.

For fictional Cinderline, a useful intent is: “By the end, operations and the data lead can judge whether this metric and correction flow are worth testing on an approved one-plant sample.” That is narrower and more observable than “impress the customer.”

<!-- section:see -->

**Reusable demo preparation note, filled with fictional inputs.**

| Preparation item | Cinderline example |
|---|---|
| Audience | Operations sponsor, analyst, data lead |
| Decision | Agree a bounded quality pilot? |
| Core question | Can everyone interpret the same corrected metric? |
| Show | Synthetic inspection correction → accepted total → report |
| Ask | Does this definition match the decision you make? |
| Exclude | Unverified source connectivity and production performance |
| Fallback | Labeled static walkthrough with expected synthetic rows |

This note keeps the presenter honest about which uncertainties the demo addresses.

<!-- section:deeper -->

Confirm data permissions and remove sensitive or irrelevant material from the presentation environment. Rehearse the sequence, reset synthetic state, verify readable text at the actual display size, and prepare a fallback that preserves the explanation. If a live environment has not been validated, do not rely on it as the sole evidence path. These are general preparation recommendations, not internal account procedures.

<!-- section:customer -->

For the meeting opener: “Today we will follow one synthetic inspection correction into the quality report. The aim is to agree the metric and what a useful one-plant test would measure. We are not using this walkthrough as proof of your source connectivity or production speed.”

<!-- section:try -->

Write a demo intent for a fictional meeting attended only by security and the data-platform owner. Choose one core question, what to show, and what to leave conditional.

<!-- section:revisit -->

A useful intent: “Determine which identity and deployment-boundary questions must be resolved before an approved quality-data pilot.” Show a labeled schematic, the proposed access matrix, and the intended positive/negative access tests. Leave exact source connectivity, region-specific networking, and entitlement conditional until the specialist review.

This may be an architecture walkthrough rather than a live feature demonstration. That is appropriate if it better serves the decision. The presentation format should follow the evidence need.
