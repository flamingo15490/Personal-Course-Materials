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

keep_nodes = {n for n, d in G_song.degree() if d >= 5}
top50_pids = {int(r["personid"]) for r in top_persons[:50]}
keep_nodes |= top50_pids
G_vis = G_song.subgraph(keep_nodes).copy()
print(f"Filtered: {G_vis.number_of_nodes()} nodes, {G_vis.number_of_edges()} edges")

print("Computing layout...")
pos = nx.spring_layout(G_vis, k=3.0, iterations=100, seed=42)
xs = [p[0] for p in pos.values()]; ys = [p[1] for p in pos.values()]
x_min, x_max = min(xs), max(xs); y_min, y_max = min(ys), max(ys)
scale = 2000

from pyvis.network import Network
net = Network(height="900px", width="100%", bgcolor="#ffffff", font_color="#333333")
net.toggle_physics(False)

name_map = {}
for pid in G_vis.nodes():
    name, dyn = pm.get(pid, (str(pid), ""))
    deg = G_vis.degree(pid)
    comm = partition.get(pid, 0)
    color = COMMUNITY_COLORS[comm % len(COMMUNITY_COLORS)]
    size = max(4, min(18, 4 + deg * 0.3))
    x = (pos[pid][0] - x_min) / (x_max - x_min + 1e-9) * scale - scale/2
    y = (pos[pid][1] - y_min) / (y_max - y_min + 1e-9) * scale - scale/2
    title_h = f"<b>{name}</b> (ID={pid})<br>朝代: {dyn}<br>度数: {deg}<br>社区: {comm}"
    kw = {"label": "", "color": color, "size": size, "title": title_h, "x": x, "y": y}
    if pid in top50_pids:
        kw["shape"] = "star"; kw["size"] = max(10, size)
    net.add_node(pid, **kw)
    name_map[str(pid)] = name

for u, v, data in G_vis.edges(data=True):
    cat = data.get("category", "其他")
    net.add_edge(u, v, color=CATEGORY_COLORS.get(cat, "#cccccc"), width=0.3)

html_path = OUT_DIR / "network_song_full.html"
net.save_graph(str(html_path))

# Post-process HTML
html = html_path.read_text(encoding="utf-8")

# Fix dragNodes
html = html.replace('"dragNodes": true', '"dragNodes": false')

# Fix any numeric labels that pyvis might have set
# The DataSet entries look like: "label": 1, or "label": 123,
# We need to keep "label": "" (string) as-is, only fix numeric ones
html = re.sub(r'"label":\s*(\d+)(?=\s*,)', '"label": ""', html)

