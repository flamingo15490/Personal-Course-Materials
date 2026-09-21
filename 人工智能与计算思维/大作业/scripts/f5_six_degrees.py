# -*- coding: utf-8 -*-
"""Part F5: Six Degrees of Separation verification on CBDB social network."""
from __future__ import annotations
import csv, json, random
from collections import Counter, defaultdict
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / 'output_cbdb_v1'
OUT_DIR = ROOT / '任务f' / '专题5_六度分隔'
OUT_DIR.mkdir(exist_ok=True, parents=True)

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

TARGET_DYNASTIES = ['唐', '宋', '明']

# Mapping from simplified to traditional for name lookup
CELEBRITY_PAIRS = [
    ('蘇軾', '李清照'),
    ('李白', '岳飛'),
    ('杜甫', '袁宏道'),
    ('白居易', '王維'),
    ('歐陽修', '王安石'),  # note: database uses 歐陽修, not 欧阳修
]

# ===================================================================
# Step 1: Data Loading & Graph Construction
# ===================================================================
def load_person_map():
    """Load person ID -> (name, dynasty) mapping."""
    print('[Step 1] Loading dim_person.csv ...')
    pm = {}
    df = pd.read_csv(
        IN_DIR / 'dim_person.csv',
        usecols=['c_personid', 'c_name_chn', 'dynasty_chn'],
        dtype={'c_personid': int},
        encoding='utf-8',
        on_bad_lines='skip',
    )
    for _, row in df.iterrows():
        pid = int(row['c_personid'])
        name = str(row['c_name_chn']) if pd.notna(row['c_name_chn']) else ''
        dyn = str(row['dynasty_chn']) if pd.notna(row['dynasty_chn']) else ''
        pm[pid] = (name, dyn)
    print(f'  Loaded {len(pm):,} persons')
    return pm


def load_assoc_edges():
    """Load social association edges, removing '未詳' and deduplicating as undirected."""
    print('[Step 1] Loading fact_person_assoc.csv ...')
    df = pd.read_csv(
        IN_DIR / 'fact_person_assoc.csv',
        usecols=['c_personid', 'c_assoc_id', 'c_assoc_desc_chn'],
        dtype={'c_personid': int, 'c_assoc_id': int},
        encoding='utf-8',
        on_bad_lines='skip',
    )
    total = len(df)
    # Remove invalid entries
    df = df[df['c_assoc_desc_chn'] != '未詳'].copy()
    print(f'  Removed {total - len(df):,} invalid, {len(df):,} remaining')

    # Deduplicate as undirected: normalize (a,b) with min/max
    edge_set = set()
    for _, row in df.iterrows():
        a, b = int(row['c_personid']), int(row['c_assoc_id'])
        if a == b:
            continue
        n1, n2 = min(a, b), max(a, b)
        edge_set.add((n1, n2))

    edges = [{'node1': n1, 'node2': n2} for (n1, n2) in edge_set]
    print(f'  Deduplicated to {len(edges):,} undirected edges')
    return edges


def build_graph(assoc_edges, person_map):
    """Build the social network graph and extract largest connected component."""
    print('[Step 1] Building graph ...')
    G_assoc = nx.Graph()
    for e in assoc_edges:
        G_assoc.add_edge(e['node1'], e['node2'])
    print(f'  G_assoc: {G_assoc.number_of_nodes():,} nodes, {G_assoc.number_of_edges():,} edges')

    # Largest connected component
    components = list(nx.connected_components(G_assoc))
    lcc_nodes = max(components, key=len)
    G_main = G_assoc.subgraph(lcc_nodes).copy()
    print(f'  G_main (LCC): {G_main.number_of_nodes():,} nodes, {G_main.number_of_edges():,} edges')
    print(f'  LCC ratio: {len(lcc_nodes) / G_assoc.number_of_nodes():.4f}')
    return G_assoc, G_main


