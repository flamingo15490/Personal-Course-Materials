import json, re, csv
from pathlib import Path
import networkx as nx
import pandas as pd

ROOT = Path(r"D:\虚拟C盘\study\人工智能与计算思维大作业")
IN_DIR = ROOT / "output_cbdb_v1"
OUT_DIR = ROOT / "任务d"

CATEGORY_COLORS = {"文學交往":"#4C78A8","墓誌傳記":"#72B7B2","師生":"#F58518","友人":"#54A24B","其他":"#B279A2"}
COMMUNITY_COLORS = ["#e6194b","#3cb44b","#ffe119","#4363d8","#f58231","#911eb4","#42d4f4","#f032e6","#bfef45","#fabed4","#469990","#dcbeff","#9A6324","#fffac8","#800000","#aaffc3","#808000","#ffd8b1","#000075","#a9a9a9"]

print("Loading data...")
pm = {}
df = pd.read_csv(IN_DIR / "dim_person.csv", usecols=["c_personid","c_name_chn","dynasty_chn"], dtype={"c_personid":int}, encoding="utf-8", on_bad_lines="skip")
for _, row in df.iterrows():
    pid = int(row["c_personid"])
    name = str(row["c_name_chn"]) if pd.notna(row["c_name_chn"]) else ""
    dyn = str(row["dynasty_chn"]) if pd.notna(row["dynasty_chn"]) else ""
    pm[pid] = (name, dyn)

df2 = pd.read_csv(IN_DIR / "fact_person_assoc.csv", usecols=["c_personid","c_assoc_id","c_assoc_desc_chn"], dtype={"c_personid":int,"c_assoc_id":int}, encoding="utf-8", on_bad_lines="skip")
df2 = df2[df2["c_assoc_desc_chn"] != "未詳"]
edge_map = {}
for _, row in df2.iterrows():
    a, b = int(row["c_personid"]), int(row["c_assoc_id"])
    n1, n2 = min(a, b), max(a, b)
    key = (n1, n2)
    if key not in edge_map: edge_map[key] = set()
    edge_map[key].add(str(row["c_assoc_desc_chn"]))

G = nx.Graph()
for (n1, n2), types in edge_map.items():
    G.add_edge(n1, n2)

song_ids = {pid for pid, (n, d) in pm.items() if d == "宋"}
G_song = G.subgraph(song_ids).copy()

import community as community_louvain
components = list(nx.connected_components(G_song))
lcc_nodes = max(components, key=len)
G_lcc = G_song.subgraph(lcc_nodes).copy()
partition = community_louvain.best_partition(G_lcc, random_state=42)

