"""Deterministic transport snapshot built from the already validated analysis."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import tempfile

from . import config


GLOBAL_LIMITATIONS = [
    "inflow_incomplete", "date_only", "period_censored", "threshold_5000",
    "intrabank_only", "path_not_money_provenance",
]


def _summary(profile: dict) -> dict:
    return {
        key: deepcopy(profile[key]) for key in (
            "gid", "depth", "is_seed", "role", "role_score", "priority_score",
            "cluster_id", "why", "limitations",
        )
    } | {"evidence": profile["evidence_text"]}


def _snapshot_id(data_dir: Path) -> str:
    digest = hashlib.sha256()
    for path in (
        *(data_dir / f"{name}.parquet" for name in ("nodes", "edges", "transactions")),
        Path(config.__file__), Path(__file__).with_name("run.py"),
    ):
        digest.update(path.name.encode("ascii"))
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()[:24]


def build_snapshot(result, nodes, edges, data_dir: Path) -> dict:
    profiles = {}
    for gid, profile in result.profiles.items():
        entity = deepcopy(profile)
        entity.pop("priority_components")
        profiles[str(gid)] = entity
    ranked = sorted(result.profiles, key=lambda gid: (-result.profiles[gid]["priority_score"], gid))
    clusters = [
        {
            **cluster,
            "sum_kzt_internal": float(cluster["sum_kzt_internal"]),
            "top_gids": cluster["top_gids"].split(";") if cluster["top_gids"] else [],
        }
        for cluster in result.clusters
    ]
    edge_items = [
        {"src": str(row.src), "dst": str(row.dst),
         "sum_kzt": int(row.cents) / 100, "n_tx": int(row.n_tx)}
        for row in edges.itertuples(index=False)
    ]
    meta = {
        "contract_version": "1", "snapshot_id": _snapshot_id(data_dir),
        "rules_version": config.RULES_VERSION, "data_mode": "live",
    }
    return {
        "meta": meta,
        "summary": {
            "period": {"from": "2026-07-01", "to": "2026-07-31"},
            "counts": {
                "n_nodes": result.n_nodes, "n_edges": result.n_edges,
                "n_transactions": result.n_transactions,
                "n_seed": int(nodes.is_seed.sum()),
                "n_components": result.n_components,
                "n_components_with_edges": result.n_components - result.n_isolates,
                "n_isolates": result.n_isolates,
                "n_depth_truncated": int((nodes.depth == 4).sum()),
                "n_clusters": len(clusters),
            },
            "total_observed_kzt": sum(int(x) for x in edges.cents) / 100,
            "limitations": GLOBAL_LIMITATIONS,
            "top_nodes": [_summary(result.profiles[gid]) for gid in ranked[:20]],
        },
        "profiles": profiles,
        "edges": edge_items,
        "clusters": clusters,
    }


def export_snapshot(result, nodes, edges, data_dir: Path, out_dir: Path) -> Path:
    snapshot = build_snapshot(result, nodes, edges, data_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "snapshot.json"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", dir=out_dir,
                                     prefix="snapshot-stage-", suffix=".json", delete=False) as handle:
        stage = Path(handle.name)
        try:
            json.dump(snapshot, handle, ensure_ascii=False, allow_nan=False,
                      sort_keys=True, separators=(",", ":"))
            handle.write("\n")
        except BaseException:
            handle.close()
            stage.unlink(missing_ok=True)
            raise
    os.replace(stage, target)
    return target
