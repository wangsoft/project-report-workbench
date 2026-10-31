# UK Regional Electricity Demonstration

[简体中文](project-spec.md) | English

## Scope and sources

DESNZ Energy Trends regional electricity: the 2024 release (data through 2023) supplies rule/visual learning; the 2025 release (through 2024) supports cross-period replay. Originals, download URLs, and SHA-256 records remain in `workspace/public-fixtures/uk-electricity/source-manifest.json`, outside the shared skill package. Official aggregate tables are not plant-level records. Both releases' summaries were seen during retrieval, so this is not blind testing and establishes neither generalization nor superiority to analysts.

0.2.0 is a four-page factual template. 0.3.0 expands 2024 data into a fifteen-page full-topic candidate, checked against the twelve-page official report: generation, consumption, trade, fuels, low carbon, renewable technologies, external context, revisions, and two appendices. Topic coverage does not establish sentence-level reproduction, independent verification of every causal explanation, or human business acceptance. See `coverage.json`.

## Data and analytical rules

- Source units: GWh; displayed units: TWh. Low carbon = nuclear + renewables; other fuels/storage are excluded.
- Locate values by year + region headers and metric names, not fixed rows/latest columns. Totals remain identifiable when a new release adds Low Carbon rows.
- Use explicit All generating companies rows only; do not add components and subtotals together. Stop for missing, textual, nonfinite, or uncached required values. Historical battery-storage gaps remain null; trade can be signed net flows.
- Year-over-year comparisons use current/previous values from the same release, not an older-release baseline. Same-year differences across releases are reported separately as revisions.
- Use the latest five years. Earlier cross-table conflicts remain in quality artifacts, outside report analysis. Disclose in-window differences above 0.001 GWh; block above 0.01 GWh. The latter is a display-materiality choice for this descriptive report (10 MWh, 1,000 times smaller than displayed 0.01 TWh), not proof of the cause. Regional-sum tolerance is 0.05 GWh because some components have only two decimals.
- `full_data` reads coal, oil, gas, renewable technologies, and supply/demand components. Historical extremes use the same fuel-table source series from 2004 onward; earlier cross-table conflicts are not thereby resolved.
- Retain discrepancies between 2020 fossil components/totals and 2024 supply-demand versus public/autogenerator consumption. Correct calculations do not prove source conservation. Northern Ireland's negative 2020 residual is a difference, not negative storage.
- External `context.json` binds DUKES literature and map SHA-256 by year. Historical policy context has source links. Attribute explanations to external literature; no independent causal model was built. Each new period must update context/coverage contracts instead of silently reusing old explanations.

## Visual learning and adaptation

References: summary hierarchy on page 1 and energy stacked bars on page 2 of the 2024 PDF. Use white backgrounds, portrait A4, categorical blues, and footer dividers. Colors are approximate reconstructions from rendered observation, not exact theme extraction. Fossil fuels use purple-blue, nuclear dark blue, renewables light blue; gray other/storage completes totals. Chinese STSong-Light replaces the original English font. Remove government signatures/logos and label workbench trial output to avoid official misidentification. Render and inspect every final PDF page.

New pages: summary, regional trends, consumption, trade ledger, fuels/history, low carbon, two regional-fuel pages, renewable trends, technology comparison, context, source differences, power-station map, policy history, and coverage index. Chart 2 becomes a comparison table; Appendix A becomes a flow ledger with residuals instead of forcing a balanced Sankey. Appendix B cites an independent DUKES 2025 map with required attribution, not a map derived from aggregates. Charts share `evidence.json`; page numbers, units, and evidence IDs are checkable. The template is bounded to five regions/five years, not arbitrary category counts. Overcapacity paragraphs fail rather than shrinking away content.

## SOP and acceptance

normalize → compute → check → render → verify. The first two perform stable calculations. `check` verifies source tables, formulas, units/periods, claim references, trends, and revisions. `verify` checks PDF values, page counts, bounds, and hashes. Automated checks and page-level visual records remain separate; human business review remains pending.

The baseline input is older-release normalized JSON containing values and locations, not official prose. It is a controlled, hashed input; maintainers must review lineage to the original workbook. The runner does not download or trace external sources automatically.

On failure, retain logs. Changes to inputs/scripts require a new run. Use shared `project_versions.py` for review, improvements, and releases. Do not generalize project rules or source discrepancies directly to other customers.

0.3.0 uses `2025-release/full-inputs.json` with additional `context`, `context_source`, and `map` inputs. Original `inputs.json` serves older archives. Cache timings exclude external retrieval, manual source preparation, and visual review. Differences between official prose and Excel, including five-year gas changes, remain in separate comparison records; do not alter formulas to match prose.
