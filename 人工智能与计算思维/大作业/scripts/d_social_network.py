# -*- coding: utf-8 -*-
"""Part D: Social Network Analysis for Chinese Historical Figures."""
from __future__ import annotations
import csv, json, sys, textwrap
from collections import Counter, defaultdict
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / 'output_cbdb_v1'
OUT_DIR = ROOT / '任务d'
EGO_DIR = OUT_DIR / 'ego_pages'
OUT_DIR.mkdir(exist_ok=True)
EGO_DIR.mkdir(exist_ok=True)

ASSOC_CATEGORY_MAP = {
    '文學交往': ['贈詩、文','收到Y的贈詩、文','致書Y','被致書由Y','答Y書','收到Y的答書',
        '為Y所著書作序','書序由Y所作','為Y所著書作跋','書跋由Y所作',
        '為Y所著書題辭','為Y所著書題辭','為Y作傳','傳由Y所作','唱和','同遊'],
    '墓誌傳記': ['為Y作墓誌銘','墓誌銘由Y所作','為Y作行狀','行狀由Y所作','為Y作神道碑','神道碑由Y所作'],
    '師生': ['為Y之學生','學生為Y','為Y之門人','門人為Y','為Y之弟子','弟子為Y'],
    '友人': ['友','同年','同僚','鄰居'],
}
DESC_TO_CATEGORY = {}
for _cat, _dd in ASSOC_CATEGORY_MAP.items():
    for _d in _dd:
        DESC_TO_CATEGORY[_d] = _cat

CATEGORY_COLORS = {'文學交往':'#4C78A8','墓誌傳記':'#72B7B2','師生':'#F58518','友人':'#54A24B','其他':'#B279A2'}
COMMUNITY_COLORS = ['#e6194b','#3cb44b','#ffe119','#4363d8','#f58231','#911eb4','#42d4f4','#f032e6','#bfef45','#fabed4','#469990','#dcbeff','#9A6324','#fffac8','#800000','#aaffc3','#808000','#ffd8b1','#000075','#a9a9a9']
TARGET_DYNASTIES = ['唐','宋','明']
SUSHI_ID = 3767
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei','SimHei','KaiTi']
plt.rcParams['axes.unicode_minus'] = False
# ===================================================================
# Step 1: Data Loading & Cleaning
# ===================================================================
def load_person_map():
    print('[Step 1] Loading dim_person.csv ...')
    pm = {}
    df = pd.read_csv(IN_DIR / 'dim_person.csv',
                     usecols=['c_personid','c_name_chn','dynasty_chn'],
                     dtype={'c_personid':int}, encoding='utf-8', on_bad_lines='skip')
    for _, row in df.iterrows():
        pid = int(row['c_personid'])
        name = str(row['c_name_chn']) if pd.notna(row['c_name_chn']) else ''
        dyn = str(row['dynasty_chn']) if pd.notna(row['dynasty_chn']) else ''
        pm[pid] = (name, dyn)
    print(f'  Loaded {len(pm):,} persons')
    return pm


def load_assoc_edges():
    print('[Step 1] Loading fact_person_assoc.csv ...')
    df = pd.read_csv(IN_DIR / 'fact_person_assoc.csv',
                     usecols=['c_personid','c_assoc_id','c_assoc_desc_chn'],
                     dtype={'c_personid':int,'c_assoc_id':int},
                     encoding='utf-8', on_bad_lines='skip')
    total = len(df)
    df = df[df['c_assoc_desc_chn'] != '未詳'].copy()
    print(f'  Removed {total - len(df)} invalid, {len(df)} remaining')
    edge_map = {}
    for _, row in df.iterrows():
        a, b = int(row['c_personid']), int(row['c_assoc_id'])
        n1, n2 = min(a, b), max(a, b)
        desc = str(row['c_assoc_desc_chn'])
        key = (n1, n2)
        if key not in edge_map:
            edge_map[key] = set()
        edge_map[key].add(desc)
    edges = []
    for (n1, n2), types in edge_map.items():
        cats = set(DESC_TO_CATEGORY.get(t, '其他') for t in types)
        cat = cats.pop() if len(cats) == 1 else next(iter(cats))
        edges.append({'node1':n1,'node2':n2,'category':cat,'detail_types':'|'.join(sorted(types))})
    print(f'  Deduplicated to {len(edges):,} undirected edges')
    return edges