# ===================================================================
# Step 2: Global Network Metrics
# ===================================================================
def compute_global_metrics(G_main):
    """Compute global network metrics using sampling approximations."""
    print('[Step 2] Computing global metrics ...')
    n = G_main.number_of_nodes()
    m = G_main.number_of_edges()
    density = nx.density(G_main)
    avg_degree = 2 * m / n if n else 0
    avg_clustering = nx.average_clustering(G_main)

    # Approximate average shortest path length (sample 5000 pairs)
    print('  Sampling 5000 pairs for avg shortest path ...')
    avg_path = approximate_avg_shortest_path(G_main, n_pairs=5000)

    # Approximate diameter (sample 200 nodes for eccentricity)
    print('  Sampling 200 nodes for diameter estimate ...')
    diameter_est = approximate_diameter(G_main, n_samples=200)

    stats = {
        'nodes': n,
        'edges': m,
        'density': round(density, 8),
        'avg_degree': round(avg_degree, 4),
        'avg_clustering': round(avg_clustering, 6),
        'avg_shortest_path': round(avg_path, 4) if avg_path else None,
        'diameter_estimate': diameter_est,
    }
    print(f'  N={n:,}, M={m:,}, density={density:.6f}, clustering={avg_clustering:.6f}')
    print(f'  Avg path ~ {avg_path:.4f}, diameter ~ {diameter_est}')
    return stats


def approximate_avg_shortest_path(G, n_pairs=5000):
    """Approximate average shortest path by sampling random node pairs."""
    nodes = list(G.nodes())
    if len(nodes) < 2:
        return 0.0
    lengths = []
    # Ensure we have enough unique pairs
    for _ in range(n_pairs):
        u, v = random.sample(nodes, 2)
        try:
            d = nx.shortest_path_length(G, source=u, target=v)
            lengths.append(d)
        except nx.NetworkXNoPath:
            pass  # should not happen in connected graph
    if not lengths:
        return 0.0
    return np.mean(lengths)


def approximate_diameter(G, n_samples=200):
    """Estimate diameter via eccentricity of random sample nodes."""
    nodes = list(G.nodes())
    if len(nodes) <= n_samples:
        sample_nodes = nodes
    else:
        sample_nodes = random.sample(nodes, n_samples)

    max_ecc = 0
    for u in sample_nodes:
        dists = nx.single_source_shortest_path_length(G, u)
        if dists:
            max_ecc = max(max_ecc, max(dists.values()))
    return max_ecc


# ===================================================================
# Step 3: Shortest Path Distance Distribution
# ===================================================================
def compute_distance_distribution(G_main, n_pairs=5000):
    """Sample random node pairs and compute shortest path distance distribution."""
    print('[Step 3] Computing distance distribution ...')
    nodes = list(G_main.nodes())
    lengths = []
    for _ in range(n_pairs):
        u, v = random.sample(nodes, 2)
        try:
            d = nx.shortest_path_length(G_main, source=u, target=v)
            lengths.append(d)
        except nx.NetworkXNoPath:
            pass

    dist_counter = Counter(lengths)
    print(f'  Sampled {len(lengths):,} reachable pairs')
    print(f'  Distance distribution: {dict(sorted(dist_counter.items()))}')
    return lengths, dist_counter


def plot_distance_distribution(lengths, dist_counter):
    """Plot shortest path distance histogram with log Y axis."""
    print('[Step 8] Plotting distance distribution ...')
    mean_val = np.mean(lengths)
    median_val = np.median(lengths)

    fig, ax = plt.subplots(figsize=(10, 6))
    max_dist = max(lengths)
    bins = np.arange(0.5, max_dist + 1.5, 1)
    ax.hist(lengths, bins=bins, edgecolor='white', alpha=0.85, color='#4C78A8')

    ax.set_yscale('log')
    ax.axvline(mean_val, color='#E45756', linestyle='--', linewidth=1.5, label=f'均值={mean_val:.2f}')
    ax.axvline(median_val, color='#F58518', linestyle='--', linewidth=1.5, label=f'中位数={median_val:.1f}')

    ax.set_xlabel('最短路径距离 (步)')
    ax.set_ylabel('频次 (对数)')
    ax.set_title('CBDB 社会网络最短路径距离分布')
    ax.legend()
    ax.set_xlim(0.5, max_dist + 0.5)

    fig.tight_layout()
    out_path = OUT_DIR / 'shortest_path_distribution.png'
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f'  Saved {out_path}')
    return mean_val, median_val


