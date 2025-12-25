# ContraKG-Constraints (CPU-only)

Constraint-driven contrast tests for Text→KG systems.

This repo gives you:
1) Wikidata property-constraint fetcher (P2302 + qualifiers like P2308/P2309/P2316/P2303)
2) Natural-sentence contrast-pair generator (entity swap / single-value injection)
3) Leakage metrics (Invalid Triple Leakage Rate; constraint-wise profiles)
4) Manual labeling pack (guidelines + CSV template)

## Anchors (paper-ready references)
- CheckList behavioral testing (ACL 2020): https://aclanthology.org/2020.acl-main.442/
- T-REx (LREC 2018): https://aclanthology.org/L18-1544/  | project: https://hadyelsahar.github.io/t-rex/
- Text2KGBench (ISWC 2023 / arXiv 2023): https://arxiv.org/abs/2308.02357
- Wikidata property constraints portal: https://www.wikidata.org/wiki/Help:Property_constraints_portal
- Wikidata constraint violations report: https://www.wikidata.org/wiki/Wikidata:Database_reports/Constraint_violations
- Property constraint definition (P2302): https://www.wikidata.org/wiki/Property:P2302
- Constraint status qualifier (P2316): https://www.wikidata.org/wiki/Property:P2316

## Quickstart (demo without external downloads)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python scripts/05_eval_leakage.py   --pairs data/demo_pairs.jsonl   --preds data/demo_preds.jsonl   --constraints data/demo_constraints.json   --types data/demo_types.json   --out_csv outputs/demo_leakage.csv
```

## Full pipeline (T-REx + Wikidata constraints)
### 0) Prepare base examples
Put your processed examples to `data/examples.jsonl` with fields:
```json
{"id":"...", "sentence":"...", "pid":"P19", "subj":"Q937", "obj":"Q123", "subj_label":"Albert Einstein", "obj_label":"Ulm"}
```
Tip: Start from T-REx (Wikipedia abstracts aligned with Wikidata triples). This repo does not redistribute T-REx.

### 1) Fetch constraints
```bash
python scripts/01_fetch_wikidata_constraints.py   --pids configs/properties_seed.txt   --out_json data/constraints.json
```

### 2) Build entity cache (labels + instance-of types)
```bash
python scripts/02_build_entity_cache.py   --examples data/examples.jsonl   --out_types data/types.json   --out_labels data/labels.json
```

### 3) Generate contrast pairs
```bash
python scripts/03_generate_contrasts.py   --examples data/examples.jsonl   --constraints data/constraints.json   --labels data/labels.json   --types data/types.json   --out_pairs data/pairs.jsonl
```

### 4) Run CPU baselines or plug your system
```bash
python scripts/04_run_baselines.py   --pairs data/pairs.jsonl   --mode string_match   --use_contrast   --out_preds outputs/preds.string_match.jsonl
```

### 5) Evaluate leakage
```bash
python scripts/05_eval_leakage.py   --pairs data/pairs.jsonl   --preds outputs/preds.string_match.jsonl   --constraints data/constraints.json   --types data/types.json   --out_csv outputs/leakage.string_match.csv
```

## Manual labeling
See:
- `annotation/labeling_guide.md`
- `annotation/labeling_template.csv`

## Notes / pitfalls
- Wikidata constraints are guidelines and can have explicit exceptions (P2303). Treat violations as **constraint leakage**, not "world truth".
- Constraint status (P2316) indicates mandatory/suggestion constraints; record it for analysis.
- WDQS has rate limits. Use caching + small samples first.
