<!-- section:action -->

Build the model so that a reader can change any input and see what moves. That means every input is labelled with its unit, its currency, its period and where it came from, and the arithmetic is visible.

1. **Separate the cost model from the benefit model.** They have different inputs and different owners, and mixing them hides which side is uncertain.
2. **List cost inputs by category:** compute, platform usage, storage, data movement, operations effort, one-time implementation, dual operation during transition. Each with unit, currency, period, and a source label: measured, quoted, or hypothetical.
3. **List benefit inputs:** the work that changes (hours, errors, delays), its unit value, and a realization factor stating how much of the released work becomes a real change.
4. **Write the arithmetic** in a form that can be recomputed by hand for one case.
5. **Run low, base and high cases** by varying the inputs the owners are least sure of, and show which single input flips the sign.
6. **Compute break-even** on the driver the decision turns on.
7. **List excluded costs and benefits** and say why each is excluded.
8. **State the period** and whether one-time costs are included in the year shown.

Evidence to collect: the input table with labels, the arithmetic, the sensitivity table, the break-even line, the exclusions list, and the names of the people who own each uncertain input.

Deeper: the retained lesson [Make a transparent value calculation](#/lesson/dbxfe-m11-l03), [Compute choices, cost and FinOps reasoning](#/module/dbxfe-finops) for the sensitivity model and the cost worksheet, [Competition and business value](#/module/dbxfe-m11), and [Proofs of value](#/module/dbxfe-m10) for measuring the uncertain inputs during the pilot.

<!-- section:example -->

**Fictional worked example: Cinderline's illustrative annual model for the one-plant quality path.** Every number below is a hypothetical teaching input in hypothetical US dollars, per year unless stated, supplied by the fictional sponsor for this exercise only. None is a price, a quotation, a benchmark or an observed saving.

### Inputs

| Input | Value | Unit | Currency and period | Source label | Owner of the uncertainty |
|---|---|---|---|---|---|
| Hours released per week | 5 / 10 / 15 | hours per week | n/a | Hypothetical (low / base / high) | Operations director |
| Working weeks | 48 | weeks per year | n/a | Hypothetical | Sponsor |
| Value per released hour | 60 | currency per hour | hypothetical USD | Hypothetical | Sponsor |
| Realization factor | 0.5 / 0.75 / 1.0 | fraction | n/a | Hypothetical | Operations director |
| Recurring platform and operations cost | 12,000 | currency per year | hypothetical USD, per year | Hypothetical | Data lead |
| One-time implementation | 15,000 | currency, once | hypothetical USD, year one only | Hypothetical | Data lead |
| Dual operation during transition | 0 / 1,500 / 3,000 | currency | hypothetical USD, year one only | Hypothetical | Data lead |

### Arithmetic

Gross annual labour value = hours per week × weeks × value per hour. Realized value = gross × realization factor. Year-one net = realized value − recurring cost − one-time implementation − dual operation. Recurring-year net = realized value − recurring cost.

Base case by hand: 10 × 48 × 60 = 28,800. Realized at 0.75 = 21,600. Year-one net = 21,600 − 12,000 − 15,000 − 1,500 = −6,900. Recurring-year net = 21,600 − 12,000 = 9,600.

### Sensitivity (hypothetical USD)

| Case | Hours per week | Realization | Dual operation | Realized value | Year-one net | Recurring-year net |
|---|---|---|---|---|---|---|
| Low | 5 | 0.5 | 3,000 | 7,200 | −22,800 | −4,800 |
| Base | 10 | 0.75 | 1,500 | 21,600 | −6,900 | 9,600 |
| High | 15 | 1.0 | 0 | 43,200 | 16,200 | 31,200 |

### Break-even

On the recurring year, realized value must reach 12,000: at a realization of 0.75 that is 12,000 ÷ (0.75 × 48 × 60) = 5.56 hours per week; at 1.0 it is 4.17. On year one with base dual operation, realized value must reach 28,500, which at 0.75 is 13.2 hours per week. The decision therefore turns on two inputs: the hours actually released and how much of that time becomes a real change. Both belong to the operations director and neither has been measured; the pilot's baseline week is where they get measured.

### Which input flips the sign

Holding everything else at base, year one turns positive only above about 13 hours per week, or at 10 hours only if realization is 1.0 and dual operation is zero. The recurring year stays positive down to about 5.6 hours per week at base realization. A reader should conclude that the recurring year is robust to modest inputs and year one is not, which is an argument for measuring, not for choosing the high case.

### Excluded

Training time for analysts (not estimated); storage growth beyond the first year (unknown volume); any revenue effect of a better morning decision (not claimed, because no mechanism has been shown); internal support effort beyond the operator's hour per day (unmeasured); price changes over the period (unknown). Each exclusion is listed so a reader can add it, not so it can be forgotten.

### What this model is

An illustration of drivers and their sensitivity over a hypothetical year, with every input labelled. It is not a savings promise, not a platform quotation, and released time is not cash unless the customer decides to make it so.

<!-- section:template -->

### Period and framing

- **Period modelled, currency, whether one-time costs are in the year shown, and the sentence stating that the model is illustrative.**

### Cost inputs

| Input | Value | Unit | Currency and period | Source label (measured / quoted / hypothetical) | Owner of the uncertainty |
|---|---|---|---|---|---|
| Compute, platform usage, storage, data movement, operations effort, one-time implementation, dual operation | | | | | |

### Benefit inputs

| Input | Value | Unit | Currency and period | Source label | Owner |
|---|---|---|---|---|---|
| The work that changes, its unit value, the realization factor | | | | | |

### Arithmetic

- **The formulas in words, and one case computed by hand so a reader can check.**

### Sensitivity

| Case | Varied inputs | Realized value | Year-one net | Recurring-year net |
|---|---|---|---|---|
| Low / base / high | | | | |

### Break-even and the flipping input

- **The driver the decision turns on, its break-even value, and which single input changes the sign.**

### Exclusions

- **Each excluded cost or benefit with the reason and whether it could change the decision.**

### Measurement plan

- **Which uncertain inputs will be measured, where, and by whom.**

<!-- section:limits -->

This model establishes how a decision depends on its inputs and which inputs matter most; with hypothetical inputs it establishes nothing about actual cost or value. Real rates depend on product, cloud, region, edition, workload and commercial terms that must be read from current authoritative sources and dated; this guide contains none. Released time is not a cash saving until the customer decides what happens to the time. A sensitivity table is not a forecast, and the high case is not a target. Escalate, or stop presenting the model, when a reader begins quoting a case as expected value, when a benefit is counted twice under different names, or when the decision turns on an input nobody owns.
