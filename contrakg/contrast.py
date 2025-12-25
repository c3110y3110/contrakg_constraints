from __future__ import annotations
import random, re
from typing import Dict, Any, List, Optional
from .wikidata import sparql, qid
from .io_utils import SimpleDiskCache

def _safe_replace(sentence: str, old: str, new: str) -> str:
    if not old or old == new:
        return sentence
    if old in sentence:
        return sentence.replace(old, new, 1)
    pat = re.compile(rf"\b{re.escape(old)}\b", flags=re.IGNORECASE)
    return pat.sub(new, sentence, count=1)

def pick_entity_of_class(target_class_qid: str, cache: SimpleDiskCache, k: int=50, sleep: float=0.1) -> List[str]:
    q = f"""
    SELECT ?x WHERE {{
      ?x wdt:P31/wdt:P279* wd:{target_class_qid} .
    }} LIMIT {int(k)}
    """
    js = sparql(q, cache=cache, sleep=sleep)
    return [qid(b["x"]["value"]) for b in js["results"]["bindings"]]

def build_type_pools(seed_classes: List[str], cache_dir: str=".cache_wdqs", per_class: int=50, sleep: float=0.1) -> Dict[str, List[str]]:
    cache = SimpleDiskCache(cache_dir)
    pools = {}
    for c in seed_classes:
        try:
            pools[c] = pick_entity_of_class(c, cache=cache, k=per_class, sleep=sleep)
        except Exception:
            pools[c] = []
    return pools

def make_range_violation(example: Dict[str, Any],
                         constraints: Dict[str, Any],
                         labels: Dict[str, str],
                         type_pools: Dict[str, List[str]],
                         rng: random.Random) -> Optional[Dict[str, Any]]:
    pid = example["pid"]
    c = constraints.get(pid, {})
    vlist = c.get("value_type", [])
    if not vlist:
        return None
    allowed = vlist[0].get("classes") or []
    if not allowed:
        return None

    pools = [(cls, type_pools.get(cls, [])) for cls in type_pools.keys() if cls not in set(allowed)]
    pools = [(cls, pool) for cls, pool in pools if pool]
    if not pools:
        return None
    bad_cls, pool = rng.choice(pools)
    new_obj = rng.choice(pool)
    new_label = labels.get(new_obj)
    if not new_label:
        return None

    sent2 = _safe_replace(example["sentence"], example.get("obj_label",""), new_label)
    if sent2 == example["sentence"]:
        return None

    return {
        "id": example["id"],
        "test_type": "value_type_violation",
        "pid": pid,
        "subj": example["subj"],
        "obj": example["obj"],
        "subj_label": example.get("subj_label"),
        "obj_label": example.get("obj_label"),
        "orig_sentence": example["sentence"],
        "contrast_sentence": sent2,
        "contrast_obj": new_obj,
        "contrast_obj_label": new_label,
        "target_allowed_classes": allowed,
        "contrast_obj_class_pool": bad_cls,
        "edit": {"op": "replace_obj", "from": example.get("obj_label"), "to": new_label},
    }

def make_subject_violation(example: Dict[str, Any],
                           constraints: Dict[str, Any],
                           labels: Dict[str, str],
                           type_pools: Dict[str, List[str]],
                           rng: random.Random) -> Optional[Dict[str, Any]]:
    pid = example["pid"]
    c = constraints.get(pid, {})
    slist = c.get("subject_type", [])
    if not slist:
        return None
    allowed = slist[0].get("classes") or []
    if not allowed:
        return None

    pools = [(cls, type_pools.get(cls, [])) for cls in type_pools.keys() if cls not in set(allowed)]
    pools = [(cls, pool) for cls, pool in pools if pool]
    if not pools:
        return None
    bad_cls, pool = rng.choice(pools)
    new_subj = rng.choice(pool)
    new_label = labels.get(new_subj)
    if not new_label:
        return None

    sent2 = _safe_replace(example["sentence"], example.get("subj_label",""), new_label)
    if sent2 == example["sentence"]:
        return None

    return {
        "id": example["id"],
        "test_type": "subject_type_violation",
        "pid": pid,
        "subj": example["subj"],
        "obj": example["obj"],
        "subj_label": example.get("subj_label"),
        "obj_label": example.get("obj_label"),
        "orig_sentence": example["sentence"],
        "contrast_sentence": sent2,
        "contrast_subj": new_subj,
        "contrast_subj_label": new_label,
        "target_allowed_classes": allowed,
        "contrast_subj_class_pool": bad_cls,
        "edit": {"op": "replace_subj", "from": example.get("subj_label"), "to": new_label},
    }

def make_single_value_violation(example: Dict[str, Any],
                                constraints: Dict[str, Any],
                                labels: Dict[str, str],
                                rng: random.Random) -> Optional[Dict[str, Any]]:
    pid = example["pid"]
    c = constraints.get(pid, {})
    if not c.get("single_value", False):
        return None

    candidates = [q for q,l in labels.items() if q != example.get("obj") and l and len(l.split()) <= 4]
    if not candidates:
        return None
    obj2 = rng.choice(candidates)
    obj2_label = labels.get(obj2)
    if not obj2_label:
        return None

    s = example["sentence"]
    olabel = example.get("obj_label","")
    if olabel and olabel in s:
        s2 = s.replace(olabel, f"{olabel} and {obj2_label}", 1)
    else:
        s2 = s.rstrip(".") + f" and {obj2_label}."
    if s2 == s:
        return None

    return {
        "id": example["id"],
        "test_type": "single_value_violation",
        "pid": pid,
        "subj": example["subj"],
        "obj": example["obj"],
        "subj_label": example.get("subj_label"),
        "obj_label": example.get("obj_label"),
        "orig_sentence": example["sentence"],
        "contrast_sentence": s2,
        "extra_obj": obj2,
        "extra_obj_label": obj2_label,
        "edit": {"op": "duplicate_value", "add": obj2_label},
    }