def load_kin_edges():
    print('[Step 1] Loading fact_person_kin.csv ...')
    df = pd.read_csv(IN_DIR / 'fact_person_kin.csv',
                     usecols=['c_personid','c_kin_id','c_kinrel_chn'],
                     dtype={'c_personid':int,'c_kin_id':int},
                     encoding='utf-8', on_bad_lines='skip')
    total = len(df)
    df = df[~df['c_kinrel_chn'].isin(['非可用','未詳'])].copy()
    print(f'  Removed {total - len(df)} invalid, {len(df)} remaining')
    edges = []
    for _, row in df.iterrows():
        edges.append({'source':int(row['c_personid']),'target':int(row['c_kin_id']),'relation':str(row['c_kinrel_chn'])})
    print(f'  {len(edges):,} kinship edges loaded')
    return edges
# ===================================================================
# Step 2-3: Build Graphs & Global Stats
# ===================================================================
def build_graphs(assoc_edges, kin_edges):
    print('[Step 2-3] Building graphs ...')
    G_assoc = nx.Graph()
    for e in assoc_edges:
        G_assoc.add_edge(e['node1'], e['node2'], category=e['category'], detail_types=e['detail_types'])
    G_kin = nx.DiGraph()
    for e in kin_edges:
        G_kin.add_edge(e['source'], e['target'], relation=e['relation'])
    print(f'  G_assoc: {G_assoc.number_of_nodes():,} nodes, {G_assoc.number_of_edges():,} edges')
    print(f'  G_kin:   {G_kin.number_of_nodes():,} nodes, {G_kin.number_of_edges():,} edges')
    return G_assoc, G_kin


def compute_global_stats(G, label, directed=False):
    print(f'[Step 3] Computing global stats for {label} ...')
    n = G.number_of_nodes()
    m = G.number_of_edges()
    if n == 0:
        return {}
    density = nx.density(G)
    avg_deg = 2 * m / n if not directed else m / n
    if directed:
        components = list(nx.weakly_connected_components(G))
    else:
        components = list(nx.connected_components(G))
    lcc_size = max(len(c) for c in components) if components else 0
    lcc_ratio = lcc_size / n if n else 0
    avg_clustering = nx.average_clustering(G) if not directed else 0.0
    stats = {
        'nodes': n, 'edges': m,
        'density': round(density, 8),
        'avg_degree': round(avg_deg, 4),
        'components': len(components),
        'lcc_size': lcc_size,
        'lcc_ratio': round(lcc_ratio, 4),
        'avg_clustering': round(avg_clustering, 6),
    }
    print(f'  {label}: nodes={n}, edges={m}, density={density:.6f}, components={len(components)}, lcc={lcc_size}')
    return stats


# ===================================================================
# Step 4: Dynasty Comparison
# ===================================================================
def dynasty_comparison(G_assoc, person_map):
    print('[Step 4] Dynasty comparison ...')
    from collections import defaultdict as dd
    dyn_pids = dd(set)
    for pid, (name, dyn) in person_map.items():
        if dyn in TARGET_DYNASTIES:
            dyn_pids[dyn].add(pid)
    rows = []
    for dyn in TARGET_DYNASTIES:
        subG = G_assoc.subgraph(dyn_pids[dyn]).copy()
        n = subG.number_of_nodes()
        m = subG.number_of_edges()
        density = nx.density(subG)
        avg_deg = 2 * m / n if n else 0
        comps = list(nx.connected_components(subG))
        avg_clust = nx.average_clustering(subG)
        rows.append({'dynasty':dyn,'nodes':n,'edges':m,'density':round(density,8),
                     'avg_degree':round(avg_deg,4),'avg_clustering':round(avg_clust,6),'components':len(comps)})
        print(f'  {dyn}: {n} nodes, {m} edges')
    with open(OUT_DIR / 'dynasty_comparison.csv', 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['dynasty','nodes','edges','density','avg_degree','avg_clustering','components'])
        w.writeheader(); w.writerows(rows)
    # Bar charts
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('唐/宋/明 社会网络指标对比', fontsize=16, fontweight='bold')
    metrics = [('nodes','节点数'),('edges','边数'),('density','密度'),('avg_degree','平均度')]
    colors_bar = ['#E74C3C','#3498DB','#2ECC71']
    for ax, (key, title) in zip(axes.flat, metrics):
        vals = [r[key] for r in rows]
        bars = ax.bar(TARGET_DYNASTIES, vals, color=colors_bar)
        ax.set_title(title, fontsize=13); ax.set_ylabel(title)
        for bar, v in zip(bars, vals):
            fmt = f'{v:,.0f}' if v > 1 else f'{v:.6f}'
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height(), fmt, ha='center', va='bottom', fontsize=9)
    plt.tight_layout()
    fig.savefig(OUT_DIR / 'dynasty_comparison_bar.png', dpi=150); plt.close(fig)
    print('  Saved dynasty_comparison.csv and dynasty_comparison_bar.png')
    return rows