top_persons = []
with open(OUT_DIR / "top_central_persons.csv", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        top_persons.append(row)

# Filter: deg >= 5
keep_nodes = {n for n, d in G_song.degree() if d >= 5}
top50_pids = {int(r["personid"]) for r in top_persons[:50]}
top20_pids = {int(r["personid"]) for r in top_persons[:20]}
keep_nodes |= top50_pids
G_vis = G_song.subgraph(keep_nodes).copy()
print(f"Filtered: {G_vis.number_of_nodes()} nodes, {G_vis.number_of_edges()} edges")

# Layout with more spacing (higher k)
print("Computing layout with wider spacing...")
pos = nx.spring_layout(G_vis, k=3.0, iterations=100, seed=42)
xs = [p[0] for p in pos.values()]; ys = [p[1] for p in pos.values()]
x_min, x_max = min(xs), max(xs); y_min, y_max = min(ys), max(ys)
scale = 2000  # larger canvas

from pyvis.network import Network
net = Network(height="900px", width="100%", bgcolor="#ffffff", font_color="#333333")
net.toggle_physics(False)

for i, pid in enumerate(G_vis.nodes()):
    name, dyn = pm.get(pid, (str(pid), ""))
    deg = G_vis.degree(pid)
    comm = partition.get(pid, 0)
    color = COMMUNITY_COLORS[comm % len(COMMUNITY_COLORS)]
    size = max(4, min(20, 4 + deg * 0.3))
    x = (pos[pid][0] - x_min) / (x_max - x_min + 1e-9) * scale - scale/2
    y = (pos[pid][1] - y_min) / (y_max - y_min + 1e-9) * scale - scale/2
    title_h = f"<b>{name}</b> (ID={pid})<br>朝代: {dyn}<br>度数: {deg}<br>社区: {comm}"
    
    # Only show label for top 20, make it small
    show_label = pid in top20_pids
    label_font = {"size": 10, "color": "#333"} if show_label else {}
    
    kw = {"label": name if show_label else "", "color": color, "size": size, "title": title_h, "x": x, "y": y, "font": label_font}
    if pid in top50_pids:
        kw["shape"] = "star"; kw["size"] = max(10, size)
        if show_label:
            kw["font"] = {"size": 11, "color": "#333", "bold": True}
    net.add_node(pid, **kw)

for u, v, data in G_vis.edges(data=True):
    cat = data.get("category", "其他")
    net.add_edge(u, v, color=CATEGORY_COLORS.get(cat, "#cccccc"), width=0.3)

html_path = OUT_DIR / "network_song_full.html"
net.save_graph(str(html_path))

# Inject click handler
html = html_path.read_text(encoding="utf-8")
html = re.sub(r"<script>\s*var selectedNodeId.*?</script>", "", html, flags=re.DOTALL)
html = re.sub(r"<script>\s*var top50_href.*?</script>", "", html, flags=re.DOTALL)

js = '<script>\n'
js += 'window.addEventListener("load", function() {\n'
js += '    var selectedNodeId = null;\n'
js += '    var allNodes = network.body.data.nodes;\n'
js += '    var allEdges = network.body.data.edges;\n'
js += '    var origNodes = allNodes.get();\n'
js += '    var origEdges = allEdges.get();\n'
js += '    function buildNeighborSet(nodeId) {\n'
js += '        var neighbors = new Set();\n'
js += '        neighbors.add(String(nodeId));\n'
js += '        origEdges.forEach(function(e) {\n'
js += '            if (String(e.from) === String(nodeId)) neighbors.add(String(e.to));\n'
js += '            if (String(e.to) === String(nodeId)) neighbors.add(String(e.from));\n'
js += '        });\n'
js += '        return neighbors;\n'
js += '    }\n'
js += '    function highlightNode(nodeId) {\n'
js += '        var neighbors = buildNeighborSet(nodeId);\n'
js += '        var newNodes = origNodes.map(function(n) {\n'
js += '            if (neighbors.has(String(n.id))) return Object.assign({}, n, {opacity: 1.0});\n'
js += '            else return Object.assign({}, n, {opacity: 0.03});\n'
js += '        });\n'
js += '        var newEdges = origEdges.map(function(e) {\n'
js += '            if (neighbors.has(String(e.from)) && neighbors.has(String(e.to))) return Object.assign({}, e, {opacity: 0.8, width: 1.5});\n'
js += '            else return Object.assign({}, e, {opacity: 0.01, width: 0.1});\n'
js += '        });\n'
js += '        allNodes.update(newNodes);\n'
js += '        allEdges.update(newEdges);\n'
js += '    }\n'
js += '    function resetAll() {\n'
js += '        allNodes.update(origNodes);\n'
js += '        allEdges.update(origEdges);\n'
js += '    }\n'
js += '    network.on("click", function(params) {\n'
js += '        if (params.nodes.length > 0) {\n'
js += '            var nodeId = String(params.nodes[0]);\n'
js += '            if (selectedNodeId === nodeId) { selectedNodeId = null; resetAll(); }\n'
js += '            else { selectedNodeId = nodeId; highlightNode(nodeId); }\n'
js += '        } else {\n'
js += '            if (selectedNodeId) { selectedNodeId = null; resetAll(); }\n'
js += '        }\n'
js += '    });\n'
js += '    console.log("Click handler installed");\n'
js += '});\n'
js += '</script>\n'
html = html.replace("</body>", js + "</body>")
html_path.write_text(html, encoding="utf-8")
print(f"Done! {html_path.stat().st_size // 1024} KB")
