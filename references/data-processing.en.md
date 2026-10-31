# Data Processing Procedures

[简体中文](data-processing.md) | English

## Profile first, then choose the cost

Keep originals read-only. Record SHA-256, file size, source version, and reporting cutoff. First inspect sheet names, visibility, dimension hints, and a few samples with row numbers to identify titles, multirow headers, merged areas, multiple table blocks, and subtotals. Excel's `max_row/max_column` describe a range, not the number of valid business records.

By default, `profile_table.py` inspects the first 200 physical rows and 128 columns per sheet and stores short samples from the first 5 rows. Adjust `--scan-rows`, `--max-columns`, and `--sample-rows` as needed. `--full-scan` scans every physical row but still respects the column limit. Nonempty rows are not necessarily business records. Counts include headers; the script does not automatically subtract one. `--sample-rows 0` disables sample values. Hidden rows, merged ranges, external links, pivot caches, and embedded objects require additional inspection and are not claimed as covered.

Do not require a complete count followed by a second read. If full validation is needed, combine counting, type checks, totals, and conversion in one streaming pass. Sampling the beginning can miss later type changes; production checks must cover all data used.

Choose a strategy based on selected column width, text length, estimated memory, repeated reads, and the environment, rather than row count alone:

- Small tables with sufficient memory: read required sheets, columns, and ranges; preserve original values.
- Repeated analysis or larger tables: normalize to Parquet with a schema, then read only relevant columns, partitions, and periods.
- Uncertain memory: stream with openpyxl `read_only` or CSV chunks, convert using an explicit schema, and write or aggregate each chunk. Do not concatenate everything into memory afterward.
- Without Arrow/DuckDB: use existing libraries for small tables, standard-library streaming aggregation for large ones, or state the missing dependency. Do not require another skill.

openpyxl metadata such as shared strings can still consume memory; read-only mode is not an unconditional constant-memory guarantee. Allow room for parsing, joins, and intermediate results, and adjust chunks after observing peak usage.

## Types and cleaning

| Situation | Handling |
| --- | --- |
| Multirow or merged headers | Record original positions and expansion mappings; fill only recognized header/group ranges, never blanket `ffill` |
| Duplicate or normalized duplicate field names | Use stable internal keys containing original column numbers; do not overwrite dictionary entries |
| IDs, postcodes, leading zeros | Preserve strings; numeric cell formatting may supply zeros, so consult formatting and the business dictionary |
| Amounts and percentages | Specify currency, scale, tax basis, and precision; convert 12% to 0.12, but never infer whether 0.12 or 12 is a percentage from magnitude alone |
| Numeric text | Use the agreed locale for grouping, decimal separators, and negative parentheses; retain raw values, parsed values, and failure reasons |
| Missing values | Distinguish unknown, not applicable, no event, and zero; interpret empty strings and NA markers per field |
| Outliers | Flag and investigate; do not automatically delete real events solely because they exceed an IQR threshold |
| Deduplication | Use business keys, versions, and grain; identical rows may be distinct transactions. Retain removal rationale and amount impact |
| Character normalization | Apply only defined whitespace, case, and alias transformations; do not remove all non-Chinese or nonnumeric characters |
| Precision | Use agreed Decimal arithmetic or integer minor currency units; do not default to float32 |

Handle Excel date systems, time zones, fiscal weeks/months, incomplete periods, event dates, and posting dates explicitly. Date formats and serials require workbook context.

Record input, output, and quarantined row counts, affected amounts, and rule versions for every transformation. Write parse failures to quarantine; never use `errors='coerce'` without reporting losses. An all-missing group must not silently become a real zero.

## Formulas and joins

`data_only=True` reads existing cached values; it does not calculate formulas. Inspect both formula and cached views, flagging missing caches, errors, and external dependencies. Nonempty caches may also be stale: confirm recalculation time/source or independently recompute key metrics. Do not discard uncached formulas as empty data. Recalculate in a copy using spreadsheet software and record its version; saving with openpyxl is not recalculation.

Identify detail, summary, target, and dimension tables separately. Never sum subtotals together with detail. Agree join keys and cardinality before joining sheets/files. Check null and duplicate keys, unmatched rates, and row counts and amounts before/after joins. Stop affected calculations when unexpected many-to-many joins or fanout change key metrics; fix grain and recalculate.

## Caching and export

Cache keys include source content hashes, sheet/range, field mappings, transformation version, data contract, and schema. File existence is insufficient. Write temporary files, reconcile counts/totals, and replace atomically; failures must not leave reusable partial output. Different sources must not share a fixed `/tmp/_auto_parquet.parquet`.

Define chunk schemas explicitly, including empty first chunks and later type changes. Do not convert every normalized field to a string merely to avoid schema errors. A raw string staging layer is acceptable, but analytical data needs contract-based conversion and row lineage.

Prefer vectorization and aggregation. Limited business logic may iterate in chunks when vectorization is unsuitable. Use write-only mode or partitioned files for large exports; Excel permits 1,048,576 rows per sheet including headers. Write untrusted formula-like text as text, and explicitly check formulas that are intentionally retained.

Charts read validated metrics and label periods and units. Use Chinese fonts actually available in the environment and verify rendering; do not copy another server's absolute font path. Use file/download links supported by the current host.