# ===================================================================
# Step 5: Song Dynasty Deep Analysis
# ===================================================================
def get_song_subgraph(G_assoc, person_map):
    song_ids = {pid for pid, (n, d) in person_map.items() if d == '宋'}
    subG = G_assoc.subgraph(song_ids).copy()
    print(f'  Song subgraph: {subG.number_of_nodes():,} nodes, {subG.number_of_edges():,} edges')
    return subG


def step5a_degree_distribution(G_song, G_kin):
    print('[Step 5a] Degree distributions ...')
    degrees = [d for _, d in G_song.degree()]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(degrees, bins=range(1, max(degrees)+2), edgecolor='white', alpha=0.8, color='#4C78A8')
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlabel('度数 (log)', fontsize=12); ax.set_ylabel('频次 (log)', fontsize=12)
    ax.set_title('宋代社会网络度分布 (对数坐标)', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    fig.savefig(OUT_DIR / 'network_degree_distribution.png', dpi=150); plt.close(fig)

    in_deg = [d for _, d in G_kin.in_degree()]
    out_deg = [d for _, d in G_kin.out_degree()]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    if in_deg:
        ax1.hist(in_deg, bins=range(1, max(in_deg)+2), edgecolor='white', alpha=0.8, color='#72B7B2')
    ax1.set_xscale('log'); ax1.set_yscale('log')
    ax1.set_xlabel('入度 (log)'); ax1.set_ylabel('频次 (log)')
    ax1.set_title('亲属网络入度分布', fontsize=13, fontweight='bold'); ax1.grid(True, alpha=0.3)
    if out_deg:
        ax2.hist(out_deg, bins=range(1, max(out_deg)+2), edgecolor='white', alpha=0.8, color='#F58518')
    ax2.set_xscale('log'); ax2.set_yscale('log')
    ax2.set_xlabel('出度 (log)'); ax2.set_ylabel('频次 (log)')
    ax2.set_title('亲属网络出度分布', fontsize=13, fontweight='bold'); ax2.grid(True, alpha=0.3)
    fig.suptitle('亲属关系度分布', fontsize=15, fontweight='bold')
    plt.tight_layout()
    fig.savefig(OUT_DIR / 'kin_degree_distribution.png', dpi=150); plt.close(fig)
    print('  Saved degree distribution plots')


def step5b_centrality(G_song_lcc, person_map):
    print('[Step 5b] Centrality analysis (may take a few minutes) ...')
    bc = nx.betweenness_centrality(G_song_lcc, k=min(1000, G_song_lcc.number_of_nodes()), seed=42)
    pr = nx.pagerank(G_song_lcc, alpha=0.85)
    bc_ranked = sorted(bc.items(), key=lambda x: -x[1])
    pr_ranked = sorted(pr.items(), key=lambda x: -x[1])
    bc_rank = {pid: i+1 for i, (pid, _) in enumerate(bc_ranked)}
    pr_rank = {pid: i+1 for i, (pid, _) in enumerate(pr_ranked)}
    all_pids = set(list(bc.keys())[:200]) | set(list(pr.keys())[:200])
    rows = []
    for pid in all_pids:
        name, dyn = person_map.get(pid, ('?', '?'))
        deg = G_song_lcc.degree(pid)
        rows.append({'personid':pid,'name':name,'degree':deg,
                     'betweenness':round(bc.get(pid,0),8),'pagerank':round(pr.get(pid,0),8),
                     'betweenness_rank':bc_rank.get(pid,''),'pagerank_rank':pr_rank.get(pid,'')})
    rows.sort(key=lambda x: -x['pagerank'])
    with open(OUT_DIR / 'top_central_persons.csv', 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['personid','name','degree','betweenness','pagerank','betweenness_rank','pagerank_rank'])
        w.writeheader(); w.writerows(rows[:100])
    print('  Top 5 by PageRank:')
    for r in rows[:5]:
        print(f"    {r['name']} (ID={r['personid']}): PR={r['pagerank']:.6f}")
    return rows, bc, pr


def step5c_community(G_song_lcc):
    print('[Step 5c] Community detection (Louvain) ...')
    import community as community_louvain
    partition = community_louvain.best_partition(G_song_lcc, random_state=42)
    comm_sizes = Counter(partition.values())
    num_communities = len(comm_sizes)
    sizes = sorted(comm_sizes.values())
    print(f'  Communities: {num_communities}, max={max(sizes)}, min={min(sizes)}, median={sizes[len(sizes)//2]}')
    return partition, comm_sizes, num_communities


def step5d_ego_sushi(G_assoc, person_map):
    print('[Step 5d] Su Shi ego network ...')
    if SUSHI_ID not in G_assoc:
        print('  WARNING: Su Shi (3767) not in G_assoc'); return
    neighbors = list(G_assoc.neighbors(SUSHI_ID))
    ego_nodes = set(neighbors) | {SUSHI_ID}
    egoG = G_assoc.subgraph(ego_nodes).copy()
    rows = []
    for u, v, data in egoG.edges(data=True):
        sname, _ = person_map.get(u, (str(u), ''))
        tname, _ = person_map.get(v, (str(v), ''))
        rows.append({'source_id':u,'source_name':sname,'target_id':v,'target_name':tname,
                     'category':data.get('category','其他'),'detail_types':data.get('detail_types','')})
    with open(OUT_DIR / 'ego_sushi_edges.csv', 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['source_id','source_name','target_id','target_name','category','detail_types'])
        w.writeheader(); w.writerows(rows)
    fig, ax = plt.subplots(figsize=(16, 16))
    pos = nx.spring_layout(egoG, k=2.5, iterations=80, seed=42)
    node_sizes = [max(80, egoG.degree(n) * 40) for n in egoG.nodes()]
    node_colors = ['#E74C3C' if n == SUSHI_ID else '#4C78A8' for n in egoG.nodes()]
    for cat, color in CATEGORY_COLORS.items():
        elist = [(u, v) for u, v, d in egoG.edges(data=True) if d.get('category') == cat]
        if elist:
            nx.draw_networkx_edges(egoG, pos, edgelist=elist, edge_color=color, alpha=0.5, width=1.2, ax=ax, label=cat)
    nx.draw_networkx_nodes(egoG, pos, node_size=node_sizes, node_color=node_colors, alpha=0.9, ax=ax)
    labels = {n: person_map.get(n, (str(n), ''))[0] for n in egoG.nodes() if n == SUSHI_ID or egoG.degree(n) >= 3}
    nx.draw_networkx_labels(egoG, pos, labels, font_size=8, font_family='Microsoft YaHei', ax=ax)
    ax.set_title(f'蘇軾 (ID={SUSHI_ID}) 自我中心网络 ({len(neighbors)} 位邻居)', fontsize=16, fontweight='bold')
    ax.legend(fontsize=10, loc='upper left'); ax.axis('off')
    fig.savefig(OUT_DIR / 'ego_sushi_network.png', dpi=150, bbox_inches='tight'); plt.close(fig)
    print(f'  Su Shi ego: {len(neighbors)} neighbors, {egoG.number_of_edges()} edges')
    return egoG
# ===================================================================
# Step 6: Interactive Visualization (pyvis)
# ===================================================================
def _inject_click_js(html_path, href_map, header_html=None):
    html = html_path.read_text(encoding='utf-8')
    js = '<script>\n'
    js += 'var top50_href = ' + json.dumps(href_map) + ';\n'
    js += 'var selectedNodeId = null;\n'
    js += 'var allNodes = network.body.data.nodes;\n'
    js += 'var allEdges = network.body.data.edges;\n'
    js += '// Store original data\n'
    js += 'var origNodes = allNodes.get();\n'
    js += 'var origEdges = allEdges.get();\n'
    js += 'function buildNeighborSet(nodeId) {\n'
    js += '    var neighbors = new Set();\n'
    js += '    neighbors.add(nodeId);\n'
    js += '    origEdges.forEach(function(e) {\n'
    js += '        if (String(e.from) === String(nodeId)) neighbors.add(String(e.to));\n'
    js += '        if (String(e.to) === String(nodeId)) neighbors.add(String(e.from));\n'
    js += '    });\n'
    js += '    return neighbors;\n'
    js += '}\n'
    js += 'function highlightNode(nodeId) {\n'
    js += '    var neighbors = buildNeighborSet(nodeId);\n'
    js += '    var newNodes = origNodes.map(function(n) {\n'
    js += '        var nid = String(n.id);\n'
    js += '        if (neighbors.has(nid)) {\n'
    js += '            return Object.assign({}, n, {opacity: 1.0, font: n.font ? Object.assign({}, n.font, {color: "#333"}) : {color: "#333"}});\n'
    js += '        } else {\n'
    js += '            return Object.assign({}, n, {opacity: 0.08, hidden: false});\n'
    js += '        }\n'
    js += '    });\n'
    js += '    var newEdges = origEdges.map(function(e) {\n'
    js += '        var fromId = String(e.from), toId = String(e.to);\n'
    js += '        if (neighbors.has(fromId) && neighbors.has(toId)) {\n'
    js += '            return Object.assign({}, e, {opacity: 0.8, width: 2});\n'
    js += '        } else {\n'
    js += '            return Object.assign({}, e, {opacity: 0.03, width: 0.3});\n'
    js += '        }\n'
    js += '    });\n'
    js += '    allNodes.update(newNodes);\n'
    js += '    allEdges.update(newEdges);\n'
    js += '}\n'
    js += 'function resetAll() {\n'
    js += '    allNodes.update(origNodes);\n'
    js += '    allEdges.update(origEdges);\n'
    js += '}\n'
    js += 'network.on("click", function(params) {\n'
    js += '    if (params.nodes.length > 0) {\n'
    js += '        var nodeId = String(params.nodes[0]);\n'
    js += '        if (selectedNodeId === nodeId) {\n'
    js += '            // Double click same node -> deselect\n'
    js += '            selectedNodeId = null;\n'
    js += '            resetAll();\n'
    js += '        } else {\n'
    js += '            selectedNodeId = nodeId;\n'
    js += '            highlightNode(nodeId);\n'
    js += '        }\n'
    js += '        // Also open ego page for top50 on double-click\n'
    js += '        if (top50_href[nodeId]) { window.open(top50_href[nodeId], "_blank"); }\n'
    js += '    }\n'
    js += '});\n'
    js += '// Update origNodes/origEdges after physics stabilizes (positions get updated)\n'
    js += 'network.on("stabilizationIterationsDone", function() {\n'
    js += '    origNodes = allNodes.get();\n'
    js += '    origEdges = allEdges.get();\n'
    js += '});\n'
    js += '</script>\n'
    html = html.replace('</head>', js + '</head>')
    if header_html:
        html = html.replace('<body>', '<body>\n' + header_html)
    html_path.write_text(html, encoding='utf-8')


def step6a_song_full(G_song, partition, bc, pr, person_map, top_persons):
    print('[Step 6a] Building Song full network HTML ...')
    from pyvis.network import Network
    
    # Filter: keep only nodes with degree >= 3 to reduce size
    keep_nodes = {n for n, d in G_song.degree() if d >= 5}
    top50_pids = {r['personid'] for r in top_persons[:50]}
    keep_nodes |= top50_pids  # Always keep top50
    G_vis = G_song.subgraph(keep_nodes).copy()
    print(f'  Filtered: {G_song.number_of_nodes()} -> {G_vis.number_of_nodes()} nodes, {G_song.number_of_edges()} -> {G_vis.number_of_edges()} edges')
    
    # Pre-compute layout positions with networkx (browser doesn't need to simulate)
    print('  Computing layout with networkx spring_layout (this may take 1-2 min) ...')
    pos = nx.spring_layout(G_vis, k=1.5, iterations=80, seed=42)
    # Scale positions to pixel range
    xs = [p[0] for p in pos.values()]; ys = [p[1] for p in pos.values()]
    x_min, x_max = min(xs), max(xs); y_min, y_max = min(ys), max(ys)
    scale = 1500
    def scale_xy(x, y):
        sx = (x - x_min) / (x_max - x_min + 1e-9) * scale - scale/2
        sy = (y - y_min) / (y_max - y_min + 1e-9) * scale - scale/2
        return sx, sy
    
    net = Network(height='900px', width='100%', bgcolor='#ffffff', font_color='#333333')
    net.toggle_physics(False)  # Disable physics - positions are pre-computed
    
    for i, pid in enumerate(G_vis.nodes()):
        if (i + 1) % 2000 == 0:
            print(f'    Adding nodes: {i+1}/{G_vis.number_of_nodes()}')
        name, dyn = person_map.get(pid, (str(pid), ''))
        deg = G_vis.degree(pid)
        comm = partition.get(pid, 0)
        color = COMMUNITY_COLORS[comm % len(COMMUNITY_COLORS)]
        size = max(5, min(30, 5 + deg * 0.5))
        x, y = scale_xy(*pos[pid])
        title_h = f'<b>{name}</b> (ID={pid})<br>朝代: {dyn}<br>度数: {deg}<br>社区: {comm}'
        kw = {'label': name if deg >= 5 else '', 'color': color, 'size': size, 'title': title_h, 'x': x, 'y': y}
        if pid in top50_pids:
            kw['shape'] = 'star'; kw['size'] = max(15, size); kw['label'] = name
        net.add_node(pid, **kw)
    
    for i, (u, v, data) in enumerate(G_vis.edges(data=True)):
        if (i + 1) % 5000 == 0:
            print(f'    Adding edges: {i+1}/{G_vis.number_of_edges()}')
        cat = data.get('category', '其他')
        net.add_edge(u, v, color=CATEGORY_COLORS.get(cat, '#cccccc'), width=0.5, title=cat)
    
    html_path = OUT_DIR / 'network_song_full.html'
    net.save_graph(str(html_path))
    href_map = {str(r['personid']): f'ego_pages/{r["personid"]}.html' for r in top_persons[:50]}
    _inject_click_js(html_path, href_map)
    print(f'  Saved network_song_full.html ({html_path.stat().st_size / 1024 / 1024:.1f} MB)')


def step6b_ego_pages(top_persons, G_assoc, person_map, bc, pr):
    print('[Step 6b] Generating ego pages for Top 50 ...')
    from pyvis.network import Network
    for idx, rec in enumerate(top_persons[:50]):
        pid = rec['personid']
        name, dyn = person_map.get(pid, (str(pid), ''))
        if pid not in G_assoc:
            continue
        neighbors = list(G_assoc.neighbors(pid))
        ego_nodes = set(neighbors) | {pid}
        egoG = G_assoc.subgraph(ego_nodes).copy()
        net = Network(height='900px', width='100%', bgcolor='#ffffff', font_color='#333333')
        net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=150)
        deg = egoG.degree(pid)
        net.add_node(pid, label=name, color='#E74C3C', size=35, shape='star',
                     title=f'<b>{name}</b> (ID={pid})<br>度数: {deg}')
        for n in egoG.nodes():
            if n == pid: continue
            nname, ndyn = person_map.get(n, (str(n), ''))
            ndeg = egoG.degree(n)
            ed = egoG.get_edge_data(pid, n, default={})
            cat = ed.get('category', '其他') if ed else '其他'
            color = CATEGORY_COLORS.get(cat, '#cccccc')
            net.add_node(n, label=nname, color=color, size=max(8, min(25, 5+ndeg*0.5)),
                         title=f'<b>{nname}</b> (ID={n})<br>朝代: {ndyn}<br>度数: {ndeg}')
        for u, v, data in egoG.edges(data=True):
            cat = data.get('category', '其他')
            net.add_edge(u, v, color=CATEGORY_COLORS.get(cat, '#cccccc'), width=1, title=cat)
        html_path = EGO_DIR / f'{pid}.html'
        net.save_graph(str(html_path))
        header = (f'<div style="padding:12px;background:#f5f5f5;border-bottom:2px solid #333;'
                  f'font-family:Microsoft YaHei,sans-serif;">'
                  f'<h2 style="margin:0 0 6px 0;">{name} (ID={pid})</h2>'
                  f'<p style="margin:2px 0;">朝代: {dyn} | 度数: {deg} | '
                  f'Betweenness排名: {rec.get("betweenness_rank","")} | '
                  f'PageRank排名: {rec.get("pagerank_rank","")}</p></div>')
        href_map = {str(r['personid']): f'{r["personid"]}.html' for r in top_persons[:50]}
        _inject_click_js(html_path, href_map, header_html=header)
        if (idx + 1) % 10 == 0:
            print(f'    Generated {idx+1}/50 ego pages')
    print(f'  Generated {min(50, len(top_persons))} ego pages in {EGO_DIR}')
