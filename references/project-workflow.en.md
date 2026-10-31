# Project Configuration, Execution, and Accumulated Knowledge

[简体中文](project-workflow.md) | English

## Three engineering principles

1. **Separate configuration from shared code:** each project's `project.yaml` binds its business contracts, scripts, and templates. Shared entry points do not hard-code customers, column counts, brand categories, or output sheets.
2. **Thin orchestration, script execution:** the skill selects projects, interprets changes, and synthesizes findings. Existing Python scripts handle stable calculations and layout without being rewritten each period.
3. **Inspectable stage outputs and resumption:** stages declare output files; runs preserve arguments, fingerprints, logs, and state. Nonzero exits or missing outputs cannot count as completion.

## Selection and initialization

Run from the skill root using Python with the required dependencies:

```bash
.venv/bin/python scripts/project_manager.py list
.venv/bin/python scripts/project_manager.py init monthly-sales
.venv/bin/python scripts/project_manager.py validate --project projects/monthly-sales/project.yaml
```

Initialization creates candidate YAML only, not a subskill or fictional business implementation. Existing directories with the same name are not overwritten. For ambiguous requests, inspect the configuration's business contract before clarifying choices that affect definitions. Similar customer names do not justify sharing rules.

### Executable quickstart

For additive metrics in a single table at period × entity grain, write a real brief following `config/periodic-brief.example.json`, then run:

```bash
.venv/bin/python scripts/onboard_project.py --brief /path/to/brief.json
.venv/bin/python scripts/project_manager.py run --project projects/<project-id>/project.yaml --inputs /path/to/inputs.json --cache-dir workspace/cache
```

Input JSON needs only a `data` file path and `period`. The brief specifies ordered `periods`, complete `entities`, mappings, units/directions, and required questions. CSV and a specified XLSX/XLSM sheet are supported, with a single header row and one row per period/entity. The script creates a real three-stage pipeline, a fixed engine version, and a project brief, producing HTML, Markdown, answers, row-level lineage, and `delivery.json`. No separate calculation script is needed. `init` remains available for custom adapters.

Supported questions cover totals/growth, contributions from every entity, counter-trend entities, and offsets when the total is unchanged. Only explicit `sum` aggregation is supported. Formula cells, duplicate grain, missing entities in selected periods, nonfinite values, unknown entities, and unsupported question types fail rather than silently becoming zero. Growth is not calculated for nonpositive baselines. Rows outside selected periods are excluded and counted.

`ready_within_scope` means the brief's descriptive questions and artifact-binding checks passed. It does not certify causality, forecasting, or arbitrary business analysis. If the task requires those capabilities, extend project adapters and evidence inputs; do not rewrite the task as descriptive and claim completion. HTML structure checks do not replace visual inspection. Initialization refuses overwrites; upgrades explicitly migrate versions.

## Configuration protocol v1

This is a format example, not an implemented business pipeline. Scripts and templates must actually exist before validation/execution:

```yaml
schema_version: 1
project_id: monthly-sales
version: "0.1.0"
status: candidate
inputs:
  data: file
  period: string
  template: file
resources:
  - references/data-contract.md
  - references/analysis-rules.md
  - references/visual-spec.md
pipeline:
  - id: compute
    script: scripts/compute.py
    args: ["--data", "{input:data}", "--period", "{input:period}", "--out", "{run_dir}/evidence.json"]
    outputs: [evidence.json]
    checkpoint: true
    timeout_seconds: 600
  - id: render
    script: scripts/render.py
    args: ["--evidence", "{run_dir}/evidence.json", "--narrative", "{run_dir}/narrative-draft.json", "--template", "{input:template}", "--out", "{run_dir}/report.pptx"]
    outputs: [report.pptx, narrative.json]
```

At the checkpoint, the host writes `narrative-draft.json`. `render` validates it and generates final `narrative.json` itself. Do not prewrite a stage's declared output. Narrative validation checks claim IDs, numbers, limitations, and counterevidence. File existence is only an engineering check, not semantic acceptance.

Inputs support `file` (content hash) and `string` (complete value) only; JSON keys must match configuration. Relative input paths resolve from the input JSON directory. List result-affecting rules, templates, imported project modules, and other dependencies individually in `resources`, not just directories. Project stage scripts, shared scripts, and dependency manifests are fingerprinted. Projects still record system fonts, third-party packages, external API environments, and versions; the manager does not encapsulate the complete environment.

Scripts/resources resolve within the project directory and cannot escape it. Outputs resolve within the current run directory and cannot overlap or occupy manager state/log paths. Arguments support `{input:name}`, `{run_dir}`, `{project_dir}`, and `{project_config}`. Scripts run with the current Python interpreter, argument arrays, and isolated working directories, without a shell. Configured scripts must be reviewed local code; this runner is not an untrusted-code sandbox.

## Periodic execution and resumption

Save current inputs as JSON, for example `{"data":"sales.xlsx","period":"2026-10","template":"report.pptx"}`, then run:

```bash
.venv/bin/python scripts/project_manager.py run --project projects/monthly-sales/project.yaml --inputs /path/to/inputs.json
.venv/bin/python scripts/project_manager.py resume --run-dir /path/to/run --acknowledge compute
```

`run` prints the actual directory, using UTC time and a random ID so same-day runs do not merge or overwrite. Inspect `run_state.json` and project acceptance artifacts afterward; an exit code alone does not prove visual/business acceptance. Trial runs do not automatically promote candidate status.

Only `checkpoint: true` pauses execution; other stages run continuously. At checkpoints, the host can read evidence, write a narrative draft, and explicitly acknowledge the stage. Acknowledgment does not automatically establish business quality. Original dates, templates, and arguments are restored from state rather than defaults. Do not alter completed files. Use a new filename for supplemental drafts, then validate/freeze them as downstream outputs.

Resumption verifies original files, configuration, code, declared resources, interpreter, and completed-output fingerprints. Changes require a new run. Failed stages without partial outputs may retry; unverified partial outputs require a new run rather than deleting user files or treating partials as cache. Each run has an exclusive lock. After forced termination, manually remove `.lock` only after confirming no writer remains. Do not modify dependencies during execution. External side effects and background processes launched by scripts are not transactionally managed.

Within-run resumption is conservative. Cross-run reuse is enabled explicitly with `--cache-dir`; quality stages cannot be cached. See [versions, feedback, and cache](project-lifecycle.en.md) and [performance procedures](execution-performance.en.md).

## Accumulating improvements

- Keep current facts, failures, manual edits, and new hypotheses in run directories. Unverified suggestions do not become next-period rules.
- Put repeated, evidenced improvements into the relevant project's rules, configuration, code, or templates. Increment its version and record source runs, scope, and regressions. Routine new periods do not automatically upgrade rules.
- Old runs retain configuration snapshots, fingerprints, and outputs, not complete code backups. Reproducible history requires a version-control commit or project archive and environment manifest; hashes cannot restore old code.
- Promote shared improvements only after cross-project evidence and regression. Customer fields, thresholds, and styles remain project-local; projects must not read one another's private assets.
- Keep the entry point generic. List projects, then load only the selected configuration and relevant rules; do not append all run history or customer reports to `SKILL.md`.