# Build sidebar
top_persons_csv = []
with open(OUT_DIR / "top_central_persons.csv", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        top_persons_csv.append(row)

css = '<style>\n'
css += 'body { margin: 0; padding: 0; display: flex; height: 100vh; overflow: hidden; }\n'
css += '#sidebar { width: 260px; min-width: 260px; background: #1a1a2e; color: #eee; overflow-y: auto; padding: 12px; font-family: "Microsoft YaHei", sans-serif; }\n'
css += '#sidebar h3 { margin: 0 0 10px 0; font-size: 14px; color: #f58518; border-bottom: 1px solid #333; padding-bottom: 8px; }\n'
css += '#sidebar .rank-item { padding: 5px 8px; margin: 2px 0; border-radius: 4px; cursor: pointer; font-size: 13px; display: flex; align-items: center; transition: background 0.15s; }\n'
css += '#sidebar .rank-item:hover { background: #16213e; }\n'
css += '#sidebar .rank-item.active { background: #0f3460; border-left: 3px solid #f58518; }\n'
css += '#sidebar .rank-num { color: #888; min-width: 22px; font-size: 11px; }\n'
css += '#sidebar .rank-name { flex: 1; margin-left: 4px; }\n'
css += '#sidebar .rank-deg { color: #72B7B2; font-size: 11px; margin-left: 6px; }\n'
css += '#sidebar .legend { margin-top: 14px; padding-top: 10px; border-top: 1px solid #333; }\n'
css += '#sidebar .legend h4 { margin: 0 0 6px 0; font-size: 12px; color: #aaa; }\n'
css += '#sidebar .legend-item { font-size: 12px; padding: 2px 0; display: flex; align-items: center; }\n'
css += '#sidebar .legend-dot { width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; display: inline-block; }\n'
css += '#graph-wrap { flex: 1; position: relative; }\n'
css += '#mynetwork { width: 100% !important; height: 100% !important; }\n'
css += '#info-bar { position: absolute; top: 8px; left: 8px; background: rgba(255,255,255,0.95); padding: 8px 14px; border-radius: 6px; font-size: 13px; font-family: "Microsoft YaHei", sans-serif; box-shadow: 0 1px 4px rgba(0,0,0,0.15); display: none; z-index: 10; max-width: 600px; }\n'
css += '#info-bar b { color: #E74C3C; }\n'
css += '</style>\n'
html = html.replace("<head>", "<head>\n" + css)

sidebar = '<div id="sidebar">\n'
sidebar += '<h3>宋代社会网络 Top 20</h3>\n'
for i, r in enumerate(top_persons_csv[:20]):
    pid = r["personid"]
    sidebar += f'<div class="rank-item" data-pid="{pid}" onclick="selectFromList({pid})">'
    sidebar += f'<span class="rank-num">{i+1}.</span>'
    sidebar += f'<span class="rank-name">{r["name"]}</span>'
    sidebar += f'<span class="rank-deg">度{r["degree"]}</span></div>\n'
sidebar += '<div class="legend"><h4>关系大类</h4>\n'
for cat, color in CATEGORY_COLORS.items():
    label = {"文學交往":"文学","墓誌傳記":"墓志","師生":"师生","友人":"友人","其他":"其他"}.get(cat, cat)
    sidebar += f'<div class="legend-item"><span class="legend-dot" style="background:{color}"></span>{label}</div>\n'
sidebar += '</div></div>\n'

html = html.replace("<body>", "<body>\n" + sidebar)
html = html.replace('<div id="mynetwork">', '<div id="graph-wrap"><div id="info-bar"></div>\n<div id="mynetwork">')

names_json = json.dumps(name_map, ensure_ascii=False)

js = '<script>\n'
js += 'var nodeNames = ' + names_json + ';\n'
js += 'var selectedNodeId = null;\n'
js += 'function doHighlight(nodeId) {\n'
js += '    var connEdges = network.getConnectedEdges(nodeId);\n'
js += '    var neighbors = new Set();\n'
js += '    neighbors.add(String(nodeId));\n'
js += '    connEdges.forEach(function(eid) {\n'
js += '        var e = network.body.data.edges.get(eid);\n'
js += '        if (e) { neighbors.add(String(e.from)); neighbors.add(String(e.to)); }\n'
js += '    });\n'
js += '    var nodeUpdates = [];\n'
js += '    network.body.data.nodes.forEach(function(n) {\n'
js += '        var sid = String(n.id);\n'
js += '        if (neighbors.has(sid)) {\n'
js += '            var nm = nodeNames[sid] || sid;\n'
js += '            var fs = (sid === String(nodeId)) ? 16 : 11;\n'
js += '            nodeUpdates.push({id: n.id, label: nm, font: {size: fs, color: "#111"}, opacity: 1.0});\n'
js += '        } else {\n'
js += '            nodeUpdates.push({id: n.id, label: "", opacity: 0.04});\n'
js += '        }\n'
js += '    });\n'
js += '    network.body.data.nodes.update(nodeUpdates);\n'
js += '    var edgeUpdates = [];\n'
js += '    network.body.data.edges.forEach(function(e) {\n'
js += '        if (neighbors.has(String(e.from)) && neighbors.has(String(e.to))) {\n'
js += '            edgeUpdates.push({id: e.id, opacity: 0.9, width: 2});\n'
js += '        } else {\n'
js += '            edgeUpdates.push({id: e.id, opacity: 0.02, width: 0.1});\n'
js += '        }\n'
js += '    });\n'
js += '    network.body.data.edges.update(edgeUpdates);\n'
js += '    network.setOptions({physics: {enabled: false}, interaction: {dragNodes: false}});\n'
js += '    var ndName = nodeNames[String(nodeId)] || String(nodeId);\n'
js += '    var nArr = [];\n'
js += '    neighbors.forEach(function(nid) { if (nid !== String(nodeId)) nArr.push(nodeNames[nid] || nid); });\n'
js += '    document.getElementById("info-bar").innerHTML = "<b>" + ndName + "</b> | 度数: " + (neighbors.size-1) + " | 邻居: " + nArr.slice(0,10).join(",") + (nArr.length>10?"...":"");\n'
js += '    document.getElementById("info-bar").style.display = "block";\n'
js += '    document.querySelectorAll(".rank-item").forEach(function(el) { el.classList.remove("active"); });\n'
js += '    var act = document.querySelector(\'.rank-item[data-pid="\' + nodeId + \'"]\');\n'
js += '    if (act) act.classList.add("active");\n'
js += '}\n'
js += 'function doReset() {\n'
js += '    network.body.data.nodes.forEach(function(n) { n.label = ""; n.opacity = 1.0; });\n'
js += '    network.body.data.nodes.update(network.body.data.nodes.get());\n'
js += '    network.body.data.edges.forEach(function(e) { e.opacity = 1.0; e.width = 0.3; });\n'
js += '    network.body.data.edges.update(network.body.data.edges.get());\n'
js += '    network.setOptions({physics: {enabled: false}, interaction: {dragNodes: false}});\n'
js += '    document.getElementById("info-bar").style.display = "none";\n'
js += '    selectedNodeId = null;\n'
js += '    document.querySelectorAll(".rank-item").forEach(function(el) { el.classList.remove("active"); });\n'
js += '}\n'
js += 'network.on("click", function(params) {\n'
js += '    if (params.nodes.length > 0) {\n'
js += '        var nodeId = params.nodes[0];\n'
js += '        if (selectedNodeId === nodeId) { doReset(); }\n'
js += '        else { selectedNodeId = nodeId; doHighlight(nodeId); }\n'
js += '    } else {\n'
js += '        if (selectedNodeId !== null) doReset();\n'
js += '    }\n'
js += '});\n'
js += 'function selectFromList(pid) {\n'
js += '    if (selectedNodeId === pid) { doReset(); }\n'
js += '    else { selectedNodeId = pid; doHighlight(pid); network.focus(pid, {scale:0.8, animation:true}); }\n'
js += '}\n'
js += 'console.log("Ready");\n'
js += '</script>\n'

html = html.replace("</body>", js + "</body>")
html_path.write_text(html, encoding="utf-8")
print(f"Done! {html_path.stat().st_size // 1024} KB")
