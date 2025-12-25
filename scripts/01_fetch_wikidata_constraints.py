#!/usr/bin/env python
from __future__ import annotations
import argparse, json
from pathlib import Path
from contrakg.constraints import fetch_constraints

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pids", required=True)
    ap.add_argument("--out_json", required=True)
    ap.add_argument("--cache_dir", default=".cache_wdqs")
    ap.add_argument("--sleep", type=float, default=0.2)
    args = ap.parse_args()

    pids = [l.strip().split()[0] for l in Path(args.pids).read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.strip().startswith("#")]
    data = fetch_constraints(pids, cache_dir=args.cache_dir, sleep=args.sleep)
    Path(args.out_json).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] wrote {args.out_json} (pids={len(pids)})")

if __name__ == "__main__":
    main()
