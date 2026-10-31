# Sources, Adaptations, and Exclusions

[简体中文](sources.md) | English

Checked: 2026-10-31. These records explain sources and design decisions; third-party examples are not treated as validated business rules.

## SenseNova

Repository: [OpenSenseNova/SenseNova-Skills](https://github.com/OpenSenseNova/SenseNova-Skills), inspected commit `95db9cf340f0efad2945c3b79f4fc7d7a5d474fd`.

Read:

- [sn-da-excel-workflow](https://github.com/OpenSenseNova/SenseNova-Skills/blob/95db9cf340f0efad2945c3b79f4fc7d7a5d474fd/skills/sn-da-excel-workflow/SKILL.md)
- [sn-da-large-file-analysis](https://github.com/OpenSenseNova/SenseNova-Skills/blob/95db9cf340f0efad2945c3b79f4fc7d7a5d474fd/skills/sn-da-large-file-analysis/SKILL.md)
- The same workflow version's `capability/excel-data-cleaning/numeric-format-normalization/SKILL.md` and `capability/excel-reading/single-sheet-reading/SKILL.md`.

| Borrowed idea | Adaptation here |
| --- | --- |
| Profile first, multiple sheets, selective loading | Bounded samples first; dimensions are hints; full scans only when needed, retaining row locators |
| Streaming large files and Parquet cache | Decide by width, memory, repeated reads; explicit schemas, content hashes, atomic writes |
| Reconcile totals after cleaning | Add quarantine records, join cardinality, grain, and cross-period definitions |
| Vectorization and large exports | Keep the principle without banning reasonable iteration; respect host/format limits |
| Charts and delivery | Generate from validated metrics and verify actual fonts/rendering |

Not adopted: fixed 10k/100k cutoffs; all-string analytical types; deleting non-Chinese/nonnumeric characters; float32 money by default; cache reuse based on existence alone; fixed server fonts or `/mnt/data` links; large lists of dependent subskills.

Helper scripts were independently implemented. The source project is MIT-licensed; its notice is retained in [sense-nova-license.txt](sense-nova-license.txt).

## Skill Training

Consulted the local `skill-training` reconstruction → comparison → rule-revision approach at commit `5a72d0ec26ee4207f153935000e0b193137f6f53`, especially `prompts/backward.md`, `prompts/loss.md`, and `skilltrain/workflows/s2_forward.py`.

Here, real data is the input, with deterministic calculations, evidence chains, cross-period checks, and a methodology baseline. No implementation or prompts were copied. Scriptwriting experiment results were not extrapolated to analytical reporting.

## Selected ideas from data-analysis-skill

Inspected [dongzhang84/data-analysis-skill](https://github.com/dongzhang84/data-analysis-skill), commit `1c2d806bb282f343d9143e2766faaeb3381f1584`: the `.claude/skills/data-analysis/` entry point, `references/workflows.md`, `domain-knowledge.md`, style/HTML component references, and three helpers.

Three ideas were rewritten into [multi-perspective analysis and narrative](analysis-synthesis.en.md):

- Choose perspectives by question and execute sequentially, without fixed expert counts, assumed institutional identities, or extra approval stages.
- Add evidence IDs, deduplication, counterevidence, scope alignment, and conflict states. Different perspectives are not independent evidence.
- Make narrative components format-independent content contracts bound to existing visual specifications; no HTML/CSS or code was copied.

Not adopted: domain formulas/thresholds, random institutional styles, mandatory multi-agent execution, automatic dependency installation, or whole-page screenshot PPTX output. Example reports and promotional claims are not validation. The project is not a runtime dependency.

## Selected ideas from data-analytics-skills

Source: [nimrodfisher/data-analytics-skills](https://github.com/nimrodfisher/data-analytics-skills). Raw `main` files were inspected without a verifiable commit ID; no fixed revision is claimed. Read `02-documentation-knowledge/` semantic-model-builder, metric-reconciliation, analysis-assumptions-log, associated definition frameworks, reconciliation references, and assumption scripts; also examined root-cause, impact-estimation, and context-packaging procedures.

Metric semantics, stepwise reconciliation, and assumption lifecycles were independently rewritten into [contracts](contracts.en.md). No upstream code/templates were copied or runtime dependencies added. Added aggregability, historically available definitions, residual reconciliation, refuted/recheck states, and downstream impact propagation.

Not adopted: universal tolerance tables, fixed standard-deviation stopping rules, preset multipliers presented as confidence intervals, or implicit upstream modification. Minimal `--help` runs of upstream `assumptions_tracker.py` and `drilldown_analyzer.py` produced demonstrations rather than help, so their CLIs were not reused. This is an agent procedure, not a completed automated semantic platform or invalidation engine.

## Original technical and methodological references

- [openpyxl optimized modes](https://openpyxl.readthedocs.io/en/stable/optimized.html): read-only/write-only modes and unreliable worksheet dimensions.
- [NIST EDA](https://www.itl.nist.gov/div898/handbook/eda/section1/eda11.htm): exploring structure, anomalies, and assumptions.
- [NIST time-series introduction](https://www.itl.nist.gov/div898/handbook/pmc/section4/pmc4.htm): trend, seasonality, autocorrelation.

Methods still require suitable inputs. These sources do not certify this skill's business results.

## Further adaptation from skill-training

Sources in local `../skill-training`: `README.zh-CN.md`, `prompts/backward.md`, `prompts/memory_policy.md`, `workflows/s2_forward.py`, `s4_backward.py`, and `s5_train.py`. Adapted reconstruction/comparison, attribution informed by reading traces, cross-sample abstraction, reinforcement/correction/creation/merging of experience, snapshots, and recovery. Independently written `experience_memory.py` and `experience_loop.py` adapt those mechanisms to reporting; upstream source/prompts were not copied and are not runtime dependencies.

Upstream specifies PolyForm Noncommercial 1.0.0. Only mechanisms were used as inspiration, not upstream code introduced as an unrestricted commercial dependency. Its scriptwriting results are not evidence for this workbench. Comparison that ignores layout is unsuitable for reports: visual acceptance remains required, complemented by independent numerical/report assertions and regression gates because format checks alone do not establish quality.
