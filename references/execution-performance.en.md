# Script-First Periodic Reporting Pipelines

[简体中文](execution-performance.md) | English

Initial construction establishes business understanding and executable capabilities. Later runs reuse validated code and templates. The skill builds and schedules pipelines from project configuration and handles exceptions requiring judgment. Do not reverse-engineer reports, select basic methods, or rewrite stable calculations every period.

## Two modes

**Build/upgrade:** use training materials to establish contracts, rules, and visual specifications; generate scripts/templates; verify calculations and holdout performance; measure speed and freeze versions. Material changes in definitions, structure, templates, or scope trigger upgrades. Without real data, deliver candidate procedures rather than claiming a working pipeline.

**Periodic execution:** read the released version and current inputs, check compatibility and assumptions, then calculate, build evidence, generate necessary narrative, render, and validate. New categories can use existing contract rules. Changed key-field semantics require isolating affected analysis and returning to upgrade mode, not having the model guess a repair.

## Responsibilities

| Stage | Default execution | Model involvement |
| --- | --- | --- |
| Reading, mapping, cleaning, grain/join checks | Validated scripts and versioned configuration | New structures or unknown business semantics |
| Metrics, comparisons, contributions, reconciliation | Deterministic scripts emitting values, units, definition versions, sources | Selecting new methods or resolving unsettled definitions |
| Established anomaly rules and routine findings | Script detection with candidate facts and evidence IDs | Assessing importance, competing explanations, external context |
| Numbers and fixed descriptions | Conditional templates with missing-data branches | Cross-theme synthesis, limitations, recommendations |
| Charts, template filling, page ordering, export | Validated generation scripts | New page types or content beyond layout capacity |
| Checks and acceptance | Automated checks and established visual inspection | Semantic judgment and inspection of actual pages |

Routine reports may need no narrative model call. Synthesis reports typically send a compact evidence packet for one consolidated draft, then validate and insert it. Fewer calls are an optimization goal, not a hard cap; add calls when new evidence, conflicts, or revisions require them and record why. Perspectives are question lists, not one model call each.

## Minimum script interface

Organize code by business complexity. A small task may use multiple stages in one script; microservices, workflow frameworks, and many files are not mandatory. Schedule through `scripts/project_manager.py` ([configuration](project-workflow.en.md)). Business scripts must implement their documented arguments, `--help`, input manifest, output directory, stage/resume options, and exit behavior.

Recommended boundaries:

```text
Input and compatibility checks → normalization/calculation → evidence packet
                                                               ↓
                                               template narrative / model synthesis
                                                               ↓
                                               charts/report export → acceptance
```

Write calculations as JSON/tables for downstream stages, including metric/claim IDs, exact values, units, sources, quality states, and applicable versions. Model input must retain key counterevidence, gaps, and unresolved conflicts, not just positive Top-N findings. Allow drilldown via stable locators instead of loading complete spreadsheets or historical reports by default.

Model output is structured narrative with claim IDs. Prefer references that scripts format into numbers. Validate reference existence, applicability, and required fields before filling templates. Interpretation strength still needs semantic checks; valid JSON is not quality acceptance.

The host agent can perform model work: scripts generate evidence, the agent writes narrative, and the runner resumes downstream stages. A separate API integration or saved keys are unnecessary. Direct API use must respect existing user environment, authorization, and cost constraints.

Stages emit explicit success/failure, input fingerprints, code/config versions, and output manifests. Nonzero exits are not completion; do not reuse partial outputs. Write temporary output, validate, then atomically publish within the current run directory, without overwriting released reports. Canonical metrics and dependency IDs are the source of truth; do not maintain separate formulas in scripts, prose, and charts.

## Cache and incremental work

Follow [data-processing cache rules](data-processing.en.md), with stage-specific dependencies:

- Normalization: source content, sheet/range, schema, mapping, cleaning code, contract version.
- Metrics: normalized partitions, historical window, formulas/filters, dimension versions, assumption states, effective configuration.
- Narrative, if enabled: complete evidence packet, task, rules, model/prompt settings, context cutoff. Cache accepted narrative only; changed dates, metrics, or assumptions invalidate old conclusions.
- Charts/reports: metrics/narrative, templates, visual rules, fonts, generation code, target format, relevant renderer environment.

