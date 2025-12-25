from __future__ import annotations
from typing import Dict, Any, List, Optional
from .wikidata import sparql
from .io_utils import SimpleDiskCache

class TypeOracle:
    def __init__(self, cache_dir: str=".cache_wdqs", sleep: float=0.05):
        self.cache = SimpleDiskCache(cache_dir)
        self.sleep = sleep

    def is_instance_or_subclass(self, ent_qid: str, class_qid: str) -> bool:
        q = f"ASK {{ wd:{ent_qid} wdt:P31/wdt:P279* wd:{class_qid} . }}"
        js = sparql(q, cache=self.cache, sleep=self.sleep)
        return bool(js.get("boolean", False))

def violates_value_type(triple: Dict[str, str], c: Dict[str, Any], oracle: Optional[TypeOracle], types_cache: Optional[Dict[str, List[str]]] = None) -> bool:
    vlist = c.get("value_type", [])
    if not vlist:
        return False
    allowed = vlist[0].get("classes") or []
    if not allowed:
        return False

    obj = triple["obj"]
    exc = set(vlist[0].get("exceptions") or [])
    if obj in exc:
        return False

    if types_cache is not None and obj in types_cache:
        cached = set(types_cache.get(obj, []))
        if cached.intersection(set(allowed)):
            return False
        if oracle is None:
            return False
        ok = any(oracle.is_instance_or_subclass(obj, a) for a in allowed)
        return not ok

    if oracle is None:
        return False
    ok = any(oracle.is_instance_or_subclass(obj, a) for a in allowed)
    return not ok

def violates_subject_type(triple: Dict[str, str], c: Dict[str, Any], oracle: Optional[TypeOracle], types_cache: Optional[Dict[str, List[str]]] = None) -> bool:
    slist = c.get("subject_type", [])
    if not slist:
        return False
    allowed = slist[0].get("classes") or []
    if not allowed:
        return False

    subj = triple["subj"]
    exc = set(slist[0].get("exceptions") or [])
    if subj in exc:
        return False

    if types_cache is not None and subj in types_cache:
        cached = set(types_cache.get(subj, []))
        if cached.intersection(set(allowed)):
            return False
        if oracle is None:
            return False
        ok = any(oracle.is_instance_or_subclass(subj, a) for a in allowed)
        return not ok

    if oracle is None:
        return False
    ok = any(oracle.is_instance_or_subclass(subj, a) for a in allowed)
    return not ok

def violates_single_value(triples: List[Dict[str,str]], c: Dict[str, Any]) -> bool:
    if not c.get("single_value", False):
        return False
    seen = {}
    for t in triples:
        key = (t["subj"], t["pid"])
        seen.setdefault(key, set()).add(t["obj"])
    return any(len(v) >= 2 for v in seen.values())
