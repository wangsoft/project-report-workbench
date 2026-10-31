# 2022 Cross-Period Evaluation and Comparison Status

[简体中文](cross-period-review-2022.md) | English

Date: 2026-10-31. Status: the user supplied the target regional report; page-by-page reading, chart inspection, and comparison with frozen output are complete. Full content-equivalence acceptance did not pass. The working directory was a 0.4.0 candidate; active release remained 0.3.0.

## Generated results

Using DESNZ's 2023 regional Excel release through 2022, the prior release as revision baseline, and contemporaneous DUKES 2023 context, the report has fifteen pages. It passed 745 calculation/source checks, 40 shared tests, and 38 project tests. Every page was rendered and inspected. Finally changed pages 6, 12, and 15 were rechecked; the remaining twelve were pixel-identical to previously inspected versions. Visual review by the generating agent is not independent business acceptance.

UK generation: 325.26 TWh, +5.29% year over year. Renewables added 12.82 TWh, contributing 4.15 percentage points to generation growth. Trade shifted from 24.58 TWh net imports to 5.34 TWh net exports. Nuclear generation rose while its share fell; the report distinguishes those directions.

Corrections addressed missing historical storage rows, renamed own-use rows, import/export wording, fixed years, map dates, and contamination by future policy context. Missing storage remains null, not zero. Small 2021 cross-sheet differences are accepted only for explicit source SHA and exact difference lists, still disclosed, without generally loosening thresholds.

## Comparison results and limits

See the [2024 review](analyst-review-2024.en.md): numerical traceability is relatively strong, but priority selection, regional explanation, and business readability remain weaker than the official report.

The 2022 output was frozen before reading the target regional PDF at `2026-10-31T09:31:59Z`; its hash was reverified unchanged. Later reports had already exposed historical data, so this is retrospective testing with delayed target reveal, not a strict time-blind test.

Earlier PDF downloads repeatedly failed with `SSL_ERROR_SYSCALL` / TLS EOF. The user then supplied a local file, stored in the sample directory with `reference-reveal.json`. Frozen hashes were verified before and after reading. All twelve official pages, charts, and appendices were read/rendered. Of 33 preregistered metrics, 25 have explicit official values and all match within displayed precision; 8 are unstated, recorded as such rather than passed. This is neither overall report accuracy nor proof of analytical completeness.

## Formal target comparison

Details are in frozen-run `target-reference-evaluation.json`; the checker is this directory's `evaluate_2022_reference.py`. Official values were transcribed manually and compared with frozen `evidence.json`, using half a unit of the last displayed digit as tolerance. Exploratory checks remain separate from preregistered results.

| Preregistered dimension | Official/generated evidence | Conclusion |
| --- | --- | --- |
| Total direction and magnitude | Official page 1: 325 TWh, +5.3%; generated page 1: 325.26, +5.29%. Renewable record on generated page 5, not emphasized in summary | Numerical agreement; partial summary-priority coverage |
| Trade reversal and regional direction | Official pages 1/3 explain French nuclear outages and UK net exports; generated pages 1/4/11 contain this narrative and regional net flows | Main story covered; ledger is not flow-diagram equivalence |
| Regional ranking and exceptions | Official pages 1/4 highlight Scotland nuclear -45%, England +27%; frozen evidence supports it, but body does not juxtapose it | Important analytical omission; available data is not reported analysis |
| Renewable drivers and counterexamples | Generated page 10 has regional technology growth; page 11 weather/outages. Missing Moray East, Hornsea 2, sunshine +21%, rainfall +12% | Partial coverage, explanations insufficiently specific |
| Nuclear capacity and output | Generated pages 6/11 distinguish output, share, closures, utilization; incomplete regional narrative | Core concepts covered, regional explanation lacking |
| Claims and sources | Main values pass; demand/consumption distinguished. Official body/appendix differences appear below | Strong traceability; unresolved source conflicts |
| Charts and appendices | Charts 1/4/5 broadly match topics; Chart 2 becomes generation/consumption table; Chart 3 low-carbon curve; Appendix A ledger; Appendix B independent same-period annual-report map | Full functional coverage not achieved |
| Clarity and next steps | Generated fifteen pages with substantial audit detail; official eight-page main body prioritizes findings | Analytical working paper requiring editing, not analyst final copy |

### Two substantive coverage gaps

