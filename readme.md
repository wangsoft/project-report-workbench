# Project Report Workbench

English | [简体中文](README.zh-CN.md)

Turn historical data, analytical methods, and report templates into reusable workflows for evidence-backed periodic reports.

## What it does

- Builds project-specific pipelines from CSV/XLSX data and reporting requirements.
- Reuses calculation scripts, analytical rules, and report templates across periods.
- Tracks sources, run logs, checkpoints, and cached outputs.
- Validates improvements before promoting project versions.

Scripts handle repeatable processing; an AI agent handles interpretation and exceptions using [SKILL.md](SKILL.md). Complex analysis and report formats require project-specific adapters.

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

Add the project's scripts, rules, and templates before running it. See the [project workflow](references/project-workflow.md) for configuration and execution details.

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

- [Detailed overview in Chinese](README.zh-CN.md)
- [Project configuration and workflow](references/project-workflow.md)
- [Versioning, feedback, and learning](references/project-lifecycle.md)
- [Evaluation procedures](references/evaluation.md)
- [Contributor guide](AGENTS.md)

Most detailed documentation is currently in Chinese.
