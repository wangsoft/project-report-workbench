# Review Against the 2024 Reference Report

[简体中文](analyst-review-2024.md) | English

This review compares the fifteen-page 0.3.0 output with DESNZ's twelve-page regional electricity report released in 2025. The reviewer was the generating agent, not an independent analyst, and the review was not blind.

Conclusion: the generated report is a traceable analytical working paper, but not yet a replacement for the official analyst report. The main gaps concern selecting and organizing explanations, not execution speed.

## Findings

| Dimension | Evidence and gap | Judgment and handling |
| --- | --- | --- |
| Numbers | 61 of 63 selected official values match. UK gas change, 2020–2024: Excel gives -22.54%, prose -29%. England coal year-over-year: recalculated -38.48%, prose -39% | 61/63 is not overall numerical accuracy. Preserve discrepancies; official-prose error versus version/definition differences remains unresolved |
| Summary | Official page 1 highlights minimum generation, renewables first exceeding half, low-carbon and import records. Generated page 1 mainly lists totals; some records appear only as yes/no on page 5 | Important findings lack priority. 0.4.0 adds contribution ranking and trade reversals; full record-focused narrative still needs improvement |
| Causal explanation | Official prose connects prices, nuclear outages, capacity, and weather with corresponding changes. Generated page 11 groups independent literature with weak links to each page's numbers | Verifiable context helps, but complete citations do not ensure strong explanation. Summary now links trade changes with contemporaneous context, without estimating causal contributions |
| Regional differences | Five-year mix, regional growth, and technology concentration are recalculated, but reasons for differences are underexplained | Statistical comparisons are usable; operational mechanisms need region/plant evidence linked to specific changes |
| Charts | Charts 1/4/5 redrawn by scripts; Chart 2 replaced by a table; Appendix A by a residual ledger; Appendix B by an independent annual-report map | Functional coverage is not chart equivalence. Ledger aids audit but lacks the official flow diagram's immediacy; map was not reconstructed from plant data |
| Source differences | Page 12 discloses fuel-component and supply-demand residuals instead of forcing balance | Retain them, distinguishing source errors, definitions, and limits of the workbench's balance formula; do not blame every residual on source tables |
| Reader experience | Official report is compact; the fifteen-page output contains many checks, limitations, and input-file details | Still resembles engineering acceptance output. Simplify business narrative and move technical ledgers to appendices. This round made necessary corrections, not a claimed editorial final |
| Cross-period ability | 0.3.0 hard-coded DUKES 2025, map dates, specific 2020 differences, and some regional supply-demand judgments | Previously only a single-year candidate was verified. 0.4.0 uses metadata, data conditions, explicit-year context, and older Excel mappings |

## Acceptance criteria for this iteration

1. A new year calculates comparisons from the same release, without mixing later historical revisions.
2. Net import/export reversals, generation direction, and regional supply/demand roles follow the data.
3. Unavailable fields remain missing; absence of historical battery rows does not mean zero generation.
4. Target references stay outside generation until freezing; predefined sections cannot claim to cover an unseen report.
5. Record content matching, numerical matching, source consistency, and human business judgment separately.
6. Script success does not establish analyst quality or completion of unperformed comparisons.

## Evidence locations

- Original generated report: `workspace/uk-electricity/20261031T091906-d13cddfc0136/report.pdf`
- Official report: `workspace/public-fixtures/uk-electricity/2025-release/reference.pdf`
- Numeric comparison: `workspace/uk-electricity/20261031T091906-d13cddfc0136/full-reference-evaluation.json`
- Cross-year freeze/reveal protocol: `workspace/public-fixtures/uk-electricity/2023-release/backtest-protocol.json`

Paths are relative to the workbench root. Text similarity and page count are not quality criteria.
