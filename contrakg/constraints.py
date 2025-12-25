from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from .wikidata import sparql, qid, pid
from .io_utils import SimpleDiskCache

# Constraint-type QIDs
Q_SUBJECT_TYPE = "Q21503250"  # subject type constraint
Q_VALUE_TYPE   = "Q21510865"  # value-type constraint
Q_SINGLE_VALUE = "Q19474404"  # single-value constraint

@dataclass
class TypeConstraint:
    constraint_qid: str
    classes: List[str]
    relation: Optional[str] = None
    status: Optional[str] = None
    exceptions: List[str] = None

    def to_dict(self):
        d = asdict(self)
        d["exceptions"] = self.exceptions or []
        return d

@dataclass
class PropertyConstraints:
    pid: str
    subject_type: List[TypeConstraint]
    value_type: List[TypeConstraint]
    single_value: bool = False
    single_value_status: Optional[str] = None
    single_value_exceptions: List[str] = None

    def to_dict(self):
        return {
            "pid": self.pid,
            "subject_type": [c.to_dict() for c in self.subject_type],
            "value_type": [c.to_dict() for c in self.value_type],
            "single_value": self.single_value,
            "single_value_status": self.single_value_status,
            "single_value_exceptions": self.single_value_exceptions or [],
        }

def fetch_constraints(pids: List[str], cache_dir: str=".cache_wdqs", sleep: float=0.1) -> Dict[str, Any]:
    cache = SimpleDiskCache(cache_dir)
    out: Dict[str, PropertyConstraints] = {}

    values = " ".join([f"wd:{p.strip()}" for p in pids if p.strip()])
    if not values:
        raise ValueError("No pids given.")
    q = f"""
    SELECT ?p ?constraint ?class ?relation ?status ?exception WHERE {{
      VALUES ?p {{ {values} }}
      ?p p:P2302 ?st .
      ?st ps:P2302 ?constraint .
      OPTIONAL {{ ?st pq:P2308 ?class . }}
      OPTIONAL {{ ?st pq:P2309 ?relation . }}
      OPTIONAL {{ ?st pq:P2316 ?status . }}
      OPTIONAL {{ ?st pq:P2303 ?exception . }}
    }}
    """
    js = sparql(q, cache=cache, sleep=sleep)
    rows = js["results"]["bindings"]

    tmp: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for r in rows:
        p = pid(r["p"]["value"])
        c = qid(r["constraint"]["value"])
        tmp.setdefault(p, {}).setdefault(c, {"classes": set(), "relations": set(), "statuses": set(), "exceptions": set()})
        if "class" in r:
            tmp[p][c]["classes"].add(qid(r["class"]["value"]))
        if "relation" in r:
            tmp[p][c]["relations"].add(qid(r["relation"]["value"]))
        if "status" in r:
            tmp[p][c]["statuses"].add(qid(r["status"]["value"]))
        if "exception" in r:
            tmp[p][c]["exceptions"].add(qid(r["exception"]["value"]))

    for p in pids:
        p = p.strip()
        if not p:
            continue
        byc = tmp.get(p, {})
        subj_list = []
        val_list = []
        single = False
        single_status = None
        single_ex = []

        if Q_SUBJECT_TYPE in byc:
            d = byc[Q_SUBJECT_TYPE]
            subj_list.append(TypeConstraint(
                constraint_qid=Q_SUBJECT_TYPE,
                classes=sorted(d["classes"]),
                relation=sorted(d["relations"])[0] if d["relations"] else None,
                status=sorted(d["statuses"])[0] if d["statuses"] else None,
                exceptions=sorted(d["exceptions"])
            ))
        if Q_VALUE_TYPE in byc:
            d = byc[Q_VALUE_TYPE]
            val_list.append(TypeConstraint(
                constraint_qid=Q_VALUE_TYPE,
                classes=sorted(d["classes"]),
                relation=sorted(d["relations"])[0] if d["relations"] else None,
                status=sorted(d["statuses"])[0] if d["statuses"] else None,
                exceptions=sorted(d["exceptions"])
            ))
        if Q_SINGLE_VALUE in byc:
            single = True
            d = byc[Q_SINGLE_VALUE]
            single_status = sorted(d["statuses"])[0] if d["statuses"] else None
            single_ex = sorted(d["exceptions"])

        out[p] = PropertyConstraints(
            pid=p, subject_type=subj_list, value_type=val_list,
            single_value=single, single_value_status=single_status,
            single_value_exceptions=single_ex
        )

    return {p: pc.to_dict() for p, pc in out.items()}
