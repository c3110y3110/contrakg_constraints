#!/usr/bin/env python
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
from contrakg.io_utils import read_jsonl
from contrakg.eval import TypeOracle, violates_value_type, violates_subject_type, violates_single_value

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", required=True)
    ap.add_argument("--preds", required=True)
    ap.add_argument("--constraints", required=True)
    ap.add_argument("--types", required=False, default=None)
    ap.add_argument("--use_oracle", action="store_true")
    ap.add_argument("--cache_dir", default=".cache_wdqs")
    ap.add_argument("--sleep", type=float, default=0.05)
    ap.add_argument("--out_csv", required=True)
    args = ap.parse_args()

    constraints = json.loads(Path(args.constraints).read_text(encoding="utf-8"))
    types_cache = json.loads(Path(args.types).read_text(encoding="utf-8")) if args.types else None
    oracle = TypeOracle(cache_dir=args.cache_dir, sleep=args.sleep) if args.use_oracle else None

    rows=[]
    for pr in read_jsonl(args.preds):
        pid = pr["pid"]
        c = constraints.get(pid, {})
        triples = pr.get("triples", [])
        v_val = any(violates_value_type(t, c, oracle, types_cache) for t in triples)
        v_sub = any(violates_subject_type(t, c, oracle, types_cache) for t in triples)
        v_single = violates_single_value(triples, c)
        violated = v_val or v_sub or v_single

        rows.append({
            "id": pr["id"],
            "test_type": pr.get("test_type"),
            "pid": pid,
            "n_triples": len(triples),
            "viol_value_type": int(v_val),
            "viol_subject_type": int(v_sub),
            "viol_single_value": int(v_single),
            "any_violation": int(violated),
        })

    df = pd.DataFrame(rows)
    df["has_output"] = (df["n_triples"] > 0).astype(int)
    itlr = (df.loc[df["has_output"]==1, "any_violation"].mean() if (df["has_output"]==1).any() else 0.0)
    summary = pd.DataFrame([{
        "ITLR": float(itlr),
        "rows": int(len(df)),
        "rows_with_output": int(df["has_output"].sum()),
        "viol_rate_any": float(df["any_violation"].mean() if len(df) else 0.0)
    }])

    out_path = Path(args.out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out_path.with_suffix(".xlsx")) as w:
        df.to_excel(w, index=False, sheet_name="per_example")
        summary.to_excel(w, index=False, sheet_name="summary")
    df.to_csv(out_path, index=False)
    print(f"[OK] wrote {args.out_csv} and {out_path.with_suffix('.xlsx')}")

if __name__=="__main__":
    main()
