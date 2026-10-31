# Multi-Perspective Analysis, Conflict Resolution, and Report Narrative

[简体中文](analysis-synthesis.md) | English

Work from confirmed data contracts and metric tables. The goal is to cover decision-relevant questions, reconcile findings, and produce readable reports. Expert role names do not substitute for methodological justification.

## 1. Questions by perspective

Choose the smallest complementary set of perspectives supported by the decision and data. Row counts or a fixed number of experts do not justify a complex process. A simple question may need only one perspective. Work sequentially in the same agent by default; this procedure requires neither multiple agents nor additional role-based approval.

| Perspective | Candidate questions | Required evidence and limits |
| --- | --- | --- |
| Growth and mix | Which products, channels, or customers account for changes? Do existing and new segments differ? | Comparable periods, stable categories, contribution calculations; mix changes are not automatically causes |
| Profitability and efficiency | Does revenue growth translate into profit? How do costs, prices, volumes, and mix change? | Matching cost/revenue grain; missing costs cannot establish profit improvement |
| Customers and behavior | Are retention, churn, and purchase frequency changing? Do cohorts differ? | Customer histories, explicit windows and denominators; aggregate tables cannot reconstruct individual behavior |
| Operations and delivery | Do capacity, inventory, fulfillment, or service quality constrain outcomes? | Operational metrics aligned in time; absent data becomes a verification question |
| Risk and robustness | Could concentration, missingness, extremes, or definition changes alter conclusions? | Raw distributions, quality records, sensitivity checks, or group recalculations |
| Statistics and comparability | Are trends affected by seasonality, sample mix, or incomplete periods? | Sufficient history and suitable methods; do not force forecasts or significance tests to appear thorough |

For each selected question record `question_id`, `lens`, decision purpose, required metric/method IDs, evidence availability, and stopping conditions. Mark unsupported questions unanswered rather than inventing answers. Omit irrelevant questions with a brief reason.

Evaluate questions independently using the same frozen metrics, cutoff, and contract before synthesizing. Do not make the first conclusion a premise for every later perspective. Cite actual methods; do not impersonate famous experts or imply institutional endorsement.

## 2. Structured findings and conflicts

Extend the existing [claim ledger](contracts.en.md) with theme, question IDs, business impact and rationale, supporting/counterevidence claim IDs, alternative explanations, and proposed charts. Explain importance through decision impact, scope, urgency, and evidence strength; do not invent composite scores or confidence probabilities.

Synthesize in this order:

1. **Align:** check metrics, periods, entities, currencies, denominators, filters, and versions. Do not merge differing scopes directly.
2. **Deduplicate:** retain one canonical claim ID per fact and reference it elsewhere. Multiple perspectives reading the same data are not independent evidence.
3. **Classify:** distinguish duplicates, scope differences, arithmetic contradictions, complementary phenomena, and competing explanations.
4. **Verify:** apply [stepwise reconciliation](contracts.en.md) to numerical gaps, locating the first divergence and retaining residuals. Separate scope differences; seek evidence distinguishing competing explanations. Track substantive assumptions with assumption IDs, states, and impacts rather than prose alone.
5. **Synthesize:** organize by business theme, preserving confirmed common findings, unresolved disagreements, missing evidence, and action implications. Neither averaging nor majority votes resolves a conflict.

Do not publish affected definite claims while critical numerical contradictions remain unresolved; unaffected content may proceed. For descriptive co-occurrence say “occurred together”; with decomposition evidence say “change is concentrated in.” Reserve causal wording for appropriate identification or sufficient external evidence.

### Synthetic example

Revenue +20% year over year, profit -10%, and rising customer churn can all be true. They are not automatically contradictory and do not prove that low-quality customer growth caused profit to fall.

- Check that revenue/profit share scope and period and that churn uses a consistent customer definition.
- With cost or customer detail, examine cost changes and customer mix separately, recording support and counterevidence.
- Without it, state: “Revenue growth has not translated into improved profit, while retention is under pressure.” Keep explanations unresolved and list required cost/cohort data.

Conflict records retain `conflict_id`, related claim IDs, type, verification actions, results, unresolved parts, affected conclusions/recommendations, and final handling status.

## 3. Narrative components

Components define content contracts, not mandatory HTML, styling, or section counts. Render through project `visual-spec.md` and templates. PDF/PPTX/text share metrics, claim IDs, and semantic colors.

| Component | Inputs and structure | Conditions and limits |
| --- | --- | --- |
| Executive summary | Decision → most important verified findings → evidence → implications/limits | Select by importance rather than repeating every section; state when judgment is not yet possible |
| KPI card | Metric, value, unit, period, baseline, change, status, claim ID | Do not invent changes without a baseline; arrows show direction, colors follow whether change is favorable for that metric |
| Finding and evidence | Conclusion headline → data/chart → interpretation limits → decision relevance | Headlines must not be more certain than evidence; association is not a cause |
| Comparison/decomposition | Objects and comparability → change → contribution/mix → residuals/unknowns | Keep residuals visible; do not use attribution layouts to imply an explanation without decomposition data |
| Risks/disagreements | Risk/conflict → support and counterevidence → impact → checks needed | Do not amplify weak speculation through dramatic risk cards; unresolved disagreements must not be hidden only in appendices |
| Recommendations | Action → evidence → prerequisites → priority rationale → verification | Distinguish immediate, conditional, and evidence-gathering actions; unspecified owners, deadlines, and benefits remain proposals or unknowns |
| Sources/definitions | File/metric sources, cutoff, units, filters, limits, ledger locators | Reader-facing references must locate evidence; complete logs belong in run directories |

Usually use conclusion → evidence → risks/limits → action, adjusting for audience and task. Each page emphasizes one main question, supported by multiple charts if useful. Do not fabricate three risks or five recommendations to fill a template.

Use “Sales fell 20% year over year, concentrated in East China” only after verifying both claims; without regional evidence, retain only the first clause. “Check East China stockout records” is a valid next step without causal proof; “stockouts caused the decline” is not.

Organize by theme rather than perspective, preserving necessary scope differences and competing explanations. If the user wants the analytical process, put coverage and conflict records in appendices; do not add fictitious expert bylines.

## 4. Project integration and acceptance

Write applicable perspectives and question triggers into `analysis-rules.md`, and selected components/bindings into `report-spec.md`. Do not copy the entire candidate list. Keep current findings, question coverage, and conflicts in run records rather than freezing one period's facts into rules.

Acceptance checks: important questions have answers or explicit gaps; duplicate evidence is not counted repeatedly; unresolved conflicts are visible and constrain recommendations; summaries, titles, charts, and body use consistent claims; action strength matches evidence. A new perspective need not create a new section when it yields no substantive finding.
