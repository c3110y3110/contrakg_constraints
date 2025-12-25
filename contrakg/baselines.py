from __future__ import annotations
from typing import Dict, Any, List
import re

def _contains(label: str, text: str) -> bool:
    if not label:
        return False
    return re.search(rf"\b{re.escape(label)}\b", text) is not None or (label in text)

def baseline_copy_gold(pair: Dict[str, Any]) -> List[Dict[str, Any]]:
    s = pair["orig_sentence"]
    subj_label = pair.get("subj_label") or ""
    obj_label  = pair.get("obj_label") or ""
    out = []
    if _contains(subj_label, s) and _contains(obj_label, s):
        out.append({"subj": pair["subj"], "pid": pair["pid"], "obj": pair["obj"]})
    return out

def baseline_string_match_swap(pair: Dict[str, Any], use_contrast: bool=False) -> List[Dict[str, Any]]:
    text = pair["contrast_sentence"] if use_contrast else pair["orig_sentence"]
    subj = pair.get("contrast_subj", pair["subj"]) if use_contrast else pair["subj"]
    obj  = pair.get("contrast_obj", pair["obj"]) if use_contrast else pair["obj"]
    subj_label = pair.get("contrast_subj_label", pair.get("subj_label","")) if use_contrast else pair.get("subj_label","")
    obj_label  = pair.get("contrast_obj_label", pair.get("obj_label","")) if use_contrast else pair.get("obj_label","")

    out = []
    if _contains(subj_label, text) and _contains(obj_label, text):
        out.append({"subj": subj, "pid": pair["pid"], "obj": obj})

    if use_contrast and pair.get("test_type") == "single_value_violation":
        extra_obj = pair.get("extra_obj")
        extra_label = pair.get("extra_obj_label","")
        if extra_obj and _contains(extra_label, text):
            out.append({"subj": subj, "pid": pair["pid"], "obj": extra_obj})
    return out
