# Reverse-Engineering Reports and Generating New Periods

[简体中文](report-workflow.md) | English

## Reading PDF/PPTX

Record page/slide counts and structure. OCR PDFs without a text layer. Extract text with page numbers and render pages containing charts, footnotes, and complex tables for verification. For PPTX, inspect body text, shapes, tables, chart data, embedded workbooks, and speaker notes; text boxes alone do not represent the entire slide.

Use available PDF/presentation tools. Without a dedicated skill, use local PDF rendering/OCR or OOXML parsing, recording missing capabilities and uncovered content. Never claim to have inspected unrendered visual information. Values read from charts are approximate evidence, not substitutes for precise source calculations.

Extract each section's questions, metrics, comparisons, dimensions, reasoning, and recommendations. Distinguish required company definitions from individual writing habits that can improve. Recompute suspicious chart values and record contradictions in the reference report.

Also follow the [visual reverse-engineering procedures](visual-reverse-engineering.en.md) to extract color roles, typography, grids, chart styles, and reusable layouts. Keep content and visual evidence separate, linking them with source-page IDs. Visual appeal and analytical correctness are separate assessments.

## Coverage gate

When matching a reference report, first inventory its sections, charts, appendices, and key explanations page by page, recording source data, implementation, output pages, and unresolved items. Do not replace a full target with a summary on your own. Distinguish recomputable content, externally supported explanations, referenced assets, and unimplemented items. Evaluate topic coverage, numerical agreement, and analytical quality separately. Preserve disagreements between source data and reference prose; never alter correct calculations to improve matching.

## Generating a new period

For an established project, existing scripts execute stable stages under the [execution and performance procedures](execution-performance.en.md). Generate new code only for initial construction or material definition/structure changes. Routine periods do not relearn reference reports.

1. Check files, metric versions, additive dimensions, and time windows. Detect missing fields, type changes, new categories, and revisions; check assumption revalidation triggers.
2. Validate and calculate deterministically, producing metrics and exceptions. For inconsistent source values, locate the first divergence and reconcile the bridge under the [contracts](contracts.en.md). Critical errors, failed assumptions, or unexplained differences block dependent conclusions; unaffected analysis can continue.
3. Execute established analysis rules and build a compact evidence packet. Use the model only for synthesis. Follow [multi-perspective analysis](analysis-synthesis.en.md), starting with totals and drilling down as needed; state unanswered questions and evidence gaps. Use conditional templates for routine facts instead of per-page model calls.
4. Write the claim ledger, deduplicate findings, reconcile scope differences and substantive conflicts, then synthesize by theme. New insights need the same traceability even when absent from the reference. Retain competing explanations; majority opinion does not replace verification.
5. Select narrative components and page types, organized as conclusion → evidence → risks/limits → action. Scripts bind validated metrics and claim IDs, apply visual rules, and render. Long titles, extra categories, negative values, and long tables trigger defined capacity/layout adaptation. Intervene when exceeding validated capabilities; never retain stale values or invalid axes.
6. Recompute key figures, check totals and agreement between text and graphics, and ensure outputs do not depend on invalid or unreviewed critical assumptions. Perform structural and page-by-page visual checks, documenting inherited design, adaptations, and fixes. Deliver the requested format with concise limitations.

Prioritize decision-relevant changes and evidence in the body. Put methods and complete quality records in appendices/run directories. When evidence is missing, state that verification is needed and identify the next evidence-gathering step, rather than presenting a known cause.

Follow the user's requested format. Otherwise establish conclusions in an auditable text draft before selecting the reader's format. Do not copy obsolete sections to imitate a reference or force every method into the body.
