# Visual Reverse Engineering and Template Generation

[简体中文](visual-reverse-engineering.md) | English

Extract a reusable design system that remains clear as content changes. Evaluate analysis and visuals separately: similar appearance does not prove numerical correctness, and accurate numbers do not prove readability.

## 1. Establish visual evidence

Record source hashes, page/slide IDs, dimensions/orientation, renderer/version, and rendered resolution. Review thumbnails across the whole document to find patterns, then inspect each page type and unusual page closely. Do not infer the entire style from the cover. Representative sampling discovers patterns; final acceptance covers every output page.

### PPTX

- Inspect theme colors/fonts, masters, layouts, placeholders, and slide overrides. Colors can combine theme references with transparency or shade transforms; fonts can be inherited. Missing explicit values do not mean missing styling.
- Inspect paragraph/run styles, margins, spacing, alignment, and autofit. Record shape positions, dimensions, stacking, group transforms, cropping, and backgrounds.
- Distinguish native charts/tables, embedded objects, and screenshots. Screenshots do not directly recover editable data; decorative images are not analytical charts.
- Cross-check structural values against rendered appearance. Record theme-font availability; substitutions can change Chinese wrapping, weight, and line height.
- Without a PPTX renderer, structural extraction can proceed as “visual verification pending.” Do not claim inheritance or font rendering has been verified.

### PDF

- Inspect page boxes, rotation, available text/glyphs, vectors, and raster objects. Distinguish text, scanned, and mixed pages; a text layer does not imply all text is directly extractable.
- OCR scanned/image regions and verify values visually. When fonts, sizes, colors, or bounds cannot be extracted reliably, record estimates and confidence. Do not promise recovery of original themes, masters, or editable objects from screenshots.
- Record origin, rotation, and units during coordinate conversion. Compare layouts using normalized rectangles `[x/W, y/H, width/W, height/H]`, retaining original coordinates.
- Sample colors away from antialiasing edges and compression noise, using recurring placement to infer roles. The most frequent color in a photo is not necessarily a brand color.
- With PDF only, reconstruct editable templates from observation, explicitly labeling them reconstructed. Render and compare again; do not call this native template extraction.

## 2. Extract visual specifications

For each visual token/rule record `id`, `role`, `value`, `unit`, `source_file_hash`, `source_pages`, `evidence_kind` (object extraction/render observation/estimate/new design), `confidence`, applicable pages, and override rules. Examples and estimates must not masquerade as source measurements.

| Category | Required information | Checks |
| --- | --- | --- |
| Page | Aspect ratio, orientation, margins, grid, headers/footers, page number, logo area | Record different sizes separately rather than forcing one |
| Color | Background, text, brand, emphasis, dividers, series, risk/positive/negative/target roles | Separate categorical colors from favorable/unfavorable meaning; decline is not always bad |
| Typography | Chinese/Latin fonts, title/subtitle/body/note hierarchy, weight, line spacing | Use effective fonts and rendered values; record substitutions and differences |
| Layout | Alignment, columns, spacing, whitespace, title/conclusion positions | Capture constraints and flexible areas, not just fixed coordinates |
| Charts | Types, axis ranges/units, ticks, baselines, legends, labels, line widths, sources | Recompute axes for new ranges; never clip negative values or new categories |
| Tables | Headers, row heights, striping, borders, numeric alignment, units, totals | Paginate long tables with repeated headers rather than shrinking text |
| Notes | Source, definition, limitation, and emphasis hierarchy/placement | Important limitations must not become unreadable small print |

Distinguish preserved design (stable brand/semantics), adaptation (new content), and correction (readability or representation defects). Record reasons. Respect requests for strict reproduction, but disclose constraints when requirements cannot all be satisfied.

Bind categorical series colors to stable entity IDs, not sort positions. Assign new categories distinct unused styles. Growth/decline, favorable/unfavorable, risk, and branding are different semantics. Interpret colors by metric direction and add labels/symbols; do not rely only on red/green.

## 3. Derive page templates

Create only evidence-supported, business-relevant types: cover, summary, KPI overview, trend, grouped comparison, contribution breakdown, recommendations, or appendix. The same layout can serve different purposes; name templates by question and content structure, not page number alone.

Each template contains:

- `template_id`, purpose, source pages, visual-spec version.
- Content slots/bindings: titles, conclusions, metrics, charts, source notes; identify required and optional fields.
- Geometry/hierarchy: canvas, areas, anchors, alignment, spacing; decoration must not obscure content.
- Capacity: text length, series/categories, table rows; establish limits by rendering, otherwise mark them candidate.
- Adaptation order: remove repetitive wording → adjust whitespace/areas → switch layout/chart → split pages. Do not delete critical evidence or shrink fonts indefinitely.
- Editability: native charts/tables/text versus necessary images and reasons. Prefer editable PPTX objects; whole-page screenshots are not a sufficient template.
- Chart data from validated metrics; shared series colors and number formats rather than separate rules per page.

Provide usable template files or actual generation code according to the environment. A rules document alone is a visual specification, not a working template.

## 4. Cleanup and adaptation across periods

When copying PPTX layouts, remove old text, notes, hidden slides, chart caches, embedded workbooks, comments, and obsolete external links. Retain needed, authorized brand assets. Customer assets belong only to that customer's authorized project, not the shared skill. Inspect package contents as well as visible slides.

Learn visuals only from training materials or independently supplied brand templates. Do not read holdout reports to choose layouts. Historical conclusions, plotted shapes, and images must not leak into holdout generation as “visual templates.” Original pages needed for style comparison belong only in evaluation.

New periods may introduce longer titles, more categories, missing metrics, negatives, new scales, or multipage tables. Select a page type suited to the finding before applying visual rules. Missing metrics must not retain old values; continuation pages preserve definitions, title relationships, and sources.

## 5. Two-layer acceptance

**Structural checks:** slots replaced; metrics agree with text and charts; canvas, series mappings, and fonts follow specifications; bounds/accidental overlaps checked; no hidden historical data remains in the package. Geometry alone does not prove text fits.

**Rendered checks:** inspect every final page, thumbnails for consistency and full-size views for Chinese text, numbers, legends, notes, alignment, whitespace, and clipping. If PPTX delivery includes PDF export, inspect that PDF too. Renderers can differ; record the actual target.

Compare brand consistency, hierarchy, layout patterns, color semantics, readability, and content adaptation separately. New-period quality cannot be judged by full-page pixel similarity. Overlays/pixel differences only help detect drift in intended fixed areas.

Actually test at least one normal-content case and one capacity stress case, selected for real risks: long Chinese titles, many categories, or long tables. Without real references, these checks remain pending; procedure completeness is not validation.

Record each page's `page_id/template_id`, specification version, structural results, rendered image path, issue severity, revisions, and final status. Unresolved occlusion, missing numbers, or misleading colors fail visual acceptance. Correct analytical conclusions may still be delivered separately as text with the unfinished visual scope stated.
