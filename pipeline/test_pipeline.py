"""Semantic and integration checks for the real three-file case dataset."""

import csv
import math
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from .run import DEFAULT_DATA, DataError, analyze, export_csv, load_and_validate, positive_midrank
from . import config, snapshot


class PipelineTests(unittest.TestCase):
    def test_positive_midrank(self):
        actual = positive_midrank({1: 0.0, 2: 10.0, 3: 10.0, 4: 20.0})
        self.assertEqual(actual, {1: 0.0, 2: 1 / 3, 3: 1 / 3, 4: 5 / 6})
        self.assertEqual(positive_midrank({1: 0.0, 2: 8.0}), {1: 0.0, 2: 0.5})

    def test_snapshot_identity_normalizes_only_source_line_endings(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for name in ("nodes", "edges", "transactions"):
                (folder / f"{name}.parquet").write_bytes(b"binary-input\nunchanged")
            with patch.object(config, "__file__", str(folder / "config.py")), \
                    patch.object(snapshot, "__file__", str(folder / "snapshot.py")):
                for name in ("config", "run"):
                    (folder / f"{name}.py").write_bytes(b"# source\nVALUE = 1\n")
                baseline = snapshot._snapshot_id(folder)
                for name in ("config", "run"):
                    (folder / f"{name}.py").write_bytes(b"# source\r\nVALUE = 1\r\n")
                self.assertEqual(snapshot._snapshot_id(folder), baseline)
                (folder / "run.py").write_bytes(b"# source\r\nVALUE = 2\r\n")
                self.assertNotEqual(snapshot._snapshot_id(folder), baseline)
                (folder / "run.py").write_bytes(b"# source\r\nVALUE = 1\r\n")
                # Binary input is never normalized, including embedded newlines.
                (folder / "nodes.parquet").write_bytes(b"binary-input\r\nunchanged")
                self.assertNotEqual(snapshot._snapshot_id(folder), baseline)

    def test_rejects_transaction_aggregate_mismatch(self):
        nodes, edges, tx = load_and_validate(DEFAULT_DATA)
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            nodes.to_parquet(folder / "nodes.parquet", index=False)
            tx.drop(columns="cents").to_parquet(folder / "transactions.parquet", index=False)
            bad_edges = edges.drop(columns="cents").copy()
            for field in ("n_tx", "sum_kzt"):
                with self.subTest(field=field):
                    corrupted = bad_edges.copy()
                    corrupted.loc[0, field] += 1
                    corrupted.to_parquet(folder / "edges.parquet", index=False)
                    with self.assertRaisesRegex(DataError, "sum or n_tx mismatch"):
                        load_and_validate(folder)

    def test_real_case_csv_invariants(self):
        start = time.perf_counter()
        nodes, edges, tx = load_and_validate(DEFAULT_DATA)
        result = analyze(nodes, edges, tx)
        self.assertEqual((result.n_nodes, result.n_edges, result.n_transactions), (2248, 3119, 4840))
        self.assertEqual((result.n_components, result.n_isolates), (35, 19))
        self.assertEqual(len(result.clusters), 105)
        self.assertEqual(sum(c["n_seed"] for c in result.clusters), 81)
        self.assertEqual(int(tx.duplicated(["src", "dst", "date", "sum_kzt"]).sum()), 97)
        self.assertEqual(int(tx.cents.sum()), 36589001201)
        self.assertEqual(int(edges.n_tx.sum()), len(tx))
        internal_cents = {cluster["cluster_id"]: 0 for cluster in result.clusters}
        for edge in edges.itertuples(index=False):
            source_cluster = result.profiles[int(edge.src)]["cluster_id"]
            if source_cluster == result.profiles[int(edge.dst)]["cluster_id"]:
                internal_cents[source_cluster] += int(edge.cents)
        from .run import cents
        for cluster in result.clusters:
            self.assertEqual(cents(cluster["sum_kzt_internal"]), internal_cents[cluster["cluster_id"]])
        self.assertEqual(sum(1 for p in result.profiles.values() if p["role"] == "terminal" and p["depth"] == 4), 0)
        isolated = [p for p in result.profiles.values() if p["metrics"]["in_degree"] == p["metrics"]["out_degree"] == 0]
        self.assertEqual(len(isolated), 19)
        self.assertTrue(all(p["is_seed"] and p["role"] == "peripheral" and p["role_score"] == 0.05
                            and p["priority_score"] == 0 and "isolated_seed" in p["limitations"] for p in isolated))
        self.assertTrue(all("depth_truncated" in p["limitations"] for p in result.profiles.values() if p["depth"] == 4))
        self.assertTrue(all("outflow_exceeds_observed_inflow" in p["limitations"]
                            for p in result.profiles.values()
                            if p["metrics"]["out_kzt"] > p["metrics"]["in_kzt"]))
        for profile in result.profiles.values():
            values = [e["value"] for e in profile["evidence"] if e["rule_id"] == "priority_v0"]
            self.assertEqual(len(values), 6)
            self.assertTrue(math.isclose(sum(values), profile["priority_score"], abs_tol=1e-9))
            self.assertTrue(math.isfinite(profile["role_score"]))
            self.assertTrue(math.isfinite(profile["priority_score"]))
            facts = {fact["metric"]: fact for fact in profile["evidence"] if fact["rule_id"] != "priority_v0"}
            self.assertEqual(len(facts), len(profile["evidence"]) - 6)
            for metric in ("in_tx", "out_tx", "in_kzt", "out_kzt", "pass_through", "seed_reach_4", "betweenness"):
                if metric in facts:
                    self.assertEqual(facts[metric]["value"], profile["metrics"][metric])
            if profile["role"] == "terminal":
                incoming = tx.loc[tx.dst == int(profile["gid"]), "date"]
                self.assertEqual(facts["in_dates"]["value"], incoming.nunique())
                self.assertEqual(facts["last_in_day"]["value"], incoming.max().day)
                self.assertEqual(facts["in_dates"]["source"], "transactions.parquet")
                self.assertGreaterEqual(facts["in_dates"]["value"], 2)
                self.assertLessEqual(facts["last_in_day"]["value"], 29)
            elif profile["role"] == "coordinator":
                self.assertGreaterEqual(facts["cross_cluster_volume"]["value"], 0.2)
                self.assertGreaterEqual(facts["betweenness"]["value"], facts["coordinator_betweenness_cutoff"]["value"])
            elif profile["role"] == "peripheral":
                self.assertEqual(facts["depth"]["value"], profile["depth"])
        with tempfile.TemporaryDirectory() as tmp:
            export_csv(result, Path(tmp))
            with (Path(tmp) / "nodes_roles.csv").open(encoding="utf-8", newline="") as handle:
                roles = list(csv.DictReader(handle))
            with (Path(tmp) / "clusters.csv").open(encoding="utf-8", newline="") as handle:
                clusters = list(csv.DictReader(handle))
            with (Path(tmp) / "top_nodes.csv").open(encoding="utf-8", newline="") as handle:
                top = list(csv.DictReader(handle))
            self.assertEqual(len(roles), 2248)
            self.assertEqual({row["gid"] for row in roles}, {str(int(g)) for g in nodes.gid})
            self.assertEqual(len(clusters), 105)
            self.assertEqual(sum(int(row["n_nodes"]) for row in clusters), 2248)
            self.assertEqual(sum(int(row["n_seed"]) for row in clusters), 81)
            by_gid = {row["gid"]: row for row in roles}
            self.assertEqual(len(top), 100)
            self.assertEqual(len({row["gid"] for row in top}), len(top))
            for rank, row in enumerate(top, 1):
                self.assertEqual(int(row["rank"]), rank)
                self.assertEqual(row["role"], by_gid[row["gid"]]["role"])
                self.assertEqual(row["priority_score"], by_gid[row["gid"]]["priority_score"])
                self.assertTrue(row["why"])
            self.assertEqual(top, sorted(top, key=lambda row: (-float(row["priority_score"]), int(row["gid"]))))
            for row in roles:
                self.assertGreater(int(row["gid"]), 2**53)
                self.assertNotIn("e+", row["gid"].lower())
                self.assertIn(row["role"], {"consolidator", "transit", "distributor", "terminal", "coordinator", "peripheral"})
                self.assertTrue(all(0 <= float(row[key]) <= 1 for key in ("role_score", "priority_score")))
                self.assertTrue(0 < len(row["evidence"]) <= 200)
                self.assertTrue(any(ch.isdigit() for ch in row["evidence"]))
                self.assertIn(int(row["cluster_id"]), {int(c["cluster_id"]) for c in clusters})
        self.assertLess(time.perf_counter() - start, 300)


if __name__ == "__main__":
    unittest.main()
