# Project Report Workbench

English | [简体中文](README.zh-CN.md)

Turn historical data, analytical methods, and report templates into reusable workflows for evidence-backed periodic reports.

## What it does

- Builds project-specific pipelines from CSV/XLSX data and reporting requirements.
- Reuses calculation scripts, analytical rules, and report templates across periods.
- Tracks sources, run logs, checkpoints, and cached outputs.
- Validates improvements before promoting project versions.

Scripts handle repeatable processing; an AI agent handles interpretation and exceptions using the [English skill guide](SKILL.en.md). Complex analysis and report formats require project-specific adapters.

## Quick start

Requires Python 3.10+. Run from the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r config/requirements.txt
.venv/bin/python scripts/project_manager.py --help
```

Ask your agent to follow `SKILL.md` with your data, reporting goals, and historical reports. For supported periodic tables, adapt the [example brief](config/periodic-brief.example.json), then run:

```bash
.venv/bin/python scripts/onboard_project.py --brief /path/to/brief.json
```

For custom pipelines, start with an empty project configuration:

```bash
.venv/bin/python scripts/project_manager.py init monthly-sales
```

Add the project's scripts, rules, and templates before running it. See the [project workflow](references/project-workflow.en.md) for configuration and execution details.

## Repository layout

| Directory | Contents |
| --- | --- |
| `scripts/` | Shared pipeline and analysis tools |
| `projects/` | Project configurations, scripts, templates, and tests |
| `references/` | Analysis, reporting, and validation procedures |
| `tests/` | Shared tool and runner tests |
| `releases/` | Frozen project versions |
| `workspace/` | Local inputs and generated outputs (excluded from Git) |

Example projects cover UK electricity and synthetic retail reporting. Their input datasets must be prepared separately.

## Testing

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Report delivery also requires numerical, source-evidence, and visual validation.

## CI and releases

GitHub Actions runs shared tests on Python 3.10, 3.12, and 3.14 for pull requests and pushes to `main`. After tests pass on `main`, an unpublished `VERSION` is released with source archives and SHA-256 checksums. Existing published versions are left unchanged.

To publish a new version, update `VERSION`, add `release-notes/v<VERSION>.md`, and merge to `main`. Retry interrupted releases with **Re-run failed jobs** on the original Actions run. **Run workflow** on `main` can also trigger validation and publication. Publishing uses the built-in `GITHUB_TOKEN`; no personal token is required. Example project versions are independent of the repository version.

## Documentation

Current guides are available in English and Simplified Chinese. Each guide links to its counterpart. Frozen archives under `releases/` retain their original documents; machine-readable configuration and evaluation records keep their original values.

| Guide | English | 简体中文 |
| --- | --- | --- |
| Detailed overview | [English](README.detailed.en.md) | [中文](README.zh-CN.md) |
| Agent workflow | [English](SKILL.en.md) | [中文](SKILL.md) |
| Project configuration | [English](references/project-workflow.en.md) | [中文](references/project-workflow.md) |
| Versions, feedback, and learning | [English](references/project-lifecycle.en.md) | [中文](references/project-lifecycle.md) |
| Data processing | [English](references/data-processing.en.md) | [中文](references/data-processing.md) |
| Metrics, evidence, and assumptions | [English](references/contracts.en.md) | [中文](references/contracts.md) |
| Method selection | [English](references/methods.en.md) | [中文](references/methods.md) |
| Analysis and narrative | [English](references/analysis-synthesis.en.md) | [中文](references/analysis-synthesis.md) |
| Report reconstruction | [English](references/report-workflow.en.md) | [中文](references/report-workflow.md) |
| Visual specifications and templates | [English](references/visual-reverse-engineering.en.md) | [中文](references/visual-reverse-engineering.md) |
| Execution and performance | [English](references/execution-performance.en.md) | [中文](references/execution-performance.md) |
| Deliverables | [English](references/deliverables.en.md) | [中文](references/deliverables.md) |
| Evaluation | [English](references/evaluation.en.md) | [中文](references/evaluation.md) |
| Sources and adaptations | [English](references/sources.en.md) | [中文](references/sources.md) |
| UK electricity specification | [English](projects/uk-electricity/references/project-spec.en.md) | [中文](projects/uk-electricity/references/project-spec.md) |
| 2024 report review | [English](projects/uk-electricity/evals/analyst-review-2024.en.md) | [中文](projects/uk-electricity/evals/analyst-review-2024.md) |
| 2022 cross-period review | [English](projects/uk-electricity/evals/cross-period-review-2022.en.md) | [中文](projects/uk-electricity/evals/cross-period-review-2022.md) |
| Contributor guide | [English](AGENTS.md) | [中文](AGENTS.zh-CN.md) |
| v0.1.0 release notes | [English](release-notes/v0.1.0.md) | [中文](release-notes/v0.1.0.zh-CN.md) |

Keep both language versions synchronized when updating documentation. Executable commands, configuration keys, metric IDs, and recorded results must retain the same meaning in both versions.
