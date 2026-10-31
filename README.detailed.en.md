# Project Report Workbench — Detailed Guide

English | [简体中文](README.zh-CN.md) | [Quick start](readme.md)

> Raw materials and generated outputs under `workspace/` are not distributed with the repository. Prepare the corresponding inputs before replaying examples below.

Accumulate project definitions, methods, templates, and scripts within one skill to produce recurring reports supported by evidence. The goal is analyst report delivery within an agreed scope.

During initial construction, combine historical Excel/CSV, corresponding analyst PDF/PPTX, and applicable methods into configuration and reusable pipelines. Later periods reuse scripts for processing, calculations, and report production; models handle synthesis and exceptions. Validation and feedback improve project capabilities.

**The current implementation comprises agent procedures, a project manager, and executable reporting components.** Additive periodic tables can become runnable pipelines from a brief. Complex business tasks need agent-built adapters, explanatory evidence, and templates. The system analyzes, writes, verifies, and handles exceptions without requiring analyst edits each period by default. Industry-wide analyst replacement has not been validated.

## Build a project quickly

The agent fills a brief from user materials using the [example structure](config/periodic-brief.example.json), then runs `scripts/onboard_project.py --brief <brief.json>`. CSV/XLSX with explicit periods, entities, and additive metrics supports change, contribution, and counter-trend analysis. Duplicate records, missing entities, invalid numbers, and unsupported questions block execution. HTML/Markdown, answers, and sources are retained together. Complex causality, forecasting, and multi-table definitions require adapters; removing questions is not acceptance.

The real-data quickstart has been validated and can be replayed with prepared local inputs:

```bash
.venv/bin/python scripts/project_manager.py run --project projects/electricity-quickstart/project.yaml --inputs workspace/onboarding-validation/inputs.json --cache-dir workspace/cache
```

See [project workflow](references/project-workflow.en.md) for fields/procedures. Ordinary `project_manager.py init` creates only empty configuration for custom projects.

## Demonstrated projects

The [UK regional electricity project](projects/uk-electricity/references/project-spec.en.md) uses two official DESNZ Excel/PDF releases to generate Chinese reports: 0.2.0 is a four-page factual version; 0.3.0 a fifteen-page full-topic candidate. Originals/source manifests reside in `workspace/public-fixtures/uk-electricity`.

```bash
.venv/bin/python -m pip install -r projects/uk-electricity/requirements.txt
.venv/bin/python scripts/project_manager.py run --project projects/uk-electricity/project.yaml --inputs workspace/public-fixtures/uk-electricity/2023-release/inputs-v0.5.json --cache-dir workspace/cache
```

Training-period normalized data is the baseline. When moving machines, move originals and rebuild it under the project SOP. For 0.3.0, medians of three runs were 1.164 seconds uncached and 0.468 warm, about 2.48×. This applies only to the fifteen-page template with prepared context/maps, no model calls, and excludes retrieval, evidence preparation, construction, and human review. Cache/full-recompute evidence and PDF bytes match; historical-revision and style-only cases were also checked.

[Version/feedback operations](references/project-lifecycle.en.md) support freezing, activation, rollback, and regression-backed resolution. The active project release remains 0.3.0, a topic-coverage candidate with source differences and business review unresolved. Candidate execution does not use the release pointer unless `--active` is specified.

The working configuration is a 0.5.0 candidate: Chart 2 uses net supply after own-use deductions; Chart 3 uses renewable-share curves. Chart data and metric definitions are checked together; the summary highlights regional nuclear divergence and operating/weather explanations appear with corresponding findings. It also outputs ten business pages plus five audit appendices. Regressions for 2022/2024 ran; 2024 source differences still block complete delivery. The frozen 0.4.0 report and 25/33 target comparison remain unchanged; these repairs are not a new blind test.

For 0.5.0, three-run medians were **1.38 seconds uncached / 0.73 warm**. The small quickstart sample measured **0.34 / 0.23 seconds**. Timings cover execution with prepared data/configuration/context, not initial construction, retrieval, or visual checks. See [regression records](projects/uk-electricity/evals/regression-0.5.0.json). Active 0.3.0 still uses `--active` and original `2025-release/full-inputs.json`.

## Core capabilities

| Capability | Approach |
| --- | --- |
| Project knowledge | Separate configuration, metric definitions, rules, SOPs, templates, tests; no new subskills |
| Historical learning | Conclusion → metric → calculation → source-location chains; separate facts, customs, assumptions, context |
| Visual system | PDF/PPTX colors, typography, grids, page types, chart semantics, content capacity |
| Script-first work | Reuse stable reading, cleaning, calculation, reconciliation, charting, template filling |
| Model synthesis | Compact evidence including counterevidence/limits, with drilldown when needed |
| Inspectability/resumption | Original arguments, configuration snapshots, fingerprints, outputs, logs, timings |
| Continuous validation | Numbers, evidence, visuals, cross-period checks before project upgrades |

Report reconstruction, method selection, and visual acceptance are agent procedures using host document tools and project scripts. There is no built-in universal PDF/PPTX parsing/rendering engine.

## Workflow

