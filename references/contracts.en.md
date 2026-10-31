# Input, Rule, and Evidence Contracts

[简体中文](contracts.md) | English

JSON/YAML or equivalent structures are sufficient. The fields below describe semantic requirements; no database or framework is required.

## Input manifest and data contract

For each period record boundaries, cutoff, timezone/fiscal calendar, completeness, data/report paths and SHA-256, availability date, business scope, version, and training/tuning/final-holdout role. Report data may contain revisions: verify versions. Historical reconstruction uses only data/context known at that time.

For each fact table record sheet/range, header row, grain, primary/join keys, original/canonical field names, types, units, currency, missingness definitions, valid values, subtotal rules, and join cardinality. Each metric records formula, filters, denominator, weights, baseline, rounding, reconciliation tolerance, and definition version. Tolerance follows units and purpose, not a universal `1e-6`.

## Metric semantics and versions

Maintain definitions in the existing data contract, not a duplicate semantic repository. Use stable `metric_id` values and explicit versions, covering:

- **Meaning and purpose:** plain-language definition, supported decision, source/definition owner (unknown when unknown), target/favorable direction, and justification. Do not invent industry thresholds.
- **Calculation and dependencies:** formula, numerator/denominator, dependent metrics/versions, base/ratio/cumulative/derived type, and input-to-output path.
- **Scope and time:** subjects, included/excluded entities, event/posting dates, timezone, period completeness, validity dates, and date the definition became known.
- **Grain and aggregability:** what a row represents, supported analytical dimensions, and additive dimensions. Balances cannot simply be summed over time; ratios require recomputing numerator/denominator; distinct users across overlapping groups cannot be added.
- **Exceptions and changes:** refunds, cancellations, duplicates, missingness, zero/negative denominators; change rationale, replacement versions, comparability strategy.

Identically named but differently defined metrics need distinct IDs or variants. Aliases do not prove equivalence. Do not apply a new definition directly to old periods to calculate growth: recompute consistently or disclose noncomparability. Preserve definitions known at the historical point. Later revised data used to restate history must be labeled a restatement, not an as-of-time result.

## Metric reconciliation

When sources, reports, or recalculation disagree, add `reconciliation` to existing conflict records rather than creating another fact ledger:

1. **Freeze snapshots:** record A/B hashes, refresh/cutoff, metric versions, periods, grain, calculation paths, and original values. Authoritative sources still require verification.
2. **Quantify gaps:** retain signed `A-B`, absolute difference, and relative difference with an explicit denominator. For zero denominators use absolute differences or an agreed scale, not infinity. Tolerances derive from units, rounding, and business requirements, not universal percentages.
3. **Locate divergence:** align time/timezone, scope/filters, deduplication, join cardinality, null handling, aggregation, and rounding. At every step record counts, key totals, and unmatched keys to locate the first divergence. Samples explain detail; difference amounts require complete reconciliation.
4. **Bridge differences:** explain the total with mutually exclusive, nonduplicated adjustments and a residual. State ordering if it affects attribution. Retain unexplained residuals when reliable decomposition is impossible; never force balance.
5. **Resolve and verify:** distinguish calculation bugs, definitions, refresh delays, rounding, and unknowns. Correct current calculations, isolate dependent claims, or select sources using known official definitions. Do not modify upstream systems on your own. Record recomputation evidence, residuals, and affected reports.

Use `open`, `resolved`, and `accepted_difference`. Record the origin even below tolerance; do not conceal systematic errors. Without authority to resolve a definition dispute, keep it open and block only dependent claims. Bridge records contain `source_a/source_b`, `gap`, `tolerance_basis`, `first_divergence`, `adjustments`, `residual`, `resolution_evidence`, and linked `claim_ids`.

## Assumption lifecycle and invalidation

Give each substantive assumption an `assumption_id`, content, type (data/business/statistical/technical), rationale, scope, dependent metric/rule/claim IDs, consequences if wrong, verification method, evidence, last-check date, and recheck triggers. Explain high/medium/low confidence rather than converting it into invented probabilities or automatic risk scores.

