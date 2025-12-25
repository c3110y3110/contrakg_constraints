#!/usr/bin/env python
from __future__ import annotations
import argparse, json, random
from pathlib import Path
from contrakg.io_utils import read_jsonl, write_jsonl
from contrakg.contrast import build_type_pools, make_range_violation, make_subject_violation, make_single_value_violation

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--examples", required=True)
    ap.add_argument("--constraints", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--out_pairs", required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--per_class", type=int, default=50)
    ap.add_argument("--sleep", type=float, default=0.1)
    ap.add_argument("--cache_dir", default=".cache_wdqs")
    ap.add_argument("--max_pairs", type=int, default=5000)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    constraints = json.loads(Path(args.constraints).read_text(encoding="utf-8"))
    labels = json.loads(Path(args.labels).read_text(encoding="utf-8"))

    seed_classes=set()
    for _,c in constraints.items():
        for tc in c.get("subject_type",[]):
            seed_classes.update(tc.get("classes") or [])
        for tc in c.get("value_type",[]):
            seed_classes.update(tc.get("classes") or [])
    seed_classes=sorted(seed_classes)[:50]

    type_pools = build_type_pools(seed_classes, cache_dir=args.cache_dir, per_class=args.per_class, sleep=args.sleep)

    pairs=[]
    for ex in read_jsonl(args.examples):
        cand=[]
        v1 = make_range_violation(ex, constraints, labels, type_pools, rng)
        if v1: cand.append(v1)
        v2 = make_subject_violation(ex, constraints, labels, type_pools, rng)
        if v2: cand.append(v2)
        v3 = make_single_value_violation(ex, constraints, labels, rng)
        if v3: cand.append(v3)
        for v in cand:
            pairs.append(v)
            if len(pairs) >= args.max_pairs:
                break
        if len(pairs) >= args.max_pairs:
            break

    write_jsonl(args.out_pairs, pairs)
    print(f"[OK] wrote pairs={args.out_pairs} n={len(pairs)}")

if __name__=="__main__":
    main()
