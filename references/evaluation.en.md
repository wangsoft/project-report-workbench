# Evaluation, Revision, and Behavioral Scenarios

[简体中文](evaluation.md) | English

## Define acceptance before viewing answers

Split contiguous, nonoverlapping training, tuning, and final-holdout periods. Related companies/customers or pages from one report are not independent samples. Fix model, tools, available context, data budget, and format. Hide reference reports/feedback using isolated generation contexts or directory allowlists. If the host cannot isolate them, disclose contamination risk rather than calling it strict blind testing.

Acceptance priorities:

1. **Factual gate:** independently recompute key figures and reconcile totals. No unresolved critical unit/denominator errors or unsupported causal claims. Style scores cannot offset critical errors beyond agreed tolerance.
2. **Analytical quality:** coverage of major changes/anomalies, sufficient evidence, importance-based ordering, actionable recommendations, necessary uncertainty.
3. **Delivery quality:** complete delivery within declared scope without analyst additions, critical omissions, text/chart consistency, readability, runtime, and cost. Manual editing effort is a development diagnostic only.

Evaluate “replacing analysts” against project tasks, not a single accuracy statistic or successful template render. Automated checks verify data, metrics, and sources; agents inspect question coverage, interpretation, and rendered pages; independent development evaluations establish capability. Routine periods do not mandate analyst editing. Missing required answers, undefined denominators, or unsourced central explanations block complete delivery. Attempt repairs first and request business input only when genuinely missing.

Rules/tests must not merely duplicate the generation algorithm. Use hand-checkable fixed values, independent recomputation, and edge cases. LLM comparisons are soft evaluation. Flag errors in original reports too; independently verify insights absent from references.

## Three ablations

- A: applicable generic methods plus company data contracts needed for calculation, without historically learned rules.
- B: the same contracts plus historical report rules, without extra library methods.
- C: the same contracts plus historical rules and applicable methods.

Use identical factual standards and data visibility. Do not disadvantage A by withholding necessary definitions. Anonymize/shuffle outputs for business reviewers to assess accuracy, omissions, usefulness, and edits. Do not claim statistical significance from tiny samples. If no people evaluated outputs, explicitly state that soft assessment was model-based.

Hold visual specifications constant when comparing analysis, so attractive layout is not mistaken for analytical improvement. Evaluate visuals separately. Learn visual rules only from training materials or predefined brand templates, not holdout reports used to choose the closest layout.

## Visual acceptance

Under [visual procedures](visual-reverse-engineering.en.md), separately record structure, page-by-page renders, and capacity stress cases. Assess editability, brand/semantic colors, hierarchy, layout, readability, and adaptation, not a full-page pixel similarity score. Missing fonts/renderers leave explicit unverified scope. Without real references, procedure completeness is not template-reconstruction validation.

## Attribution and revision

Measure cold/warm cache, historical revisions, stage timings, and available model costs under [execution/performance](execution-performance.en.md), separating construction from recurring work. Keep inputs, output format/page count, model settings, and quality gates constant. Incremental/cache outputs must match full recomputation in metrics and evidence states. Timer-helper tests do not establish business-pipeline speedup.

Evaluate perspectives/narrative under [synthesis procedures](analysis-synthesis.en.md): answered/unanswered questions, deduplicated evidence, resolved/disclosed conflicts, summary/body agreement, and evidence-proportionate actions. To isolate a new capability, fix data, model, visual rules, and other rules, enabling/disabling only the relevant question list or component. Section and role counts are not quality measures.

Fix parsing before downstream rules; definition errors require contract/test fixes; correct but unselected rules need trigger-description changes. Generalize rules only with multiple periods or explicit business definitions. Reading a rule does not prove it caused an outcome; use with/without ablations when needed.

Record versions, rationale, failures, and before/after results. By default, after two unsuccessful revision rounds, retain candidate status and report problems. Do not overwrite a better version when final-holdout results deteriorate. State publication scope. Once final-holdout results inform revision, collect unseen samples for new holdout evidence.

## Behavioral exercises (definitions, not claimed passes)

Also verify metric IDs/versions and additivity; same-scope A/B snapshots; nonduplicated adjustments and visible residuals; supported/refuted/recheck distinctions; and downstream effects on claims, actions, and charts. Complete logs do not replace recomputation evidence.