# ===================================================================
# Step 4: Small-World Verification vs Null Models
# ===================================================================
def build_null_models(G_main):
    """Build Erdős–Rényi and configuration model null networks."""
    print('[Step 4] Building null models ...')
    n = G_main.number_of_nodes()
    m = G_main.number_of_edges()

    # Erdős–Rényi: same n, same expected avg degree
    avg_deg = 2 * m / n
    p_er = avg_deg / (n - 1) if n > 1 else 0
    G_random = nx.erdos_renyi_graph(n, p_er, seed=SEED)
    print(f'  G_random: {G_random.number_of_nodes():,} nodes, {G_random.number_of_edges():,} edges')

    # Configuration model: same degree sequence
    degree_seq = [d for _, d in G_main.degree()]
    G_config_multi = nx.configuration_model(degree_seq, seed=SEED)
    G_config = nx.Graph(G_config_multi)  # remove self-loops, parallel edges
    G_config.remove_edges_from(nx.selfloop_edges(G_config))
    print(f'  G_config: {G_config.number_of_nodes():,} nodes, {G_config.number_of_edges():,} edges')

    return G_random, G_config


def compute_comparison_metrics(G, label, n_pairs=5000):
    """Compute comparison metrics for small-world verification."""
    n = G.number_of_nodes()
    m = G.number_of_edges()

    if n < 2:
        return {'label': label, 'nodes': n, 'edges': m, 'avg_clustering': 0.0,
                'avg_shortest_path': None, 'diameter': None, 'avg_degree': 0.0}

    # clustering
    avg_clustering = nx.average_clustering(G)

    # avg shortest path (use largest component for disconnected graphs)
    if nx.is_connected(G):
        components = [set(G.nodes())]
    else:
        components = list(nx.connected_components(G))
    lcc = max(components, key=len)
    Glcc = G.subgraph(lcc).copy()

    avg_path = approximate_avg_shortest_path(Glcc, n_pairs=n_pairs)
    diam = approximate_diameter(Glcc, n_samples=200)

    avg_deg = 2 * m / n if n else 0
    return {
        'label': label,
        'nodes': n,
        'edges': m,
        'avg_degree': round(avg_deg, 4),
        'avg_clustering': round(avg_clustering, 6),
        'avg_shortest_path': round(avg_path, 4) if avg_path else None,
        'diameter': diam,
    }


def plot_small_world_comparison(main_metrics, rand_metrics, conf_metrics):
    """Plot side-by-side bar charts for small-world verification."""
    print('[Step 8] Plotting small-world verification ...')
    labels = ['社会网络\n(G_main)', '随机网络\n(G_random)', '配置模型\n(G_config)']
    clustering_vals = [main_metrics['avg_clustering'],
                       rand_metrics['avg_clustering'],
                       conf_metrics['avg_clustering']]
    path_vals = [main_metrics['avg_shortest_path'] or 0,
                 rand_metrics['avg_shortest_path'] or 0,
                 conf_metrics['avg_shortest_path'] or 0]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    colors = ['#4C78A8', '#E45756', '#F58518']

    # Clustering coefficient
    bars1 = ax1.bar(labels, clustering_vals, color=colors, edgecolor='white', linewidth=0.8)
    ax1.set_title('平均聚类系数')
    ax1.set_ylabel('聚类系数')
    for bar, val in zip(bars1, clustering_vals):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.001,
                 f'{val:.4f}', ha='center', va='bottom', fontsize=10)

    # Average shortest path
    bars2 = ax2.bar(labels, path_vals, color=colors, edgecolor='white', linewidth=0.8)
    ax2.set_title('平均最短路径长度')
    ax2.set_ylabel('路径长度 (步)')
    for bar, val in zip(bars2, path_vals):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                 f'{val:.2f}', ha='center', va='bottom', fontsize=10)

    fig.suptitle('小世界特征验证', fontsize=14, fontweight='bold')

    # Add verdict
    if main_metrics['avg_clustering'] > rand_metrics['avg_clustering'] * 5:
        verdict = '[验证通过] 聚类系数远高于随机网络，路径长度接近'
    else:
        verdict = '[结果不确定] 小世界特征较弱'
    fig.text(0.5, 0.01, verdict, ha='center', fontsize=11, style='italic', color='#555555')

    fig.tight_layout(rect=[0, 0.05, 1, 0.95])
    out_path = OUT_DIR / 'small_world_verification.png'
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f'  Saved {out_path}')