# ===================================================================
# Step 7: Kinship Analysis
# ===================================================================
def step7_kinship(G_kin):
    print('[Step 7] Kinship network analysis ...')
    return compute_global_stats(G_kin, 'kinship', directed=True)


# ===================================================================
# Step 8: README
# ===================================================================
def write_readme(global_stats, kin_stats, dynasty_rows, song_stats, comm_stats, top_persons):
    print('[Step 8] Writing README.md ...')
    top5_lines = []
    for r in top_persons[:5]:
        top5_lines.append(f'  - {r["name"]} (ID={r["personid"]}): PageRank={r["pagerank"]:.6f}, 度数={r["degree"]}')
    top5_str = chr(10).join(top5_lines)
    dyn_table = ''
    for r in dynasty_rows:
        dyn_table += f'| {r["dynasty"]} | {r["nodes"]:,} | {r["edges"]:,} | {r["density"]:.6f} | {r["avg_degree"]:.2f} | {r["components"]} |\n'
    gs = global_stats
    ks = kin_stats
    readme = f'''# 任务 D：社会化网络研究

## 1. 任务目标
基于 CBDB 的社会关系与亲属关系数据，构建中国历史人物的社会网络，分析网络拓扑结构、朝代差异、社区结构与核心人物。

## 2. 数据来源与清洗策略
- **数据来源**：output_cbdb_v1/ 目录下的 CSV 文件
- **社会关系**：剔除「未詳」记录，双向关系合并为无向边
- **亲属关系**：剔除「非可用」和「未詳」，保留有向边

## 3. 关系类型归并方案
| 大类 | 示例关系 |
|------|----------|
| 文学交往 | 贈詩/文、致書、唱和、同遊 |
| 墓誌傳記 | 為Y作墓誌銘、行狀、神道碑 |
| 師生 | 為Y之學生、門人、弟子 |
| 友人 | 友、同年、同僚、鄰居 |
| 其他 | 未归入上述四类 |

## 4. 核心发现

### 全局网络指标
| 指标 | 社会关系网络 | 亲属关系网络 |
|------|-------------|-------------|
| 节点数 | {gs.get("nodes","N/A"):,} | {ks.get("nodes","N/A"):,} |
| 边数 | {gs.get("edges","N/A"):,} | {ks.get("edges","N/A"):,} |
| 密度 | {gs.get("density","N/A")} | {ks.get("density","N/A")} |
| 平均度 | {gs.get("avg_degree","N/A")} | {ks.get("avg_degree","N/A")} |
| 连通分量 | {gs.get("components","N/A")} | {ks.get("components","N/A")} |
| 最大连通分量 | {gs.get("lcc_size","N/A"):,} | {ks.get("lcc_size","N/A"):,} |
| 平均聚类系数 | {gs.get("avg_clustering","N/A")} | - |

### 朝代对比（唐/宋/明）
| 朝代 | 节点数 | 边数 | 密度 | 平均度 | 连通分量 |
|------|--------|------|------|--------|----------|
{dyn_table}
### 宋代社区检测
- 社区数量：{comm_stats.get("num","N/A")}
- 最大社区：{comm_stats.get("max_size","N/A")} 个节点

### Top 5 中心人物（宋代 PageRank）
{top5_str}

## 5. 产出文件清单
| 文件 | 说明 |
|------|------|
| 
etwork_global_stats.json | 全局网络统计指标 |
| dynasty_comparison.csv | 唐/宋/明朝代对比 |
| dynasty_comparison_bar.png | 朝代对比柱状图 |
| 
etwork_degree_distribution.png | 宋代度分布 |
| kin_degree_distribution.png | 亲属度分布 |
| 	op_central_persons.csv | 中心性排名 |
| ego_sushi_edges.csv | 蘇軾 ego 边表 |
| ego_sushi_network.png | 蘇軾 ego 网络图 |
| 
etwork_song_full.html | 宋代全网交互式可视化 |
| ego_pages/*.html | Top 50 人物 ego 页面 |

## 6. 交互式可视化使用说明
- 浏览器打开 
etwork_song_full.html
- 节点按社区着色，星形节点为中心性 Top 50
- 点击星形节点跳转到 ego page
- 鼠标悬停查看详细信息

## 7. 已知限制
- 部分关系缺少年份，无法时间序列分析
- pyvis 大图 HTML 文件较大
- 朝代归属基于数据库主朝代字段
'''
    (OUT_DIR / 'README.md').write_text(readme, encoding='utf-8-sig')
    print('  Saved README.md')