| Scenario/minimum input | Observable expected behavior | Failure |
| --- | --- | --- |
| One Excel period and report | Candidate rules/evidence, cross-period evidence pending | Claiming generalization |
| Only methodology and field definitions | Method-driven candidate with real-sample requirements | Invented historical reports/training results |
| Formula present but cache empty | Block affected metrics; propose recalculation in a copy or independent computation | Treating empty cache as zero |
| Report blames competitor promotion; data contains only volume | External-evidence requirement/hypothesis | Promotion stated as fact or recurring rule |
| Two transactions; dimension key occurs twice | Detect many-to-many risk before join and block doubled amounts | Sum after a fanout join |
| Current 80, previous 100, reference says -10% | Recompute -20% and record contradiction | Changing to -10% to match |
| Historical materials include final holdout | Exclude its report/feedback from generation and document isolation | Reading answers, then claiming a blind test |
| Zero net change, two regions offset | Absolute regional changes, no infinite contributions | All contributions zero or infinity |
| New channel and missing key field next period | Compatibility warning; isolate dependent metrics, retain valid analysis | Fill zero and claim complete delivery |
| PPTX fonts/colors inherited from themes/masters | Resolve inheritance/overrides and verify rendering | Replace absent local values with default font/black |
| Scanned PDF only | OCR plus rendering; confidence-tagged style estimates, reconstructed editable template | Claim exact original masters/chart data |
| Channel order changes and one new channel | Keep entity colors stable; assign a new style | Colors follow rank and change meaning |
| Longer title, more categories, negative values | Adapt layout/paginate/reset axes and render | Shrink to fit, clip negatives, retain invalid axes |
| Old values in notes/embedded workbooks | Clean package and bind new metrics | Edit visible text only |
| No source report or renderer | Candidate visual rules with pending checks | Claim validated visual reconstruction |
| Revenue up, profit down, churn up; no cost/customer detail | Align scope, combine complementary facts, preserve explanation gaps | Assert poor-quality customer growth or force a contradiction |
| Three perspectives cite one sales summary | One canonical claim with references, no added weight | Three independent sources claimed |
| Same-scope/period claims say +10% and -10% | Recompute; block affected claims/actions until resolved | Average, vote, or select flattering claim |
| Small single-metric query | Applicable questions and necessary components only | Mandatory perspectives, risk cards, fixed recommendations |
| Body has correlation; summary says “causes” | Weaken summary and preserve evidence links | Keep causal headline for impact |
| Missing evidence and unknown action benefit | Verification action or conditional advice; no invented gain | Promised benefits/deadlines/owners to fill cards |
| “Active customer” means login in one source, purchase in another | Separate variants/versions; explain noncomparability | Growth calculated solely from matching names |
| Month-end balance or distinct users in overlapping groups | Aggregate only permitted dimensions; recompute detail if needed | Sum across time/groups |
| A=100, B=90; independent filter difference=6; residual=4 | Gap 10, explained 6, residual 4; continue checking | Force balance or select “authority” |
| Different refresh times or zero relative-gap denominator | Same-cutoff snapshots; absolute gap for zero denominator | Call refresh lag a business decline or output infinity |
| “Missing means zero” refuted; growth/actions depend on it | Mark direct/indirect outputs for review and recalculate before restoring | Relabel assumption or change a note only |
| Supported assumption with changed source | Trigger recheck and inspect scope | Reuse because previously validated |
| Later definitions reconstruct old periods | Explicit restatement/version, historical definitions and limits preserved | Claim historically available information |
| New period, same structure | Frozen scripts/templates; consolidated narrative if needed | Relearn all reports, rewrite formulas, per-page calls |
| Filename unchanged, historical content revised | Fingerprint invalidation through affected windows/downstream; full-recompute agreement | Filename/append-only reuse |
| Template colors only changed | Reuse valid metrics, regenerate affected graphics/report | Reuse old report or needlessly recompute all history |
| Rendering failure or missing narrative references | Record failure, do not publish full report; resume valid stages only | File existence as success or old advice reused |
| Speedup claimed after dropping checks | Reject comparison; remeasure identical scope | Count reduced validation as equal-quality speedup |

Record pass/fail only after execution with real files/isolated runs. Unit tests establish helper behavior in listed cases, not PDF/PPTX reading, model reasoning, or real-business outcomes.

## Runner validation scope

Synthetic tests cover refusing existing-project overwrite; unrunnable empty candidates; isolated same-day runs; preserved period/template arguments on resume; rejecting changed inputs/configuration/completed outputs; nonzero exits/missing artifacts; rejecting unverified partials; path escapes/output overlap; and exclusive run locks. Structural validity does not establish business, narrative, visual, or performance acceptance. Projects still require real-sample regression.

## Executed example

[UK electricity pilot results](../projects/uk-electricity/evals/pilot-results.json) distinguish automated data/file checks, official-value comparisons, agent visual inspection, and pending human business review. Summaries were exposed during retrieval, making this cross-period replay rather than blind testing. That recorded example covers the four-page factual template, not every scenario in this document.

### Independent tuning acceptance

`scripts/tuning_evaluation.py` separates acceptance from candidate changes: frozen multi-period inputs and independent numerical answers, delivery/source/artifact fingerprint checks, required questions in report bodies, and per-period timeouts. Tuning cannot change answers, tolerances, or questions to pass. Numerical/question coverage does not establish insight, causality, or visual quality; use suitable real samples and specific evaluations. A viewed or revision-informing holdout replay is not a strict blind test.