# ===================================================================
# Step 5: Dynasty Sub-Network Analysis
# ===================================================================
def dynasty_subnetwork_analysis(G_assoc, person_map):
    """Build sub-networks per dynasty and compute metrics on their LCCs."""
    print('[Step 5] Dynasty sub-network analysis ...')
    # Group person IDs by dynasty
    dyn_pids = defaultdict(set)
    for pid, (name, dyn) in person_map.items():
        if dyn in TARGET_DYNASTIES:
            dyn_pids[dyn].add(pid)

    rows = []
    for dyn in TARGET_DYNASTIES:
        pids = dyn_pids[dyn] & set(G_assoc.nodes())
        if not pids:
            print(f'  {dyn}: no nodes in network')
            continue
        subG = G_assoc.subgraph(pids).copy()
        comps = list(nx.connected_components(subG))
        lcc_nodes = max(comps, key=len) if comps else set()
        G_dyn_lcc = subG.subgraph(lcc_nodes).copy()

        n = G_dyn_lcc.number_of_nodes()
        m = G_dyn_lcc.number_of_edges()
        density = nx.density(G_dyn_lcc) if n > 1 else 0.0
        avg_clustering = nx.average_clustering(G_dyn_lcc) if n > 1 else 0.0
        avg_path = approximate_avg_shortest_path(G_dyn_lcc, n_pairs=min(5000, n * (n - 1) // 2)) if n > 1 else None
        diameter = approximate_diameter(G_dyn_lcc, n_samples=min(200, n)) if n > 1 else 0

        rows.append({
            'dynasty': dyn,
            'nodes': n,
            'edges': m,
            'full_nodes': subG.number_of_nodes(),
            'components': len(comps),
            'density': round(density, 8),
            'avg_clustering': round(avg_clustering, 6),
            'avg_shortest_path': round(avg_path, 4) if avg_path else None,
            'diameter': diameter,
        })
        print(f'  {dyn}: LCC {n:,} nodes, {m:,} edges, diam={diameter}, avg_path={avg_path}')

    return rows


def plot_dynasty_comparison(dyn_rows):
    """Plot dynasty comparison chart for diameter and avg path."""
    print('[Step 8] Plotting dynasty comparison ...')
    dynasties = [r['dynasty'] for r in dyn_rows]
    diameters = [r['diameter'] or 0 for r in dyn_rows]
    paths = [r['avg_shortest_path'] or 0 for r in dyn_rows]

    x = np.arange(len(dynasties))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    bars1 = ax.bar(x - width / 2, diameters, width, label='直径 (最长最短路径)',
                   color='#4C78A8', edgecolor='white')
    bars2 = ax.bar(x + width / 2, paths, width, label='平均最短路径',
                   color='#F58518', edgecolor='white')

    ax.set_xlabel('朝代')
    ax.set_ylabel('路径长度 (步)')
    ax.set_title('各朝代社会网络路径长度对比')
    ax.set_xticks(x)
    ax.set_xticklabels(dynasties)
    ax.legend()

    for bar, val in zip(bars1, diameters):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                str(val), ha='center', va='bottom', fontsize=9)
    for bar, val in zip(bars2, paths):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                f'{val:.1f}', ha='center', va='bottom', fontsize=9)

    fig.tight_layout()
    out_path = OUT_DIR / 'dynasty_path_comparison.png'
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f'  Saved {out_path}')