Distinguish `unverified`, `supported`, `refuted`, `needs_recheck`, and `superseded`. Having checked an assumption does not mean it is supported. Record every transition with evidence and retain prior versions. Weakly supported assumptions affecting key conclusions require evidence, sensitivity analysis, or isolation of the conclusion; checks are not reserved only for low-confidence labels.

Each period, check changes in sources, field meaning, missingness, business rules, windows, and method prerequisites. Triggered changes move supported assumptions to needs_recheck. Do not carry them across periods without checking scope.

When refuted or requiring recheck, trace direct and indirect dependencies to metrics, derived metrics, claims, recommendations, charts, and pages. Mark them pending review/recalculation so they are not reused as certain. Missing dependency metadata means impact coverage cannot be claimed complete: conservatively inspect related analysis chains and disclose gaps. Update states using fresh recomputation evidence, not labels alone.

Example: a synchronization failure refutes “missing sales means zero.” Quarantine rows, reassess totals, growth, regional contributions, and affected historical reports. Preserve original reports and revision notes. Regenerate local versions only within existing authorization; do not automatically overwrite publications or send correction messages.

## Claim ledger

Example claim with synthetic values:

```json
{
  "claim_id": "C-001",
  "period": "2026-02",
  "kind": "computed_fact",
  "text": "Sales fell 20% from the previous period",
  "metric_id": "net_sales",
  "value": "-0.20",
  "unit": "ratio",
  "evidence": [
    {"artifact": "metrics.json", "key": "net_sales.current", "value": "80"},
    {"artifact": "metrics.json", "key": "net_sales.previous", "value": "100"}
  ],
  "calculation": "(80-100)/100",
  "lineage": {
    "input_manifest": "input-manifest.json",
    "source_locator": "Sales!A2:F51",
    "filters": "period=2026-02; exclude subtotal",
    "transform_version": "v1"
  },
  "reference_location": "human.pdf#page=3",
  "status": "recomputed",
  "limitations": []
}
```

`kind` distinguishes `computed_fact`, `external_fact`, `hypothesis`, and `recommendation`. Explanations/recommendations may lack numeric values but must link factual claim IDs and state assumptions, missing evidence, and applicability. `status` distinguishes recomputed, source-verified, pending, and contradictory claims. Valid formatting is not factual correctness. Training `reference_location` must not enter generation context.

Metric claims record `metric_version`; claims record `assumption_ids` and upstream `depends_on_claim_ids` as applicable. After assumption invalidation, `review_status` is `current/needs_review/invalidated`, separate from whether numbers were once recomputed (`status`). Earlier numerical correctness does not establish current premises. Dependencies must not self-cycle; missing references must explicitly fail or be marked as impact-coverage gaps.

## Multi-perspective findings and conflicts

For cross-question synthesis, extend the same ledger without duplicating values:

- `question_ids`, `lens`, `theme`: questions answered, perspective, business theme.
- `importance_reason`: basis for decision impact, scope, urgency; no invented scores.
- `supports`, `counterevidence`: supporting and opposing claim IDs. No recorded counterevidence does not prove none exists.
- `alternative_explanations`, `evidence_gaps`: plausible alternatives and evidence needed to distinguish them.
- `canonical_claim_id`: deduplicated fact ID; repeated perspectives are not independent evidence.
- `chart_recommendation`: chart question, metric IDs, comparison scope; a graphic does not strengthen evidence by itself.

Record necessary conflicts with `conflict_id`, `claim_ids`, type (scope difference/arithmetic contradiction/competing explanation), checks, results, unresolved parts, affected claims/actions, and status. Complementary phenomena do not require artificial conflicts. See [analysis and narrative](analysis-synthesis.en.md).

## Rule cards and release manifest

Rule cards include ID, type (company definition/method/presentation), trigger, action, exceptions, source, supporting periods and counterexamples, status, and test IDs. Runtime rules exclude historical reference prose and holdout conclusions; full training evidence stays in development records.

Release manifests record skill runtime version; project configuration/script/template versions and hashes; rule IDs; data-contract version; dependencies; evaluation settings; generation isolation; sample splits; executed results; and unverified scope. `candidate` means available for trials. `validated_for_scope` means evidence exists only for the listed business, definition, and time scope, not arbitrary new data.