```text
Historical data + matching reports + business questions + applicable methods
                                  ↓
              definitions, analysis rules, visual specifications
                                  ↓
                 configuration + scripts + templates + regression
                                  ↓
New data → validate/calculate → evidence → narrative → report → acceptance
                                                                 ↓
                                      feedback → validate changes → upgrade
```

Keep projects' business assets isolated. Current facts/new assumptions remain in run records; validated improvements enter long-term rules. Do not append every report to `SKILL.md`.

## Getting started

### 1. Prepare the environment

Requires Python 3.10+. Run from the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r config/requirements.txt
.venv/bin/python scripts/project_manager.py --help
```

Base dependencies are `openpyxl` and `PyYAML`. Install project-specific PDF/PPTX, chart, and export tools as needed; base requirements do not include every reporting capability.

### 2. Ask the agent to establish a project

Use the [English skill guide](SKILL.en.md) and provide goals, historical data, and matching reports. Example:

> Follow this project's skill instructions to establish monthly-sales. Extract definitions, methods, colors, and layouts from historical Excel and corresponding PPTX; build reusable scripts/templates. Verify historical calculations, then evaluate later-period reports. Preserve unverified items and do not create a new skill.

Specify audience, decisions, periods/cutoff, and format. With multiple periods, split learning/tuning/final holdout before reading reference conclusions. Without historical reports, create a method-driven candidate. One period does not establish cross-period generalization.

Manual candidate initialization:

```bash
.venv/bin/python scripts/project_manager.py list
.venv/bin/python scripts/project_manager.py init monthly-sales
.venv/bin/python scripts/project_manager.py validate --project projects/monthly-sales/project.yaml
```

`init` creates `project.yaml`, not scripts/templates. Empty pipelines may validate configuration but cannot run. Implement rules, resources, and stages first. See [configuration fields and examples](references/project-workflow.en.md).

### 3. Run a new period

For an implemented pipeline declaring `data`, `period`, and `template`, save `inputs.json`:

```json
{
  "data": "sales-2026-10.xlsx",
  "period": "2026-10",
  "template": "report-template.pptx"
}
```

Relative file paths resolve from the input JSON directory; keys must match project configuration.

```bash
.venv/bin/python scripts/project_manager.py run \
  --project projects/monthly-sales/project.yaml \
  --inputs /path/to/inputs.json
```

The command prints a unique run directory, defaulting to `workspace/<project-id>/<run-id>/`, avoiding same-day overwrites. Use `--workspace /path/to/workspace` to change the destination.

### 4. Inspect and resume

Inspect `run_state.json`, `logs/`, and declared outputs. Only `checkpoint: true` pauses execution. For example, after reading evidence and writing a narrative draft at `compute`:

```bash
.venv/bin/python scripts/project_manager.py resume \
  --run-dir /path/to/run \
  --acknowledge compute
```

Replace `compute` with the actual waiting stage. Resumption retains original dates/templates/data and verifies dependencies/completed artifacts. Changed inputs/configuration/code/resources require a new run. Within-run resumption is conservative; `--cache-dir` enables explicit cross-run reuse, with quality stages always rerun.

Successful execution is engineering acceptance only; reports still need project-defined numerical, evidence, and visual acceptance.

## Directory structure

Projects/run directories are created as needed; project files are built for actual requirements.

```text
project-report-workbench/
├── SKILL.md                   # Canonical agent entry point; English guide: SKILL.en.md
├── agents/openai.yaml         # Skill display and invocation metadata
├── config/requirements.txt    # Base Python dependencies
├── scripts/                   # Management, profiling, calculation, timing
├── references/                # Analysis, visual, configuration, validation procedures
├── tests/                     # Synthetic helper/runner tests
├── evals/validation.json       # Executed checks and unverified scope
├── projects/<project-id>/
│   ├── project.yaml           # Identity, version, inputs, resources, stages
│   ├── references/            # Definitions, rules, report specifications, SOPs
│   ├── scripts/               # Calculations, validation, rendering
│   ├── templates/             # Clean templates and authorized assets
│   ├── tests/                 # Business regression
│   └── evals/                 # Project-version evidence
└── workspace/<project-id>/<run-id>/
    ├── run_state.json         # Arguments, snapshot, fingerprints, status, timings
    ├── logs/                  # Stage logs
    └── ...                    # Metrics, evidence, narrative, reports, acceptance
