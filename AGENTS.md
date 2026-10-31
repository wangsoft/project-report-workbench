# Repository Guidelines

English | [简体中文](AGENTS.zh-CN.md)

## Project Structure & Module Organization

This Python 3.10+ workbench builds evidence-backed periodic reports. Shared pipeline, caching, onboarding, and evaluation tools live in `scripts/`; generic tests live in `tests/`. Each `projects/<project-id>/` contains `project.yaml` and project-specific scripts, references, templates, tests, and evaluation records. Shared procedures live in `references/`, dependencies in `config/requirements.txt`, and agent entry instructions in `SKILL.md`. `workspace/` holds inputs and generated runs; `releases/` holds frozen versions. Keep business-specific logic within its project.

## Build, Test, and Development Commands

Run commands from the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r config/requirements.txt
.venv/bin/python scripts/project_manager.py --help
.venv/bin/python -m unittest discover -s tests -v
```

The first two commands prepare the environment; the others list CLI operations and run shared tests. There is no separate compilation step.

Validate a project configuration:

```bash
.venv/bin/python scripts/project_manager.py validate --project projects/electricity-quickstart/project.yaml
```

Run the prepared quickstart:

```bash
.venv/bin/python scripts/project_manager.py run --project projects/electricity-quickstart/project.yaml --inputs workspace/onboarding-validation/inputs.json --cache-dir workspace/cache
```

Install project-specific requirements before running its reports or tests.

## Coding Style & Naming Conventions

Use four-space Python indentation, `snake_case` functions and modules, and descriptive names. Match neighboring code; no repository-wide formatter or linter configuration is provided. Project and stage identifiers must match `[a-z][a-z0-9_-]*`. Declare pipeline outputs and cache dependencies explicitly in `project.yaml`. Keep configuration paths relative and preserve input fingerprints and source evidence.

## Testing Guidelines

Use standard-library `unittest`, naming files `test_*.py` and methods `test_*`. Reproduce bugs and identify their cause before changing code. Add regression checks for changed behavior, using temporary directories for isolated runner tests. Run affected project suites with `-m unittest discover -s projects/<project-id>/tests -v`. No numeric coverage threshold is configured. Report changes also require numerical, evidence, and visual checks; command success alone does not establish report quality. Claim success only with fresh verification evidence.

## Commit & Pull Request Guidelines

Use concise imperative subjects describing the change; existing history uses prefixes such as `docs:` and `ci:`. PR descriptions should explain the problem, affected projects, validation commands and results, and remaining limitations. Link relevant issues and include rendered examples for report-layout changes.

## Data & Configuration Safety

Exclude customer data and generated runs from shared distributions. Preserve frozen releases; evolve candidate project assets and validate before promotion. Never use a proxy for `ess-repos01.wisers.com:9980` or `gitlab.wisers.com`.