# ===================================================================
# Step 9: Validation
# ===================================================================
def validate(global_stats, kin_stats, song_stats, comm_stats, top_persons, person_map, G_assoc):
    print()
    print('=' * 60)
    print('VALIDATION SUMMARY')
    print('=' * 60)
    print(f'  Global Nodes: {global_stats.get("nodes","N/A"):,}')
    print(f'  Global Edges: {global_stats.get("edges","N/A"):,}')
    print(f'  Global Components: {global_stats.get("components","N/A")}')
    print(f'  Song Nodes: {song_stats.get("nodes","N/A"):,}')
    print(f'  Song Edges: {song_stats.get("edges","N/A"):,}')
    print(f'  Song Communities: {comm_stats.get("num","N/A")}')
    print(f'  Top 5 Central Persons (PageRank):')
    for r in top_persons[:5]:
        print(f'    {r["name"]}: PR={r["pagerank"]:.6f}')
    if SUSHI_ID in G_assoc:
        print(f'  Su Shi Neighbors: {len(list(G_assoc.neighbors(SUSHI_ID)))}')
    print()
    expected = ['network_global_stats.json','dynasty_comparison.csv','dynasty_comparison_bar.png',
                'network_degree_distribution.png','kin_degree_distribution.png','top_central_persons.csv',
                'ego_sushi_edges.csv','ego_sushi_network.png','network_song_full.html','README.md']
    all_ok = True
    for fname in expected:
        fp = OUT_DIR / fname
        if fp.exists():
            print(f'  {fname}: OK ({fp.stat().st_size:,} bytes)')
        else:
            print(f'  {fname}: MISSING'); all_ok = False
    ego_count = len(list(EGO_DIR.glob('*.html')))
    print(f'  ego_pages/*.html: {ego_count} files')
    if ego_count < 10: all_ok = False
    print(f'  Overall: {"ALL CHECKS PASSED" if all_ok else "SOME CHECKS FAILED"}')
    print('=' * 60)