```

Raw data/references belong in authorized data/run directories. Shared skill distribution excludes customer projects, raw data, and generated outputs; project assets are shared separately as authorized.

## Available tools

| Tool | Purpose and limits |
| --- | --- |
| `scripts/project_manager.py` | `init`, `list`, `validate`, `run`, `resume`; schedules Python stages, not business algorithms |
| `scripts/project_versions.py` | Freeze, activate, roll back, evidence-linked feedback/regression |
| `scripts/stage_cache.py` | Explicit dependency cache, published only after whole-pipeline success |
| `scripts/profile_table.py` | Bounded `.xlsx/.xlsm/.csv` profiling; no cleaning/formula calculation/legacy `.xls` |
| `scripts/metric_math.py` | Decimal ratios, growth, additive contributions; projects establish comparability |
| `scripts/benchmark_command.py` | Command wall time, failures, repeated statistics; no token/cost/peak-memory measurement |

Profiling example:

```bash
.venv/bin/python scripts/profile_table.py /path/to/input.xlsx --out /path/to/profile.json
```

Optimize through code/template reuse, fewer repeated parses, and consolidated model synthesis. Measure construction and periodic execution separately. Establish actual gains with equal data and quality gates.

## Validation and current scope

Run shared tests:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Recorded validation includes 77 shared tests, 42 real-sample project tests, and 5 margin edge checks passing. 0.3.0 produced a fifteen-page PDF with 743 calculation/source checks and page-level visual review; 61 of 63 official-value comparisons matched, with 2 discrepancies retained. Historical two-period four-page validation remains separate. See [validation](evals/validation.json), [pilot results](projects/uk-electricity/evals/pilot-results.json), and the [0.4.0 cross-period review](projects/uk-electricity/evals/cross-period-review-2022.en.md).

This is cross-period replay, not strict blind testing. The expanded report covers official themes; weather, policy, and operations explanations use independent external evidence. Not every detail or causal assertion is reproduced. Human business review, full analyst-style causal investigation, PPTX, and large-data performance remain unverified; analyst-level or superior performance is not promised.

## Further reading

- [Project configuration and workflow](references/project-workflow.en.md)
- [Data processing](references/data-processing.en.md)
- [Metric, evidence, and assumption contracts](references/contracts.en.md)
- [Methods](references/methods.en.md) and [analysis/narrative](references/analysis-synthesis.en.md)
- [Report reconstruction](references/report-workflow.en.md) and [visual templates](references/visual-reverse-engineering.en.md)
- [Execution and performance](references/execution-performance.en.md)
- [Deliverables](references/deliverables.en.md) and [evaluation](references/evaluation.en.md)
- [Sources and adaptations](references/sources.en.md)

## Automatic diagnosis, tuning, and promotion

Quickstart projects support a bounded loop: identify missing required questions, create an isolated candidate, accept across three periods, archive/activate, then rerun the selected archive. Failure preserves the old version or rolls back.

```bash
.venv/bin/python scripts/auto_tune.py --project projects/<quickstart-project>/project.yaml --suite /path/to/suite.json
.venv/bin/python scripts/project_manager.py run --project projects/retail-monthly/project.yaml --active --inputs workspace/business-tuning-case/april-inputs.json
```

Synthetic retail automatically advanced from 0.1.0 to 0.1.1 by filling eight revenue/profit/order questions. Three-period numerical/coverage acceptance passed. Already-compliant projects should not repeatedly increment versions. Scripts handle recurring analysis/reporting without model recalculation each time.

Repairs currently cover supported change/contribution/anomaly question configuration. New definitions, arbitrary algorithms, causality, and visual templates need adapters. This is engineering validation, not real analyst-report comparison. See [lifecycle/recovery](references/project-lifecycle.en.md) and [tuning evidence](evals/auto-tuning-validation.json).

## Learning experience from historical reports

Adapted skill-training mechanisms include reconstruction/comparison, gap attribution, rule retrieval, and updates. Beyond fixed questions, the host can propose experience and modify isolated scripts/templates; the workbench validates across periods, archives, and switches versions. No additional agents or model service are launched.

- `experience_loop.py prepare`: freeze acceptance/references, reconstruct baseline, build learning packet.
- `recall`: find applicable rules, explicitly open bodies, record learning reads separately from production application.
- `learn`: verify quotes, attribution, and create/correct/reinforce/merge operations.
- `finish`: adopt only when all candidate periods pass and a baseline gap improves; rule-only edits without report improvement are rejected.

Retail advanced from 0.1.1 to 0.1.2: two synthetic references yielded a scale/margin synthesis rule, implemented as recomputable code. The third period reports revenue falling while profit rises and margin improves by 2.50 percentage points. Production `experience-applied.json` records applied rules and hashes. Experience and implementation are archived together without a new skill.

See [learning protocol, formats, and commands](references/project-lifecycle.en.md). Current evaluators cover periodic descriptive projects; synthetic cases do not establish real business-report quality. Body assertions are not complete semantic or visual scoring; real samples and specific acceptance remain necessary.

Retail now uses a customized learned engine; further iteration uses `experience_loop`. `auto_tune` only supports the original quickstart engine and does not overwrite custom implementations. See [experience-learning evidence](evals/experience-learning-validation.json).

## CI and releases

GitHub Actions runs shared tests on Python 3.10, 3.12, and 3.14 for PRs and main pushes. After all main checks pass, root `VERSION` determines an unpublished GitHub Release with source ZIP, tar.gz, and SHA-256 checksums. Published versions are not overwritten.

Update `VERSION` and add `release-notes/v<VERSION>.md`, then merge to main. Retry interrupted publication with **Re-run failed jobs** on the original run; **Run workflow** on main can also trigger validation/publication. Built-in `GITHUB_TOKEN` needs no personal token. Repository and example-project versions are independent. Inputs/generated outputs are excluded from release packages.
