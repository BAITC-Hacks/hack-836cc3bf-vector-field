"""Parquet -> validated graph analytics -> the three official CSV exports."""

from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
import csv
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import json
import math
import os
from pathlib import Path
import tempfile
import time

import networkx as nx
import numpy as np
import pandas as pd

from . import config as cfg


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "case" / "data (1)" / "data"
DEFAULT_OUT = ROOT / "pipeline" / "out"
SCOPE = "observed_intrabank_july_2026"
CSV_COLUMNS = {
    "nodes_roles.csv": ("gid", "role", "role_score", "cluster_id", "priority_score", "evidence"),
    "clusters.csv": ("cluster_id", "n_nodes", "n_seed", "sum_kzt_internal", "top_gids", "hypothesis"),
    "top_nodes.csv": ("rank", "gid", "role", "priority_score", "why"),
}


class DataError(ValueError):
    """Input/schema/invariant failure: no CSV is published."""


def cents(value: object) -> int:
    try:
        number = Decimal(str(value))
        if not number.is_finite():
            raise ValueError("non-finite amount")
        return int((number * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except (ValueError, ArithmeticError) as exc:
        raise DataError(f"Invalid KZT amount: {value!r}") from exc


def kzt(value_cents: int) -> str:
    return f"{Decimal(value_cents) / 100:.2f}"


def load_and_validate(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    required = {
        "nodes": {"gid", "depth", "is_seed"},
        "edges": {"src", "dst", "sum_kzt", "n_tx", "depth"},
        "transactions": {"src", "dst", "date", "sum_kzt"},
    }
    tables: dict[str, pd.DataFrame] = {}
    for name, columns in required.items():
        path = data_dir / f"{name}.parquet"
        if not path.is_file():
            raise DataError(f"Missing input: {path}")
        try:
            frame = pd.read_parquet(path)
        except Exception as exc:
            raise DataError(f"Cannot read {path}: {exc}") from exc
        missing = columns - set(frame.columns)
        if missing:
            raise DataError(f"{path.name}: missing columns {sorted(missing)}")
        if frame[list(columns)].isna().any().any():
            raise DataError(f"{path.name}: null in required columns")
        tables[name] = frame
    nodes, edges, tx = (tables[x] for x in ("nodes", "edges", "transactions"))
    for table_name, frame, cols in (
        ("nodes", nodes, ("gid", "depth")),
        ("edges", edges, ("src", "dst", "n_tx", "depth")),
        ("transactions", tx, ("src", "dst")),
    ):
        for col in cols:
            if not pd.api.types.is_integer_dtype(frame[col]):
                raise DataError(f"{table_name}.{col} must be an integer dtype (gid int64)")
    for name, frame, cols in (("nodes", nodes, ("gid",)), ("edges", edges, ("src", "dst")), ("transactions", tx, ("src", "dst"))):
        for col in cols:
            if frame[col].dtype != "int64":
                raise DataError(f"{name}.{col} must be int64; got {frame[col].dtype}")
    if not pd.api.types.is_bool_dtype(nodes["is_seed"]):
        raise DataError("nodes.is_seed must be boolean")
    if nodes.empty or edges.empty or tx.empty:
        raise DataError("Input tables must be non-empty")
    if nodes.gid.duplicated().any():
        raise DataError("nodes.gid contains duplicates")
    if edges.duplicated(["src", "dst"]).any():
        raise DataError("edges contains duplicate src,dst pairs")
    if not nodes.depth.between(0, 4).all() or not edges.depth.between(1, 4).all():
        raise DataError("depth outside the observed 0..4 / 1..4 range")
    if (nodes.is_seed != (nodes.depth == 0)).any():
        raise DataError("is_seed and depth=0 disagree")
    gids = set(int(g) for g in nodes.gid)
    for name, frame in (("edges", edges), ("transactions", tx)):
        unknown = (set(int(g) for g in frame.src) | set(int(g) for g in frame.dst)) - gids
        if unknown:
            raise DataError(f"{name}: {len(unknown)} unknown endpoints, e.g. {min(unknown)}")
    if (edges.n_tx <= 0).any():
        raise DataError("edges.n_tx must be positive")
    try:
        dates = pd.to_datetime(tx.date, errors="raise")
    except Exception as exc:
        raise DataError(f"transactions.date invalid: {exc}") from exc
    if ((dates < pd.Timestamp("2026-07-01")) | (dates >= pd.Timestamp("2026-08-01"))).any():
        raise DataError("transactions.date outside July 2026")
    if (dates != dates.dt.normalize()).any():
        raise DataError("transactions.date has intraday time; expected date precision")
    tx = tx.copy()
    tx["date"] = dates
    edges = edges.copy()
    tx["cents"] = [cents(x) for x in tx.sum_kzt]
    edges["cents"] = [cents(x) for x in edges.sum_kzt]
    if (tx.cents < 500000).any() or (edges.cents <= 0).any():
        raise DataError("nonpositive edge or transaction below 5000 KZT")
    aggregate: dict[tuple[int, int], list[int]] = defaultdict(lambda: [0, 0])
    for row in tx.itertuples(index=False):  # Repeated rows are separate transactions.
        item = aggregate[(int(row.src), int(row.dst))]
        item[0] += int(row.cents)
        item[1] += 1
    edge_pairs: set[tuple[int, int]] = set()
    for row in edges.itertuples(index=False):
        pair = (int(row.src), int(row.dst))
        edge_pairs.add(pair)
        if aggregate.get(pair) != [int(row.cents), int(row.n_tx)]:
            raise DataError(f"edges/transactions sum or n_tx mismatch for {pair}")
    if edge_pairs != set(aggregate):
        raise DataError("edges/transactions pairs differ")
    if sum(int(x) for x in edges.cents) != sum(int(x) for x in tx.cents):
        raise DataError("total edge and transaction amounts differ")
    return nodes.sort_values("gid").reset_index(drop=True), edges.sort_values(["src", "dst"]).reset_index(drop=True), tx


def positive_midrank(values: dict[int, float]) -> dict[int, float]:
    positive = sorted(v for v in values.values() if math.isfinite(v) and v > 0)
    if any(not math.isfinite(v) or v < 0 for v in values.values()):
        raise DataError("normalization feature is missing, negative, or non-finite")
    if not positive:
        return {gid: 0.0 for gid in values}
    n = len(positive)
    return {gid: (bisect_left(positive, x) + 0.5 * (bisect_right(positive, x) - bisect_left(positive, x))) / n if x > 0 else 0.0 for gid, x in values.items()}


def fact(gid: int, metric: str, value: int | float | str | None, unit: str, rule_id: str, source: str, text: str, limitations: list[str]) -> dict:
    return {
        "evidence_id": f"node:{gid}:{rule_id}:{metric}", "gid": str(gid),
        "metric": metric, "value": value, "unit": unit, "rule_id": rule_id,
        "source": source, "scope": SCOPE, "text": text,
        "limitations": limitations.copy(),
    }


@dataclass
class AnalysisResult:
    profiles: dict[int, dict]
    clusters: list[dict]
    top: list[dict]
    n_nodes: int
    n_edges: int
    n_transactions: int
    n_components: int
    n_isolates: int


def analyze(nodes: pd.DataFrame, edges: pd.DataFrame, tx: pd.DataFrame) -> AnalysisResult:
    graph = nx.DiGraph()
    graph.add_nodes_from(int(g) for g in nodes.gid)  # Include isolates before any edge.
    for row in edges.itertuples(index=False):
        graph.add_edge(int(row.src), int(row.dst), cents=int(row.cents), n_tx=int(row.n_tx))
    components = sorted(nx.weakly_connected_components(graph), key=lambda c: (-len(c), min(c)))
    isolates = set(nx.isolates(graph))
    undirected = nx.Graph()
    undirected.add_nodes_from(graph.nodes)
    for src, dst, attrs in graph.edges(data=True):
        if undirected.has_edge(src, dst):
            undirected[src][dst]["weight"] += attrs["cents"]
        else:
            undirected.add_edge(src, dst, weight=attrs["cents"])
    communities: list[set[int]] = []
    for component in components:
        if len(component) == 1:
            communities.append(set(component))
        else:
            subgraph = undirected.subgraph(sorted(component)).copy()
            communities.extend(nx.community.louvain_communities(
                subgraph, weight="weight", seed=cfg.LOUVAIN_SEED,
                resolution=cfg.LOUVAIN_RESOLUTION,
            ))
    communities.sort(key=lambda c: (-len(c), min(c)))
    cluster_by_gid = {gid: i for i, community in enumerate(communities) for gid in community}
    if len(cluster_by_gid) != len(nodes):
        raise DataError("clustering lost nodes")
    seed_by_gid = {int(r.gid): bool(r.is_seed) for r in nodes.itertuples(index=False)}
    depth_by_gid = {int(r.gid): int(r.depth) for r in nodes.itertuples(index=False)}
    betweenness = nx.betweenness_centrality(graph, normalized=True, weight=None)
    reach = {gid: 0 for gid in graph}
    shortest_depth: dict[int, int] = {}
    for seed in sorted(g for g, is_seed in seed_by_gid.items() if is_seed):
        paths = nx.single_source_shortest_path_length(graph, seed, cutoff=4)
        for gid, distance in paths.items():
            shortest_depth[gid] = min(shortest_depth.get(gid, 99), distance)
            if gid != seed:
                reach[gid] += 1
    if any(shortest_depth.get(gid) != depth_by_gid[gid] for gid in graph):
        raise DataError("nodes.depth disagrees with directed seed reach <=4")
    in_dates: dict[int, set[int]] = defaultdict(set)
    last_in_day: dict[int, int] = {}
    for row in tx.itertuples(index=False):
        dst = int(row.dst)
        day = int(row.date.day)
        in_dates[dst].add(day)
        last_in_day[dst] = max(last_in_day.get(dst, 0), day)
    raw: dict[int, dict] = {}
    cross_cents = {gid: 0 for gid in graph}
    internal_cents = [0] * len(communities)
    for src, dst, attrs in graph.edges(data=True):
        if cluster_by_gid[src] == cluster_by_gid[dst]:
            internal_cents[cluster_by_gid[src]] += attrs["cents"]
        else:
            cross_cents[src] += attrs["cents"]
            cross_cents[dst] += attrs["cents"]
    for gid in graph:
        in_cents = int(graph.in_degree(gid, weight="cents"))
        out_cents = int(graph.out_degree(gid, weight="cents"))
        in_tx = int(graph.in_degree(gid, weight="n_tx"))
        out_tx = int(graph.out_degree(gid, weight="n_tx"))
        ratio = out_cents / in_cents if in_cents > 0 else None
        raw[gid] = {
            "in_degree": int(graph.in_degree(gid)), "out_degree": int(graph.out_degree(gid)),
            "in_cents": in_cents, "out_cents": out_cents, "in_tx": in_tx, "out_tx": out_tx,
            "pass_through": ratio,
            "direct_seed_senders": sum(seed_by_gid[src] for src in graph.predecessors(gid)),
            "seed_reach_4": reach[gid], "betweenness": float(betweenness[gid]),
            "cross_cluster_volume": cross_cents[gid] / (in_cents + out_cents) if in_cents + out_cents else 0.0,
            "in_dates": len(in_dates[gid]), "last_in_day": last_in_day.get(gid),
        }
    features = {
        "in_degree": {g: float(m["in_degree"]) for g, m in raw.items()},
        "out_degree": {g: float(m["out_degree"]) for g, m in raw.items()},
        "in_tx": {g: float(m["in_tx"]) for g, m in raw.items()},
        "out_tx": {g: float(m["out_tx"]) for g, m in raw.items()},
        "min_tx": {g: float(min(m["in_tx"], m["out_tx"])) for g, m in raw.items()},
        "direct_seed_senders": {g: float(m["direct_seed_senders"]) for g, m in raw.items()},
        "seed_reach_4": {g: float(m["seed_reach_4"]) for g, m in raw.items()},
        "flow_volume": {g: float(max(m["in_cents"], m["out_cents"])) for g, m in raw.items()},
        "betweenness": {g: m["betweenness"] for g, m in raw.items()},
    }
    p = {name: positive_midrank(values) for name, values in features.items()}
    positive_betweenness = [v for v in betweenness.values() if v > 0]
    coordinator_cutoff = float(np.quantile(positive_betweenness, cfg.COORDINATOR_BETWEENNESS_QUANTILE, method="linear")) if positive_betweenness else None
    profiles: dict[int, dict] = {}
    for gid in graph:
        m = raw[gid]
        depth = depth_by_gid[gid]
        is_seed = seed_by_gid[gid]
        ratio = m["pass_through"]
        eligible: dict[str, float] = {}
        if m["in_degree"] >= cfg.CONSOLIDATOR_MIN_IN_DEGREE:
            eligible["consolidator"] = 0.7 * p["in_degree"][gid] + 0.3 * p["in_tx"][gid]
        if m["out_degree"] >= cfg.DISTRIBUTOR_MIN_OUT_DEGREE:
            eligible["distributor"] = 0.7 * p["out_degree"][gid] + 0.3 * p["out_tx"][gid]
        if (not is_seed and depth < 4 and m["in_cents"] > 0 and m["out_cents"] > 0
                and m["in_tx"] >= cfg.TRANSIT_MIN_TX and m["out_tx"] >= cfg.TRANSIT_MIN_TX
                and ratio is not None and cfg.TRANSIT_RATIO_MIN <= ratio <= cfg.TRANSIT_RATIO_MAX):
            eligible["transit"] = 0.6 * max(0.0, 1 - abs(ratio - 1) / 0.2) + 0.4 * p["min_tx"][gid]
        if (not is_seed and depth < 4 and m["in_cents"] > 0 and ratio is not None
                and ratio <= cfg.TERMINAL_RATIO_MAX and m["in_dates"] >= cfg.TERMINAL_MIN_IN_DATES
                and m["last_in_day"] is not None and m["last_in_day"] <= cfg.TERMINAL_LAST_IN_DAY_MAX):
            eligible["terminal"] = 0.6 * (1 - min(ratio / 0.1, 1)) + 0.4 * p["in_tx"][gid]
        if (coordinator_cutoff is not None and m["in_degree"] > 0 and m["out_degree"] > 0
                and m["seed_reach_4"] >= cfg.COORDINATOR_MIN_SEED_REACH
                and m["betweenness"] >= coordinator_cutoff
                and m["cross_cluster_volume"] >= cfg.COORDINATOR_MIN_CROSS_CLUSTER_VOLUME):
            eligible["coordinator"] = 0.6 * p["betweenness"][gid] + 0.4 * p["seed_reach_4"][gid]
        scored = {role: signal * cfg.ROLE_SUPPORT[role] for role, signal in eligible.items()}
        if scored:
            role = min(scored, key=lambda r: (-scored[r], cfg.ROLE_ORDER.index(r)))
            role_score = min(scored[role], cfg.SINGLE_TX_CAP) if m["in_tx"] + m["out_tx"] == 1 else scored[role]
            secondary = [r for r in cfg.ROLE_ORDER if r in scored and r != role]
            signal = eligible[role]
            support = cfg.ROLE_SUPPORT[role]
        else:
            role = "peripheral"
            role_score = cfg.ISOLATE_SCORE if gid in isolates else cfg.PERIPHERAL_SCORE
            secondary = []
            signal = role_score
            support = 1.0
        priority_parts = {name: weight * p[name][gid] for name, weight in cfg.PRIORITY_WEIGHTS.items()}
        priority = sum(priority_parts.values())
        if not math.isclose(sum(priority_parts.values()), priority, rel_tol=0, abs_tol=1e-9):
            raise DataError("priority component sum mismatch")
        limitations = ["inflow_incomplete", "date_only", "period_censored", "threshold_5000", "intrabank_only"]
        if is_seed:
            limitations.append("seed_inflow_incomplete")
        if depth == 4:
            limitations.append("depth_truncated")
        if gid in isolates:
            limitations.append("isolated_seed")
        if m["out_cents"] > m["in_cents"]:
            limitations.append("outflow_exceeds_observed_inflow")
        if role == "peripheral":
            limitations.append("insufficient_evidence")
        limitations.append("path_not_money_provenance")
        next_checks = ["Запросить полную входящую историю за июль, включая источники вне графа."]
        if depth == 4:
            next_checks.append("Проверить исходящие переводы следующего колена за тот же период.")
        if role == "terminal":
            next_checks.append("Проверить остатки и ненаблюдаемые исходящие операции.")
        if role == "transit":
            next_checks.append("Запросить точное время входящих и исходящих переводов.")
        if gid in isolates:
            next_checks.append("Проверить причину отсутствия наблюдаемых связей: период, порог или канал.")
        rule_id = f"{role}_v0"
        evidence = [
            fact(gid, "role_signal_strength", signal, "ratio", rule_id, "derived", f"Сила признака роли {role}: {signal:.6f}", limitations),
            fact(gid, "role_support_multiplier", support, "ratio", rule_id, "derived", f"Policy-множитель роли: {support:.2f}", limitations),
            fact(gid, "in_degree", m["in_degree"], "count", rule_id, "edges.parquet", f"Наблюдаемых отправителей: {m['in_degree']}", limitations),
            fact(gid, "out_degree", m["out_degree"], "count", rule_id, "edges.parquet", f"Наблюдаемых получателей: {m['out_degree']}", limitations),
        ]
        if m["in_tx"] + m["out_tx"] == 1 and scored:
            evidence.append(fact(gid, "role_score_cap", cfg.SINGLE_TX_CAP, "ratio", rule_id, "derived", "Одна наблюдаемая транзакция ограничивает оценку роли", limitations))
        for name in cfg.PRIORITY_WEIGHTS:
            value = priority_parts[name]
            evidence.append(fact(gid, f"priority_component_{name}", value, "ratio", "priority_v0", "derived", f"Вклад {name}: {value:.9f}", limitations))
        if role == "consolidator":
            short = f"{m['in_degree']} плательщиков, {m['in_tx']} входящих tx, вход {kzt(m['in_cents'])} KZT; признаки консолидации, вход неполон"
        elif role == "distributor":
            short = f"{m['out_degree']} получателей, {m['out_tx']} исходящих tx, выход {kzt(m['out_cents'])} KZT; веер исходящих переводов"
        elif role == "transit":
            short = f"Вход {kzt(m['in_cents'])}, выход {kzt(m['out_cents'])} KZT, r={ratio:.3f}; сходство объёмов, порядок не известен"
        elif role == "terminal":
            short = f"{m['in_degree']} плательщиков, {m['in_dates']} даты входа, последний день {m['last_in_day']}; r={ratio:.3f}, исходящие вне выборки неизвестны"
        elif role == "coordinator":
            short = f"Достижим от {m['seed_reach_4']} seed, betweenness={m['betweenness']:.5f}, межкластерный объём {m['cross_cluster_volume']:.2f}; структурный кандидат"
        else:
            short = f"Недостаточно признаков: вход {m['in_degree']} gid, выход {m['out_degree']} gid, depth={depth}; наблюдение ограничено"
        if len(short) > 200:
            raise DataError(f"role evidence too long for {gid}")
        top_parts = sorted(priority_parts.items(), key=lambda item: (-item[1], item[0]))[:3]
        why = (f"Приоритет {priority:.6f}: крупнейшие вклады " + ", ".join(f"{name}={value:.4f}" for name, value in top_parts)
               + f"; seed-отправителей {m['direct_seed_senders']}, достижим от {m['seed_reach_4']} seed, вход {m['in_degree']} gid, выход {m['out_degree']} gid. Вход неполон.")
        profiles[gid] = {
            "gid": str(gid), "depth": depth, "is_seed": is_seed, "role": role,
            "role_score": role_score, "priority_score": priority,
            "cluster_id": cluster_by_gid[gid], "evidence_text": short, "why": why,
            "metrics": {
                "in_degree": m["in_degree"], "out_degree": m["out_degree"],
                "in_kzt": m["in_cents"] / 100, "out_kzt": m["out_cents"] / 100,
                "in_tx": m["in_tx"], "out_tx": m["out_tx"], "pass_through": ratio,
                "direct_seed_senders": m["direct_seed_senders"],
                "seed_reach_4": m["seed_reach_4"], "betweenness": m["betweenness"],
            },
            "evidence": evidence, "secondary_roles": secondary,
            "limitations": limitations, "next_checks": next_checks,
            "priority_components": priority_parts,
        }
    ranked = sorted(profiles, key=lambda gid: (-profiles[gid]["priority_score"], gid))
    clusters = []
    for cluster_id, community in enumerate(communities):
        members = sorted(community)
        cluster_roles = Counter(profiles[g]["role"] for g in members)
        dominant, dominant_count = sorted(cluster_roles.items(), key=lambda item: (-item[1], item[0]))[0]
        seed_count = sum(seed_by_gid[g] for g in members)
        hypothesis = (f"Гипотеза: {len(members)} узлов, {seed_count} seed; преобладает {dominant} ({dominant_count}); "
                      f"внутренние переводы {kzt(internal_cents[cluster_id])} KZT.")
        if len(members) == 1 and members[0] in isolates:
            hypothesis = "Гипотеза: изолированный seed; 0 наблюдаемых связей."
        clusters.append({
            "cluster_id": cluster_id, "n_nodes": len(members), "n_seed": seed_count,
            "sum_kzt_internal": kzt(internal_cents[cluster_id]),
            "top_gids": ";".join(str(g) for g in sorted(members, key=lambda g: (-profiles[g]["priority_score"], g))[:3]),
            "hypothesis": hypothesis,
        })
    top = [profiles[gid] for gid in ranked[:max(20, min(100, len(ranked)))]]
    if len(top) < 20:
        raise DataError("top_nodes requires at least 20 unique nodes")
    result = AnalysisResult(profiles, clusters, top, len(nodes), len(edges), len(tx), len(components), len(isolates))
    validate_result(result, nodes)
    return result


def validate_result(result: AnalysisResult, nodes: pd.DataFrame) -> None:
    if set(result.profiles) != set(int(g) for g in nodes.gid):
        raise DataError("profiles do not cover every input gid")
    if sum(c["n_nodes"] for c in result.clusters) != len(nodes):
        raise DataError("cluster sizes do not cover nodes")
    if sum(c["n_seed"] for c in result.clusters) != int(nodes.is_seed.sum()):
        raise DataError("cluster seed counts disagree")
    ids = {c["cluster_id"] for c in result.clusters}
    for gid, profile in result.profiles.items():
        if profile["cluster_id"] not in ids:
            raise DataError(f"missing cluster for {gid}")
        if profile["role"] not in (*cfg.ROLE_ORDER, "peripheral"):
            raise DataError(f"invalid role for {gid}")
        if any(not math.isfinite(profile[x]) or not 0 <= profile[x] <= 1 for x in ("role_score", "priority_score")):
            raise DataError(f"invalid score for {gid}")
        if not profile["evidence_text"] or len(profile["evidence_text"]) > 200 or not any(ch.isdigit() for ch in profile["evidence_text"]):
            raise DataError(f"invalid short evidence for {gid}")
        if profile["depth"] == 4 and profile["role"] == "terminal":
            raise DataError(f"terminal assigned on depth=4 for {gid}")
        values = [e["value"] for e in profile["evidence"] if e["rule_id"] == "priority_v0"]
        if len(values) != 6 or not math.isclose(sum(values), profile["priority_score"], rel_tol=0, abs_tol=1e-9):
            raise DataError(f"priority evidence mismatch for {gid}")
    top_gids = [int(p["gid"]) for p in result.top]
    if len(top_gids) != len(set(top_gids)) or top_gids != sorted(top_gids, key=lambda gid: (-result.profiles[gid]["priority_score"], gid)):
        raise DataError("top list unsorted or repeated")


def export_csv(result: AnalysisResult, out_dir: Path) -> None:
    rows = {
        "nodes_roles.csv": [
            {"gid": str(gid), "role": p["role"], "role_score": f"{p['role_score']:.12f}",
             "cluster_id": p["cluster_id"], "priority_score": f"{p['priority_score']:.12f}",
             "evidence": p["evidence_text"]}
            for gid, p in sorted(result.profiles.items())
        ],
        "clusters.csv": result.clusters,
        "top_nodes.csv": [
            {"rank": rank, "gid": p["gid"], "role": p["role"],
             "priority_score": f"{p['priority_score']:.12f}", "why": p["why"]}
            for rank, p in enumerate(result.top, 1)
        ],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="csv-stage-", dir=out_dir) as stage_name:
        stage = Path(stage_name)
        for name, data in rows.items():
            with (stage / name).open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS[name], extrasaction="ignore", lineterminator="\n")
                writer.writeheader()
                writer.writerows(data)
        for name in CSV_COLUMNS:
            os.replace(stage / name, out_dir / name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate validated HackAlem CSV exports from three Parquet files")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="directory containing nodes, edges, transactions Parquet")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output CSV directory")
    args = parser.parse_args()
    started = time.perf_counter()
    try:
        nodes, edges, tx = load_and_validate(args.data)
        result = analyze(nodes, edges, tx)
        export_csv(result, args.out)
        from .snapshot import export_snapshot
        export_snapshot(result, nodes, edges, args.data, args.out)
    except DataError as exc:
        parser.exit(2, f"Input/analysis error: {exc}\n")
    elapsed = time.perf_counter() - started
    print(json.dumps({
        "rules_version": cfg.RULES_VERSION, "n_nodes": result.n_nodes,
        "n_edges": result.n_edges, "n_transactions": result.n_transactions,
        "n_components": result.n_components, "n_isolates": result.n_isolates,
        "n_clusters": len(result.clusters),
        "roles": dict(sorted(Counter(p["role"] for p in result.profiles.values()).items())),
        "elapsed_seconds": round(elapsed, 3),
        "outputs": [str(args.out / name) for name in CSV_COLUMNS] + [str(args.out / "snapshot.json")],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