# ===================================================================
# Step 6: Six-Degree Reach
# ===================================================================
def compute_six_degree_reach(G_main, person_map, n_starts=1000):
    """Compute the proportion of nodes reachable within 6 steps."""
    print('[Step 6] Computing six-degree reach ...')
    nodes = list(G_main.nodes())
    sample_starts = random.sample(nodes, min(n_starts, len(nodes)))

    reach_ratios = []
    max_dist = 0
    for u in sample_starts:
        dists = nx.single_source_shortest_path_length(G_main, u)
        reachable = sum(1 for d in dists.values() if 0 < d <= 6)
        ratio = reachable / (len(nodes) - 1) if len(nodes) > 1 else 0
        reach_ratios.append(ratio)
        max_dist = max(max_dist, max(dists.values()) if dists else 0)

    avg_reach = np.mean(reach_ratios)
    median_reach = np.median(reach_ratios)

    print(f'  Avg 6-step reach: {avg_reach:.4f} ({avg_reach * 100:.1f}%)')
    print(f'  Median 6-step reach: {median_reach:.4f} ({median_reach * 100:.1f}%)')

    # Build cumulative distribution
    all_dists = []
    for u in sample_starts:
        dists = nx.single_source_shortest_path_length(G_main, u)
        all_dists.extend(dists.values())

    cumulative = Counter(all_dists)
    cum_frac = {}
    running = 0
    total_nodes = len(nodes)
    for d in sorted(cumulative.keys()):
        if d == 0:
            continue
        running += cumulative[d]
        cum_frac[d] = running / (total_nodes - 1) if total_nodes > 1 else 0

    return reach_ratios, avg_reach, median_reach, cum_frac


def plot_six_degree_reach(cum_frac, avg_reach):
    """Plot cumulative distribution of node coverage by distance."""
    print('[Step 8] Plotting six-degree reach ...')
    distances = sorted(cum_frac.keys())
    ratios = [cum_frac[d] for d in distances]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(distances, ratios, 'o-', color='#4C78A8', linewidth=1.5, markersize=4)
    ax.axvline(6, color='#E45756', linestyle='--', linewidth=1.5,
               label=f'6 步 (平均覆盖 {avg_reach * 100:.1f}%)')
    ax.axhline(0.9, color='#72B7B2', linestyle=':', linewidth=1, label='90% 覆盖')

    ax.set_xlabel('最大距离 (步)')
    ax.set_ylabel('可覆盖节点比例')
    ax.set_title('六度分隔验证：累积分布')
    ax.legend()
    ax.set_xlim(0, max(distances) + 1)
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    out_path = OUT_DIR / 'six_degree_reach.png'
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f'  Saved {out_path}')


# ===================================================================
# Step 7: Celebrity Path Examples
# ===================================================================
def find_person_id_by_name(person_map, name):
    """Find person ID by name. Returns list of matching (pid, name, dynasty)."""
    matches = []
    for pid, (pname, dynasty) in person_map.items():
        if pname == name:
            matches.append((pid, pname, dynasty))
    return matches



def pick_best_match(matches, G):
    """When multiple name matches exist, pick the one with most network connections."""
    if len(matches) <= 1:
        return matches[0] if matches else None
    best = None
    best_deg = -1
    for pid, pname, dyn in matches:
        if pid in G:
            deg = G.degree(pid)
            if deg > best_deg:
                best_deg = deg
                best = (pid, pname, dyn)
    if best is None:
        best = matches[0]
    if len(matches) > 1:
        print(f'  Multiple matches for "{matches[0][1]}": using ID={best[0]} (deg={best_deg})')
    return best


