#!/usr/bin/env python
from __future__ import annotations
import argparse
from contrakg.io_utils import read_jsonl, write_jsonl
from contrakg.baselines import baseline_copy_gold, baseline_string_match_swap

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", required=True)
    ap.add_argument("--mode", choices=["copy_gold","string_match"], default="copy_gold")
    ap.add_argument("--use_contrast", action="store_true")
    ap.add_argument("--out_preds", required=True)
    args = ap.parse_args()

    out=[]
    for pair in read_jsonl(args.pairs):
        if args.mode=="copy_gold":
            p2 = {"orig_sentence": pair["contrast_sentence"], **pair} if args.use_contrast else pair
            triples = baseline_copy_gold(p2)
        else:
            triples = baseline_string_match_swap(pair, use_contrast=args.use_contrast)
        out.append({"id": pair["id"], "test_type": pair.get("test_type"), "pid": pair["pid"],
                    "is_contrast": bool(args.use_contrast), "triples": triples})
    write_jsonl(args.out_preds, out)
    print(f"[OK] wrote preds={args.out_preds} rows={len(out)}")

if __name__=="__main__":
    main()
