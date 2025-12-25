from __future__ import annotations
import requests, time
from typing import Dict, Any, Optional
from .io_utils import SimpleDiskCache

WDQS = "https://query.wikidata.org/sparql"

HEADERS = {
    "User-Agent": "ContraKG-Constraints/0.1 (local-run)",
    "Accept": "application/sparql-results+json"
}

def sparql(query: str, cache: Optional[SimpleDiskCache]=None, sleep: float=0.0) -> Dict[str, Any]:
    if cache is not None:
        hit = cache.get(query)
        if hit is not None:
            return hit
    if sleep:
        time.sleep(sleep)
    r = requests.get(WDQS, params={"query": query}, headers=HEADERS, timeout=60)
    r.raise_for_status()
    js = r.json()
    if cache is not None:
        cache.set(query, js)
    return js

def qid(url_or_qid: str) -> str:
    return url_or_qid.rsplit("/",1)[-1] if url_or_qid.startswith("http") else url_or_qid

def pid(url_or_pid: str) -> str:
    return url_or_pid.rsplit("/",1)[-1] if url_or_pid.startswith("http") else url_or_pid
