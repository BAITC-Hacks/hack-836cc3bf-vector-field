"""Read-only dataset audit for the product red-team review; not a role engine.

Run with Python + pandas, numpy, pyarrow, networkx, scipy installed:
    python analysis/audit_dataset.py
Outputs: analysis/dataset_audit.json and analysis/node_metrics.csv.
"""
from pathlib import Path
import hashlib
import json
import platform
import time
import sys

ROOT = Path(__file__).resolve().parents[1]
# Optional isolated dependencies used by the review environment.
if (ROOT / '.analysis_deps').exists():
    sys.path.insert(0, str(ROOT / '.analysis_deps'))

import numpy as np
import pandas as pd
import networkx as nx
import pyarrow


def main():
    started = time.perf_counter()
    data = ROOT / 'case' / 'data (1)' / 'data'
    tables = {n: pd.read_parquet(data / f'{n}.parquet') for n in ('nodes', 'edges', 'transactions')}
    n, e, t = (tables[x] for x in ('nodes', 'edges', 'transactions'))
    t['date'] = pd.to_datetime(t['date'])
    audit = {'versions': {'python': platform.python_version(), 'pandas': pd.__version__,
                         'networkx': nx.__version__, 'pyarrow': pyarrow.__version__}, 'tables': {}}
    for name, df in tables.items():
        audit['tables'][name] = {
            'rows': len(df), 'dtypes': {c: str(v) for c, v in df.dtypes.items()},
            'nulls': df.isna().sum().to_dict(), 'distinct': df.nunique().to_dict(),
            'duplicate_rows': int(df.duplicated().sum()),
            'sha256': hashlib.sha256((data / f'{name}.parquet').read_bytes()).hexdigest()}
    agg = t.groupby(['src', 'dst']).agg(tx_sum=('sum_kzt', 'sum'), tx_count=('sum_kzt', 'size')).reset_index()
    m = e.merge(agg, on=['src', 'dst'], how='outer', indicator=True)
    audit['integrity'] = {
        'duplicate_gids': int(n.gid.duplicated().sum()),
        'duplicate_edges': int(e.duplicated(['src', 'dst']).sum()),
        'unknown_endpoints': sorted((set(e.src) | set(e.dst)) - set(n.gid)),
        'edge_tx_pair_mismatches': int((m['_merge'] != 'both').sum()),
        'edge_tx_amount_mismatches': int((~np.isclose(m.sum_kzt, m.tx_sum, rtol=0, atol=.01)).sum()),
        'edge_tx_count_mismatches': int((m.n_tx != m.tx_count).sum()),
        'self_loops': int((e.src == e.dst).sum()),
        'nonpositive_tx': int((t.sum_kzt <= 0).sum()),
        'tx_below_5000': int((t.sum_kzt < 5000).sum()),
        'seed_depth_mismatches': int((n.is_seed != (n.depth == 0)).sum())}
    audit['integrity']['gids_above_js_safe_integer'] = int((n.gid > 2**53 - 1).sum())
    audit['integrity']['gids_changed_by_float64_roundtrip'] = sum(int(float(gid)) != gid for gid in n.gid)
    audit['period'] = {'min': str(t.date.min()), 'max': str(t.date.max()),
                       'non_midnight_rows': int((t.date != t.date.dt.normalize()).sum()),
                       'distinct_days': int(t.date.nunique())}
    audit['amounts'] = {'edge_sum_kzt': float(e.sum_kzt.sum()), 'tx_sum_kzt': float(t.sum_kzt.sum()),
                       'tx_quantiles': t.sum_kzt.quantile([0, .25, .5, .75, .9, .95, .99, 1]).to_dict()}
    G = nx.DiGraph()
    G.add_nodes_from(sorted(n.gid.tolist()))
    for r in e.sort_values(['src', 'dst']).itertuples(index=False):
        G.add_edge(r.src, r.dst, sum_kzt=float(r.sum_kzt), n_tx=int(r.n_tx))
    d = n.set_index('gid').copy()
    for col, mapping in [('in_deg', G.in_degree()), ('out_deg', G.out_degree()),
                         ('in_kzt', G.in_degree(weight='sum_kzt')), ('out_kzt', G.out_degree(weight='sum_kzt')),
                         ('in_tx', G.in_degree(weight='n_tx')), ('out_tx', G.out_degree(weight='n_tx'))]:
        d[col] = pd.Series(dict(mapping))
    d['pass_through'] = d.out_kzt / d.in_kzt.replace(0, np.nan)
    d['direct_seed_senders'] = [sum(bool(d.loc[s, 'is_seed']) for s in G.predecessors(g)) for g in d.index]
    d['seed_reach_4'] = 0
    min_depth = {}
    for seed in n.loc[n.is_seed, 'gid']:
        lengths = nx.single_source_shortest_path_length(G, seed, cutoff=4)
        for gid, length in lengths.items():
            min_depth[gid] = min(min_depth.get(gid, 99), length)
            if gid != seed:
                d.loc[gid, 'seed_reach_4'] += 1
    audit['integrity']['depth_shortest_path_mismatches'] = sum(min_depth.get(r.gid, -1) != r.depth for r in n.itertuples())
    audit['by_depth'] = []
    for depth, part in d.groupby('depth'):
        audit['by_depth'].append({'depth': int(depth), 'nodes': len(part),
                                 'no_out': int((part.out_deg == 0).sum()),
                                 'no_in': int((part.in_deg == 0).sum()),
                                 'out_gt_in': int((part.out_kzt > part.in_kzt).sum())})
    comps = sorted(nx.weakly_connected_components(G), key=lambda c: (-len(c), min(c)))
    audit['components'] = [{'n_nodes': len(c), 'n_seed': int(d.loc[list(c), 'is_seed'].sum())} for c in comps]
    isolates = list(nx.isolates(G))
    audit['graph'] = {'nodes': G.number_of_nodes(), 'edges': G.number_of_edges(),
                      'components_including_isolates': len(comps),
                      'components_excluding_isolates': len(comps) - len(isolates),
                      'isolates': len(isolates), 'isolated_seed': int(d.loc[isolates, 'is_seed'].sum()),
                      'seed_no_out': int((d.is_seed & (d.out_deg == 0)).sum()),
                      'seed_only_receiver': int((d.is_seed & (d.out_deg == 0) & (d.in_deg > 0)).sum()),
                      'out_gt_in': int((d.out_kzt > d.in_kzt).sum()),
                      'out_gt_in_with_positive_in': int(((d.out_kzt > d.in_kzt) & (d.in_kzt > 0)).sum()),
                      'out_gt_in_nonseed': int(((~d.is_seed) & (d.out_kzt > d.in_kzt)).sum()),
                      'no_out_depth_lt4': int(((d.out_deg == 0) & (d.depth < 4) & (d.in_deg > 0)).sum()),
                      'pass_through_08_12': int(d.pass_through.between(.8, 1.2).sum()),
                      'in_deg_ge3': int((d.in_deg >= 3).sum()),
                      'out_deg_ge10': int((d.out_deg >= 10).sum()),
                      'nontrivial_scc_sizes': sorted([len(c) for c in nx.strongly_connected_components(G) if len(c) > 1], reverse=True),
                      'reciprocal_pairs': sum(G.has_edge(v, u) for u, v in G.edges if u != v) // 2}
    d['pagerank'] = pd.Series(nx.pagerank(G, weight='sum_kzt'))
    d['betweenness_unweighted'] = pd.Series(nx.betweenness_centrality(G, normalized=True, weight=None))
    UG = nx.Graph()
    UG.add_nodes_from(sorted(G.nodes))
    for u, v, attrs in G.edges(data=True):
        if UG.has_edge(u, v):
            UG[u][v]['weight'] += attrs['sum_kzt']
        else:
            UG.add_edge(u, v, weight=attrs['sum_kzt'])
    audit['louvain_runs'] = []
    partitions = []
    for seed in (0, 42, 123):
        communities = []
        for component in comps:
            if len(component) == 1:
                communities.append(component)
            else:
                communities.extend(nx.community.louvain_communities(UG.subgraph(sorted(component)).copy(), weight='weight', seed=seed, resolution=1))
        communities.sort(key=lambda c: (-len(c), min(c)))
        partitions.append(communities)
        audit['louvain_runs'].append({'seed': seed, 'n_communities': len(communities),
                                      'multi_seed_communities': sum(int(d.loc[list(c), 'is_seed'].sum()) > 1 for c in communities),
                                      'largest_sizes': [len(c) for c in communities[:10]]})
    d['cluster_id_example'] = pd.Series({g: i for i, c in enumerate(partitions[1]) for g in c})
    d['component_id'] = pd.Series({g: i for i, c in enumerate(comps) for g in c})
    audit['top_examples'] = {}
    for metric in ('in_deg', 'out_deg', 'in_kzt', 'pagerank', 'betweenness_unweighted', 'seed_reach_4'):
        audit['top_examples'][metric] = d.sort_values([metric], ascending=False).head(8).reset_index().to_dict(orient='records')
    audit['date_pattern'] = t.groupby('date').agg(n_tx=('sum_kzt', 'size'), sum_kzt=('sum_kzt', 'sum')).reset_index().assign(date=lambda x: x.date.astype(str)).to_dict(orient='records')
    # A date-only co-occurrence signal, NOT attribution of the same money.
    temporal = []
    for gid in d.index[(d.in_deg > 0) & (d.out_deg > 0)]:
        inc = t.loc[t.dst == gid, ['date', 'sum_kzt']]
        out = t.loc[t.src == gid, ['date', 'sum_kzt']]
        in_days = set(inc.date)
        after_days = set(day + pd.Timedelta(days=lag) for day in in_days for lag in (1, 2))
        temporal.append({'gid': int(gid), 'out_on_in_day': int(out.date.isin(in_days).sum()),
                         'out_1_2_days_after_in': int(out.date.isin(after_days).sum()), 'n_out_tx': len(out)})
    audit['temporal_examples'] = sorted(temporal, key=lambda x: -x['out_1_2_days_after_in'])[:10]
    audit['elapsed_seconds'] = round(time.perf_counter() - started, 3)
    outdir = ROOT / 'analysis'
    d.reset_index().to_csv(outdir / 'node_metrics.csv', index=False)
    def convert(x):
        if hasattr(x, 'item'):
            return x.item()
        raise TypeError(type(x).__name__)
    # pandas converts NaN to null before final strict JSON serialization.
    cleaned = json.loads(pd.Series(audit).to_json(force_ascii=False, default_handler=convert))
    (outdir / 'dataset_audit.json').write_text(json.dumps(cleaned, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    summary = {k: v for k, v in audit.items() if k not in ('top_examples', 'date_pattern', 'temporal_examples')}
    print(json.dumps(summary, ensure_ascii=True, indent=2, default=convert))
    print('\nTOP EXAMPLES (computed metrics, not final roles or investigation priorities):')
    for metric, rows in audit['top_examples'].items():
        print(metric, [(r['gid'], r[metric], r['depth'], r['is_seed']) for r in rows])


if __name__ == '__main__':
    main()