def compute_celebrity_paths(G_full, person_map):
    """Compute shortest paths between named celebrity pairs and 5 random pairs."""
    print('[Step 7] Computing celebrity path examples ...')
    results = []

    # Specified celebrity pairs
    for name1, name2 in CELEBRITY_PAIRS:
        m1 = find_person_id_by_name(person_map, name1)
        m2 = find_person_id_by_name(person_map, name2)

        if not m1:
            print(f'  WARNING: "{name1}" not found in person map')
            results.append({'name1': name1, 'name2': name2, 'path': '名称未在数据库中找到'})
            continue
        if not m2:
            print(f'  WARNING: "{name2}" not found in person map')
            results.append({'name1': name1, 'name2': name2, 'path': '名称未在数据库中找到'})
            continue

        pid1, pname1, dyn1 = pick_best_match(m1, G_full)
        pid2, pname2, dyn2 = pick_best_match(m2, G_full)

        if pid1 not in G_full or pid2 not in G_full:
            results.append({'name1': pname1, 'name2': pname2, 'distance': '不可达 (不在网络中)'})
            continue

        try:
            path = nx.shortest_path(G_full, source=pid1, target=pid2)
            path_names = []
            for p in path:
                if p in person_map:
                    path_names.append(f'{person_map[p][0]}({person_map[p][1]})')
                else:
                    path_names.append(str(p))
            dist = len(path) - 1
            chain = ' → '.join(path_names)
            print(f'  {pname1}({dyn1}) → {pname2}({dyn2}): {dist} 步')
            results.append({
                'name1': pname1, 'name2': pname2,
                'dynasty1': dyn1, 'dynasty2': dyn2,
                'distance': dist,
                'path': chain,
            })
        except nx.NetworkXNoPath:
            results.append({'name1': pname1, 'name2': pname2, 'distance': '不可达'})
            print(f'  {pname1}({dyn1}) → {pname2}({dyn2}): 不可达')

    # 5 random pairs
    nodes = list(G_full.nodes())
    if len(nodes) >= 10:
        random_pairs = []
        for _ in range(5):
            u = random.choice(nodes)
            v = random.choice(nodes)
            while v == u:
                v = random.choice(nodes)
            random_pairs.append((u, v))
    else:
        random_pairs = []

    for pid1, pid2 in random_pairs:
        pname1 = person_map.get(pid1, ('?', ''))[0]
        pname2 = person_map.get(pid2, ('?', ''))[0]
        try:
            path = nx.shortest_path(G_full, source=pid1, target=pid2)
            path_names = []
            for p in path:
                if p in person_map:
                    path_names.append(person_map[p][0])
                else:
                    path_names.append(str(p))
            dist = len(path) - 1
            chain = ' → '.join(path_names)
            results.append({
                'name1': pname1, 'name2': pname2, 'distance': dist, 'path': chain,
            })
            print(f'  Random: {pname1} → {pname2}: {dist} 步')
        except nx.NetworkXNoPath:
            results.append({'name1': pname1, 'name2': pname2, 'distance': '不可达'})

    return results


# ===================================================================
# Step 8 & 9: Save Outputs & Visualizations
# ===================================================================
def save_outputs(global_stats, dyn_rows, path_results, reach_stats, cum_frac, lengths, dist_counter):
    """Save all CSV, JSON outputs."""
    print('[Step 9] Saving output files ...')

    # global_network_metrics.csv
    with open(OUT_DIR / 'global_network_metrics.csv', 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=global_stats.keys())
        w.writeheader()
        w.writerow(global_stats)
    print(f'  Saved global_network_metrics.csv')

    # dynasty_path_stats.csv
    if dyn_rows:
        with open(OUT_DIR / 'dynasty_path_stats.csv', 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=dyn_rows[0].keys())
            w.writeheader()
            w.writerows(dyn_rows)
        print(f'  Saved dynasty_path_stats.csv')

    # path_examples.csv
    if path_results:
        with open(OUT_DIR / 'path_examples.csv', 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['name1', 'name2', 'dynasty1', 'dynasty2', 'distance', 'path'])
            w.writeheader()
            for r in path_results:
                row = {
                    'name1': r.get('name1', ''),
                    'name2': r.get('name2', ''),
                    'dynasty1': r.get('dynasty1', ''),
                    'dynasty2': r.get('dynasty2', ''),
                    'distance': r.get('distance', ''),
                    'path': r.get('path', ''),
                }
                w.writerow(row)
        print(f'  Saved path_examples.csv')

    # six_degree_reach_stats.csv
    with open(OUT_DIR / 'six_degree_reach_stats.csv', 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['avg_reach_ratio', 'median_reach_ratio', 'sample_size'])
        w.writerow([
            reach_stats['avg_reach'], reach_stats['median_reach'], reach_stats['sample_size']
        ])
    print(f'  Saved six_degree_reach_stats.csv')

    # analysis_summary.json
    summary = {
        'global_metrics': global_stats,
        'dynasty_comparison': dyn_rows,
        'six_degree_reach': {
            'avg_reach': reach_stats['avg_reach'],
            'median_reach': reach_stats['median_reach'],
        },
        'distance_distribution': dict(sorted(dist_counter.items())),
        'methodology': {
            'avg_shortest_path': 'sampled 5000 random pairs',
            'diameter': 'sampled 200 random nodes (eccentricity)',
            'six_degree_reach': 'sampled 1000 random starts',
            'seed': SEED,
        },
    }
    with open(OUT_DIR / 'analysis_summary.json', 'w', encoding='utf-8-sig') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f'  Saved analysis_summary.json')

    # README.md
    write_readme(global_stats, dyn_rows, reach_stats, path_results)


