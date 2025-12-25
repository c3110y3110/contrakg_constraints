# Paper-facing cautions (copy into limitations)
- Wikidata constraints are guidelines and can have explicit exceptions (P2303). Avoid claiming "world truth".
- Treat leakage as data-quality constraint leakage for KG construction pipelines.
- Disclose which constraint types you operationalize (we focus on subject/value type + single-value).
- Report constraint status (P2316) and analyze mandatory vs non-mandatory separately.

# Reproducibility checklist
- Freeze PID list + sampling seed + max_pairs
- Cache WDQS queries; log query counts and failures
- Release manual labels and annotation guidelines