1. **Chart 3 uses a different metric.** Official page 5 plots renewable share for 2018–2022; generated page 6 plots low-carbon share, listing only current renewable share in a table. It is clearly labeled, so this is not mislabeling, but official Chart 3 is not covered.
2. **Chart 2 supply is not generation.** Official page 3 Chart A shows supply shares: England 72.5%, Scotland 15.6%, Wales 8.8%. Generated page 3 uses generation shares 72.23%, 15.46%, 9.14%. Official page 2 generation shares agree with our calculations. Verify the supply denominator/deductions before building corresponding charts; do not adjust values just to match. Four-region statements that local generation exceeds listed consumption do not replace official supply-role judgments.

### Source conflicts and definition diagnosis

| Item | Official target | Frozen output/Excel | Judgment |
| --- | --- | --- | --- |
| England gas year-over-year | Page 1: -0.5%; page 4: -4.6% | -0.4551%, generated -0.46% | Official passages contradict; Excel supports page 1, not copying page 4 |
| Northern Ireland consumption | Appendix A page 10: 8,205 GWh | 8,214.8607 GWh | Gap 9.8607 GWh exceeds integer rounding; retain chart/table discrepancy, cause unknown |
| UK consumption year-over-year | Regional page 1: -4.5%; earlier DUKES: -4.3% | -4.5347% | Matches regional target; DUKES discrepancy is not established as a calculation error or version difference |
| Chart 2A shares | Supply shares | Generation shares | Definition diagnosis, excluded from accuracy scoring |

Official page 1 summary says “highest since 2019,” while its body says “since 2018”; the page 2 nuclear paragraph labels the comparison year 2021. Preserve context for these inconsistencies. Do not edit official documents or count them as generated-report quality gains.

### Color and layout comparison

Both reports use blues and clear page numbers. Official pages organize the story with dark-blue titles, pale-blue highlight boxes, and compact sans-serif text. Generated output uses fine Chinese serif text, pale table headers, and more whitespace: restrained, but body contrast and summary hierarchy are weaker. Horizontal bars help reading, but Chart 4 provides only a current-share table rather than annual in-bar percentage labels. Ledgers help lookup but communicate cross-region flows less directly. No occlusion was found; absence of overlap does not establish official-level information design.

### Acceptance decision

**Numbers are reproducible and cross-period adaptation works; complete analytical coverage and final-copy quality do not yet pass.** Keep the frozen output unchanged; do not revise it after seeing answers in this round. Next priorities: Chart 2/3 contracts, regional nuclear and specific capacity/weather explanations, and moving audit material into appendices. Do not expand the method library or add agents. Issues were logged as unresolved feedback; the active release was not upgraded.

Supplementary contemporaneous checks used downloaded DUKES 2023 pages 28–33. Of 29 selected values, 28 match displayed precision. The unmatched value is final-consumption growth: regional Excel -4.53%, DUKES -4.3%. Preserve the discrepancy; revisions versus statistical definitions remain unresolved. Total demand cannot substitute for final consumption. Tolerances remain half the last displayed unit, not relaxed to fit.

DUKES was also a context input and these checks were selected after generation. **28/29 is neither independent validation nor the target regional report's match rate.** DUKES also analyzes domestic-sector demand, interconnectors, station operations, and capacity utilization more specifically; generated output contains only partial context/net values and does not cover everything.

## Files

Paths relative to the workbench root:

- New report: `workspace/uk-electricity/20261031T093157-27160d72f692/report.pdf`
- Supplemental values: `supplementary-dukes-comparison.json` in that run
- Visual review: `visual-review.json` in that run
- Freeze: `workspace/public-fixtures/uk-electricity/2023-release/generation-freeze.json`
- Contemporaneous annual report: `workspace/public-fixtures/uk-electricity/context-2022/dukes-2023.pdf`
- Target: `workspace/public-fixtures/uk-electricity/2023-release/reference.pdf`; original [government file](https://assets.publishing.service.gov.uk/media/6581b267fc07f300128d44b9/Electricity_generation_and_supply_in_Scotland__Wales__Northern_Ireland__and_England__2018_to_2022.pdf)

Replay:

```bash
.venv/bin/python scripts/project_manager.py run --project projects/uk-electricity/project.yaml --inputs workspace/public-fixtures/uk-electricity/2023-release/inputs-v0.4.json --cache-dir workspace/cache
```

Verification: `.venv/bin/python projects/uk-electricity/evals/evaluate_2022_reference.py`. The numeric comparison executed successfully, all 33 registrations remain, and the frozen hash is unchanged. The same agent reviewed this work; it is not an independent analyst blind review or proof of matching/exceeding analyst quality.
