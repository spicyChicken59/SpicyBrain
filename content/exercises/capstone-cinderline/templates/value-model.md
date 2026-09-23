# Value model (template, hypothetical inputs)

Fictional exercise. Every input below is a labelled hypothetical planning
figure from the capstone's own disclosures. Real prices need current product,
cloud, region, edition and commercial terms. Released time is redeployed
capacity, not a cash saving, unless the customer decides otherwise. Nothing
here is a savings promise.

## Inputs (hypothetical, labelled)

| Input | Value | Source | Status |
|---|---|---|---|
| Hourly rate | $60 | sponsor statement | hypothetical |
| Weeks per year | 48 | sponsor statement | hypothetical |
| Recurring annual cost | $12,000 | sponsor statement | hypothetical, incomplete |
| One-time implementation | $15,000 | sponsor statement | hypothetical |
| Hours/week released: low / base / high | 5 / 10 / 15 | sponsor statement | scenarios |
| Measured reconciliation effort today | about 13 hours/week | plant controller | hypothetical baseline |
| Engineer-hours per misdirected investigation | 4 | plant controller | hypothetical |
| Expediting cost per held unit | $250 | plant controller | hypothetical |
| Misdirected decisions per year | unknown | no log exists | must be measured |

## Arithmetic (reproduce it; do not paste the model's)

Gross annual value = hours/week × weeks × rate. Year-one net = gross −
(recurring + implementation). Recurring-year net = gross − recurring.

| Scenario | Hours/week | Gross value | Year-one net | Recurring-year net |
|---|---|---|---|---|
| Low | 5 | | | |
| Base | 10 | | | |
| High | 15 | | | |
| High, capped at the measured baseline | 13 | | | |

Break-even hours/week = (recurring + implementation) / (weeks × rate) = [ ].

## Lines kept out of the base case, and why

| Candidate benefit | Hypothetical arithmetic | Why it is $0 in the base case | What would let it in |
|---|---|---|---|
| Avoided misdirected investigations | events/year × (4 × $60 + units × $250) | no incident log; frequency unknown | a counted log over the baseline period |
| Company-wide reliability | — | not observable from a one-plant test | |
| Scrap reduction | — | no causal basis | |

## Exclusions and sensitivity

- Excluded costs: [internal operations time, training, storage and networking, migration delay, dual operation, DBA change-window cost, …]
- The input that moves the answer most: [ ]
- What must be measured before an investment recommendation: [ ]
