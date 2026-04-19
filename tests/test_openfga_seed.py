from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_seed_module():
    seed_path = Path(__file__).resolve().parents[1] / "deploy" / "openfga" / "seed.py"
    spec = importlib.util.spec_from_file_location("openfga_seed", seed_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_seed_inline_model_job_relations_match_enforcement_scope():
    seed = _load_seed_module()
    payload = seed._build_model_payload()

    job_defs = [d for d in payload["type_definitions"] if d.get("type") == "job"]
    assert len(job_defs) == 1

    job_relations = job_defs[0]["relations"]
    assert "can_submit" in job_relations
    assert "can_cancel" in job_relations
    assert {"analyst", "reviewer", "compliance_officer", "admin"} <= set(job_relations.keys())

    def _computed_children(rel_def: dict) -> set[str]:
        children = rel_def["union"]["child"]
        return {
            child["computedUserset"]["relation"]
            for child in children
            if "computedUserset" in child
        }

    assert _computed_children(job_relations["can_submit"]) == {"analyst", "reviewer", "compliance_officer", "admin"}
    assert _computed_children(job_relations["can_cancel"]) == {"reviewer", "compliance_officer", "admin"}