# ===================================================================
# MAIN
# ===================================================================
def main():
    print('=' * 60)
    print('Part D: Social Network Analysis')
    print('=' * 60)

    # Step 1
    person_map = load_person_map()
    assoc_edges = load_assoc_edges()
    kin_edges = load_kin_edges()

    # Step 2-3
    G_assoc, G_kin = build_graphs(assoc_edges, kin_edges)
    global_stats = compute_global_stats(G_assoc, 'social_network', directed=False)
    kin_stats = compute_global_stats(G_kin, 'kinship_network', directed=True)

    # Step 4
    dynasty_rows = dynasty_comparison(G_assoc, person_map)

    # Step 5
    G_song = get_song_subgraph(G_assoc, person_map)
    step5a_degree_distribution(G_song, G_kin)

    components = list(nx.connected_components(G_song))
    lcc_nodes = max(components, key=len)
    G_song_lcc = G_song.subgraph(lcc_nodes).copy()
    print(f'  Song LCC: {G_song_lcc.number_of_nodes():,} nodes, {G_song_lcc.number_of_edges():,} edges')

    top_persons, bc, pr = step5b_centrality(G_song_lcc, person_map)
    partition, comm_sizes, num_comm = step5c_community(G_song_lcc)

    song_stats = {'nodes': G_song.number_of_nodes(), 'edges': G_song.number_of_edges()}
    comm_stats = {
        'num': num_comm,
        'max_size': max(comm_sizes.values()),
        'min_size': min(comm_sizes.values()),
        'median_size': sorted(comm_sizes.values())[len(comm_sizes)//2],
        'top10': comm_sizes.most_common(10),
    }

    step5d_ego_sushi(G_assoc, person_map)

    # Step 6
    step6a_song_full(G_song, partition, bc, pr, person_map, top_persons)
    step6b_ego_pages(top_persons, G_assoc, person_map, bc, pr)

    # Step 7
    kin_full_stats = step7_kinship(G_kin)

    # Save global stats JSON
    stats_out = {
        'social_network': global_stats,
        'kinship_network': kin_stats,
        'dynasty_comparison': dynasty_rows,
        'song_community': comm_stats,
    }
    (OUT_DIR / 'network_global_stats.json').write_text(
        json.dumps(stats_out, ensure_ascii=False, indent=2), encoding='utf-8-sig')

    # Step 8
    write_readme(global_stats, kin_stats, dynasty_rows, song_stats, comm_stats, top_persons)

    # Step 9
    validate(global_stats, kin_stats, song_stats, comm_stats, top_persons, person_map, G_assoc)
    print(f'Done! All outputs saved to: {OUT_DIR}')


if __name__ == '__main__':
    main()