Do not infer unchanged content from filenames, paths, or modification times alone. Verify manifests and integrity. Content edits, historical backfills, refunds/deletions, and late data invalidate dependencies. Rolling windows, cumulative metrics, and cohorts may affect multiple periods: recompute actual dependencies. When dependency scope is unknown, recompute the relevant stages fully rather than appending under the label “incremental” and creating duplicates.

Template-only changes may reuse valid metrics. Current-period changes need not repeat visual reverse engineering. Propagate upstream changes downstream. Use run isolation or locks for concurrent writes, otherwise execute sequentially. Cache hits must not bypass current quality gates, expired assumptions, or failed validation.

## Speed and cost acceptance

Time initial construction and periodic execution separately. Do not present build cost as recurring cost or warm-cache time as first-run performance. Fix representative data size, history, page count, format, machine, dependencies, and model settings. Record:

- End-to-end and per-stage time: reading/validation, calculation, model, rendering/export, acceptance.
- Cache state and reused scope, rows/file sizes, pages, failures, retries.
- Model call count, input/output tokens, costs, and their sources. Mark unavailable measures null/unknown; command count is not model call count.
- Peak memory with measurement tool/scope. Main-process measurements are not whole-pipeline peaks.

`scripts/benchmark_command.py` measures wall-clock time, failures, and repeated-run statistics for an existing command. It does not clear caches, count tokens, collect memory, or generate business reports. Each command must write a separate run directory or be idempotent. Prepare cold, warm, and historical-revision environments separately; relabeling runs does not create distinct scenarios.

First compare correctness for one cold run, one warm run, and one historical revision. If comparison is needed, repeat timing under identical settings and report sample size, median, and range; tiny samples cannot establish reliable P95. Key metrics and evidence states must agree with uncached full recomputation. Different binary report hashes do not alone imply numerical errors.

Record user latency/cost targets and measurement definitions when provided. Otherwise report the measured baseline and largest bottleneck before optimizing; do not invent “generated in seconds.” First remove repeated Excel parsing, repeated model reads/per-page generation, and unnecessary rendering. Keep the same quality gates; do not manufacture speed by dropping factual checks, counterevidence, or visual acceptance.

When models are unavailable, deliver a template-based factual draft only if the contract permits it, stating that synthesis is absent. Do not mix old recommendations into a new report or claim equivalence with full analysis. Without business samples, provide measurement entry points and pending acceptance items, not business speedup claims.

## Recorded demonstration measurements

The UK electricity project enables normalization, calculation, and rendering cache via `--cache-dir`; check/verify always execute. See [project lifecycle](project-lifecycle.en.md). Within-run resumption still uses complete fingerprints; cross-run reuse uses declared stage dependencies.

`workspace/uk-electricity-benchmark-02/benchmark.json` records three cold, three warm, and three uncached runs plus style-change and historical-revision comparisons. Median times: 0.698, 0.297, and 0.687 seconds; warm versus uncached is about 2.31×. Evidence and PDF bytes match; revised-input results match full recomputation. No model calls; tokens and peak memory were not measured. Initial construction, visual inspection, and human business review are excluded. Do not extrapolate to large datasets or model-written reports.

The fifteen-page 0.3.0 benchmark is `workspace/uk-electricity-benchmark-04/benchmark.json`: cold 1.189 seconds, warm 0.468, uncached 1.164 (medians of three each), about 2.48×. External documents, context manifests, and maps were prepared in advance; retrieval/manual preparation is excluded. The older four-page benchmark does not represent the new version.

Experience learning separates construction and production. During construction, the host compares history, retrieves rules, attributes gaps, and edits candidates. Production executes validated scripts/templates. Scripts may record applied rule IDs and hashes (`experience-applied.json` in the retail example). Do not count construction model work as zero or present small synthetic runtimes as complete PDF/PPTX production speed. Rule-title routing returns at most eight items and requires opening bodies explicitly, avoiding full rule-pool context every period.
