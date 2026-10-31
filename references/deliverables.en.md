# One Skill, Multiple Projects, Separate Run Records

[简体中文](deliverables.md) | English

Do not generate another `SKILL.md`. Keep shared methods and the execution entry point in this skill, business differences in projects, and current-period facts in run directories.

```text
project-report-workbench/
  SKILL.md
  scripts/                     # Shared management, profiling, calculations, timing
  references/                  # Shared procedures
  projects/<project-id>/
    project.yaml               # Identity, version, inputs, resources, stages
    references/
      data-contract.md
      analysis-rules.md
      report-spec.md
      visual-spec.md           # When visual reports are required
      sop.md
    scripts/                   # Business calculations, validation, rendering
    templates/                 # Clean templates and authorized brand assets
    tests/                     # Business regression with fixed expectations
    evals/                     # Version evaluation and validated scope
  workspace/<project-id>/<run-id>/
    run_state.json             # Original arguments, config snapshot, fingerprints, status, timing
    logs/
    ...                        # Declared metrics, evidence, narrative, reports, acceptance outputs
```

Create only needed files; do not fill directories with empty scripts. `init` creates candidate configuration only. Without business samples, do not claim the pipeline is usable. See [project configuration and workflow](project-workflow.en.md).

Project contracts fix metric semantics, versions, join grain, and sources. Analysis rules fix methods, triggers, exceptions, assumption rechecks, and conflict handling. SOPs describe inputs, actions, outputs, checks, and failure handling while referencing the same rule IDs, not duplicating algorithms. Narrative components reference claim and metric IDs. Keep actual question coverage, reconciliations, assumption evidence, and invalidation impact lists in the run directory.

For PDF/PPTX, follow [visual procedures](visual-reverse-engineering.en.md) to retain specifications, template provenance, color semantics, fonts, capacities, and overflow handling. Remove old conclusions, notes, chart caches, and embedded data. Without a source, label the design as a new candidate. Brand assets belong only to the authorized project, not shared assets.

Prefer scripts for calculations, cleaning, charting, filling templates, and checks. The skill selects configuration, executes stages, performs necessary model synthesis, and handles exceptions. See [execution and performance](execution-performance.en.md). Provide working invocation examples, dependencies, and actual test results; label untested performance or visual behavior. A project's `validated` label does not replace versioned, sample-scoped acceptance evidence.

Store raw data, reference reports, page extracts, current facts, and logs in authorized run or external data directories, not distributable shared skill content. Configuration/templates may also contain customer information. Share only common files and synthetic tests by default; export project assets separately as authorized. Local storage does not automatically install or publish anything.
