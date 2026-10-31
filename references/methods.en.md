# Method Selection: Start with the Decision

[简体中文](methods.md) | English

These are candidate analytical approaches, not an authoritative library for every field. Verify industry standards, accounting rules, and regulatory definitions against user materials and applicable official sources. A source's reputation does not establish applicability.

## Selection guide

| Question | Preferred analysis | Requirements and limits |
| --- | --- | --- |
| What changed? | Totals, year-over-year/period-over-period changes, budget variance, absolute changes | Comparable periods and definitions; do not invent a prior-year comparison |
| Where is change concentrated? | Additive changes and contributions by dimension | Mutually exclusive, complete categories including unknowns; contribution is not causation |
| Why did a ratio change? | Separate numerator/denominator changes, weights, and mix | Recompute aggregate numerators/denominators rather than averaging group ratios |
| Is this unusual? | Distribution, historical baseline, seasonality, known events | Thresholds need business tolerance or validation; anomalies are not automatic deletion criteria |
| Are customers retained? | Fixed cohorts, observation windows, churn definitions | Complete customer/transaction histories; address right censoring and inconsistent windows |
| Did an intervention work? | Examine experiment/control and identification conditions first | Before/after changes and correlation do not prove causality; describe associations when identification is absent |
| What might happen next? | Compare candidate forecasts with naive/seasonal baselines | Sufficient history, rolling time validation, intervals, and errors; two periods cannot establish a long-term trend |

The NIST [EDA introduction](https://www.itl.nist.gov/div898/handbook/eda/section1/eda11.htm) supports exploring structure, anomalies, and assumptions first. Its [time-series introduction](https://www.itl.nist.gov/div898/handbook/pmc/section4/pmc4.htm) highlights trend, seasonality, and autocorrelation. Neither page endorses every business method above. Checked: 2026-10-31.

## Calculation conventions

- Default growth: `(current - previous) / previous`. With a zero or negative base, do not automatically report conventional growth; show absolute change and explain the business definition.
- Distinguish percentages and percentage points: 10% to 12% is +2 percentage points and +20% relative.
- Category contribution is `delta_i / delta_total`, only for additive metrics with consistent categories. Offsetting changes can produce contributions above 100%. Near zero net change, suppress unstable percentages and retain absolute changes; determine the near-zero threshold from business precision.
- Do not directly compare partial and complete periods. Explain assumptions and business-day differences for matched elapsed periods or daily averages; daily averages do not automatically remove holidays or seasonality.
- Do not fill missing categories with zero by default. Determine whether there were genuinely no transactions or data was not collected. Map classification changes or disclose noncomparability.

## Method cards

For each project method record `method_id`, decision question, authoritative/original source or “internal convention,” verification date, input requirements, algorithm, assumptions, scope, failure conditions, evidence requirements, and tests.

Seek recurring cross-period evidence and counterexamples before promoting historical experience to a rule. Experience supported only by the current period remains a hypothesis or conditional rule. Additional methodology enters the report body only when supported by data and relevant to decisions; otherwise place it in an appendix or omit it.
