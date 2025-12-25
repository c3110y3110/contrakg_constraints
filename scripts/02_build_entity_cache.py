#!/usr/bin/env python
from __future__ import annotations
import argparse, json
from pathlib import Path
from collections import defaultdict
from contrakg.io_utils import read_jsonl
from contrakg.wikidata import sparql, qid
from contrakg.io_utils import SimpleDiskCache

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--examples", required=True)
    ap.add_argument("--out_types", required=True)
    ap.add_argument("--out_labels", required=True)
    ap.add_argument("--cache_dir", default=".cache_wdqs")
    ap.add_argument("--sleep", type=float, default=0.1)
    args = ap.parse_args()

    ents=set()
    for ex in read_jsonl(args.examples):
        ents.add(ex["subj"]); ents.add(ex["obj"])
    ents=sorted(ents)
    cache = SimpleDiskCache(args.cache_dir)

    labels={}
    chunk=200
    for i in range(0, len(ents), chunk):
        sub=ents[i:i+chunk]
        values=" ".join([f"wd:{e}" for e in sub])
        q=f"""
        SELECT ?x ?xLabel WHERE {{
          VALUES ?x {{ {values} }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        """
        js=sparql(q, cache=cache, sleep=args.sleep)
        for b in js["results"]["bindings"]:
            labels[qid(b["x"]["value"])]=b.get("xLabel",{}).get("value","")

    types=defaultdict(list)
    for i in range(0, len(ents), chunk):
        sub=ents[i:i+chunk]
        values=" ".join([f"wd:{e}" for e in sub])
        q=f"""
        SELECT ?x ?t WHERE {{
          VALUES ?x {{ {values} }}
          OPTIONAL {{ ?x wdt:P31 ?t . }}
        }}
        """
        js=sparql(q, cache=cache, sleep=args.sleep)
        for b in js["results"]["bindings"]:
            x=qid(b["x"]["value"])
            if "t" in b:
                types[x].append(qid(b["t"]["value"]))

    Path(args.out_labels).write_text(json.dumps(labels, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.out_types).write_text(json.dumps(types, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] wrote labels={args.out_labels}, types={args.out_types}, ents={len(ents)}")

if __name__=="__main__":
    main()