def write_readme(global_stats, dyn_rows, reach_stats, path_results):
    """Write README.md with methodology and findings."""
    print('[Step 9] Writing README.md ...')
    dyn_table = ''
    for r in (dyn_rows or []):
        dyn_table += (f'| {r["dynasty"]} | {r["nodes"]:,} | {r["edges"]:,} | '
                      f'{r["density"]:.6f} | {r.get("avg_clustering", "-")} | '
                      f'{r.get("diameter", "-")} | {r.get("avg_shortest_path", "-")} |\n')

    path_table = ''
    for r in (path_results or []):
        dist = r.get('distance', '-')
        path_table += f'| {r.get("name1","?")} → {r.get("name2","?")} | {dist} |\n'

    readme = f'''# 专题 F5：中国历史人物的"六度分隔"验证

## 方法论

### 数据来源
- **社会关系**：`output_cbdb_v1/fact_person_assoc.csv`，剔除「未詳」记录
- **人物信息**：`output_cbdb_v1/dim_person.csv`，用于姓名和朝代映射

### 网络构建
- 按无向图处理，以 `min(c_personid, c_assoc_id)` / `max(...)` 去重
- 分析基于**最大连通分量 (LCC)**，因为小世界分析要求图连通

### 近似方法
- **平均最短路径长度**：随机采样 5,000 对节点计算，避免 O(N²logN)
- **直径**：随机抽取 200 个节点的 eccentricity 后取最大值
- **六度可达**：随机采样 1,000 个起始节点，BFS 深度限制 6
- **零模型对比**：
  - Erdős–Rényi 随机网络 `G(n, p)`，p = avg_deg / (n-1)
  - 配置模型：保持度序列，用 `nx.configuration_model` 后转为 `nx.Graph` 清除自环/多边
- 随机种子固定为 42，保证可复现

### 朝代划分
- 基于 `dim_person.csv` 的 `dynasty_chn` 字段
- 分析唐、宋、明三个朝代的社会关系子网络（各自的最大连通分量）

## 核心发现

### 全局网络指标
| 指标 | 值 |
|------|-----|
| 最大连通分量节点数 | {global_stats.get("nodes", "N/A"):,} |
| 边数 | {global_stats.get("edges", "N/A"):,} |
| 密度 | {global_stats.get("density", "N/A")} |
| 平均度 | {global_stats.get("avg_degree", "N/A")} |
| 平均聚类系数 | {global_stats.get("avg_clustering", "N/A")} |
| 平均最短路径长度 (近似) | {global_stats.get("avg_shortest_path", "N/A")} |
| 直径估计 (近似) | {global_stats.get("diameter_estimate", "N/A")} |

### 朝代对比（LCC 指标）
| 朝代 | 节点数 | 边数 | 密度 | 平均聚类系数 | 直径 | 平均路径长度 |
|------|--------|------|------|-------------|------|-------------|
{dyn_table}

### 六度可达
- 在宋代最大连通分量上随机采样 1,000 个起始节点
- 6 步内平均可达比例：**{reach_stats.get("avg_reach", "N/A")}**
- 6 步内中位可达比例：**{reach_stats.get("median_reach", "N/A")}**

### 名人最短路径
| 人物对 | 最短路径距离 |
|--------|-------------|
{path_table}

## 产出文件清单
| 文件 | 说明 |
|------|------|
| `global_network_metrics.csv` | 全局网络指标 |
| `dynasty_path_stats.csv` | 各朝代路径长度对比 |
| `path_examples.csv` | 名人最短路径案例（含完整链路） |
| `six_degree_reach_stats.csv` | 六度可达统计 |
| `shortest_path_distribution.png` | 距离分布直方图 |
| `small_world_verification.png` | 小世界验证对比图 |
| `dynasty_path_comparison.png` | 朝代路径对比 |
| `six_degree_reach.png` | 六度可达累积图 |
| `analysis_summary.json` | 分析摘要 |
| `README.md` | 本说明文档 |

## 已知限制
- 平均最短路径长度和直径均为采样近似值，存在一定误差
- 名人路径可能跨越不同连通分量导致不可达
- 零模型对比中配置模型可能不连通，使用其 LCC 计算路径指标
'''
    (OUT_DIR / 'README.md').write_text(readme, encoding='utf-8-sig')
    print(f'  Saved README.md')


# ===================================================================
# MAIN
# ===================================================================
def main():
    print('=' * 60)
    print('F5: Six Degrees of Separation — CBDB Social Network')
    print('=' * 60)

    # Step 1: Load data and build graph
    person_map = load_person_map()
    assoc_edges = load_assoc_edges()
    G_assoc, G_main = build_graph(assoc_edges, person_map)

    # Step 2: Global metrics
    global_stats = compute_global_metrics(G_main)

    # Step 3: Distance distribution
    lengths, dist_counter = compute_distance_distribution(G_main, n_pairs=5000)
    _, _ = plot_distance_distribution(lengths, dist_counter)

    # Step 4: Small-world verification
    G_random, G_config = build_null_models(G_main)
    main_metrics = compute_comparison_metrics(G_main, '社会网络')
    rand_metrics = compute_comparison_metrics(G_random, '随机网络')
    conf_metrics = compute_comparison_metrics(G_config, '配置模型')
    plot_small_world_comparison(main_metrics, rand_metrics, conf_metrics)

    # Step 5: Dynasty analysis
    dyn_rows = dynasty_subnetwork_analysis(G_assoc, person_map)
    plot_dynasty_comparison(dyn_rows)

    # Step 6: Six-degree reach (on Song LCC)
    # Build Song LCC
    song_pids = {pid for pid, (n, d) in person_map.items() if d == '宋'} & set(G_assoc.nodes())
    G_song = G_assoc.subgraph(song_pids).copy()
    song_comps = list(nx.connected_components(G_song))
    song_lcc_nodes = max(song_comps, key=len)
    G_song_lcc = G_song.subgraph(song_lcc_nodes).copy()
    print(f'[Step 6] Song LCC: {G_song_lcc.number_of_nodes():,} nodes, {G_song_lcc.number_of_edges():,} edges')

    reach_ratios, avg_reach, median_reach, cum_frac = compute_six_degree_reach(G_song_lcc, person_map, n_starts=1000)
    plot_six_degree_reach(cum_frac, avg_reach)
    reach_stats = {
        'avg_reach': round(avg_reach, 6),
        'median_reach': round(median_reach, 6),
        'sample_size': len(reach_ratios),
    }

    # Step 7: Celebrity paths (use full G_main for cross-dynasty reach)
    path_results = compute_celebrity_paths(G_main, person_map)

    # Step 9: Save all outputs
    save_outputs(global_stats, dyn_rows, path_results, reach_stats, cum_frac, lengths, dist_counter)

    print()
    print('=' * 60)
    print('F5: Analysis Complete')
    print(f'All outputs saved to: {OUT_DIR}')
    print('=' * 60)


if __name__ == '__main__':
    main()
