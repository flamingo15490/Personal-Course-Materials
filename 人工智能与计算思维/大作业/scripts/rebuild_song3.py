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

# Build node data for JS side panel
node_data_js = {}

for i, pid in enumerate(G_vis.nodes()):
    name, dyn = pm.get(pid, (str(pid), ""))
    deg = G_vis.degree(pid)
    comm = partition.get(pid, 0)
    color = COMMUNITY_COLORS[comm % len(COMMUNITY_COLORS)]
    size = max(4, min(18, 4 + deg * 0.3))
    x = (pos[pid][0] - x_min) / (x_max - x_min + 1e-9) * scale - scale/2
    y = (pos[pid][1] - y_min) / (y_max - y_min + 1e-9) * scale - scale/2
    title_h = f"<b>{name}</b> (ID={pid})<br>朝代: {dyn}<br>度数: {deg}<br>社区: {comm}"
    
    # NO labels on any node by default
    kw = {"label": "", "color": color, "size": size, "title": title_h, "x": x, "y": y}
    if pid in top50_pids:
        kw["shape"] = "star"; kw["size"] = max(10, size)
    net.add_node(pid, **kw)
    
    node_data_js[str(pid)] = {"name": name, "dynasty": dyn, "deg": deg}

for u, v, data in G_vis.edges(data=True):
    cat = data.get("category", "其他")
    net.add_edge(u, v, color=CATEGORY_COLORS.get(cat, "#cccccc"), width=0.3)

html_path = OUT_DIR / "network_song_full.html"
net.save_graph(str(html_path))

# Now rebuild the HTML with sidebar and click handler
html = html_path.read_text(encoding="utf-8")
html = re.sub(r"<script>\s*var selectedNodeId.*?</script>", "", html, flags=re.DOTALL)
html = re.sub(r"<script>\s*var top50_href.*?</script>", "", html, flags=re.DOTALL)

# Add CSS for sidebar
css = '<style>\n'
css += 'body { margin: 0; padding: 0; display: flex; height: 100vh; overflow: hidden; }\n'
css += '#sidebar { width: 280px; min-width: 280px; background: #1a1a2e; color: #eee; overflow-y: auto; padding: 12px; font-family: "Microsoft YaHei", sans-serif; }\n'
css += '#sidebar h3 { margin: 0 0 10px 0; font-size: 15px; color: #f58518; border-bottom: 1px solid #333; padding-bottom: 8px; }\n'
css += '#sidebar .rank-item { padding: 6px 8px; margin: 2px 0; border-radius: 4px; cursor: pointer; font-size: 13px; display: flex; align-items: center; transition: background 0.15s; }\n'
css += '#sidebar .rank-item:hover { background: #16213e; }\n'
css += '#sidebar .rank-item.active { background: #0f3460; border-left: 3px solid #f58518; }\n'
css += '#sidebar .rank-num { color: #888; min-width: 24px; font-size: 12px; }\n'
css += '#sidebar .rank-name { flex: 1; margin-left: 4px; }\n'
css += '#sidebar .rank-deg { color: #72B7B2; font-size: 11px; margin-left: 6px; }\n'
css += '#sidebar .legend { margin-top: 16px; padding-top: 10px; border-top: 1px solid #333; }\n'
css += '#sidebar .legend h4 { margin: 0 0 6px 0; font-size: 13px; color: #aaa; }\n'
css += '#sidebar .legend-item { font-size: 12px; padding: 2px 0; display: flex; align-items: center; }\n'
css += '#sidebar .legend-dot { width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; display: inline-block; }\n'
css += '#graph-wrap { flex: 1; position: relative; }\n'
css += '#mynetwork { width: 100% !important; height: 100% !important; }\n'
css += '#info-bar { position: absolute; top: 8px; left: 8px; background: rgba(255,255,255,0.92); padding: 8px 14px; border-radius: 6px; font-size: 13px; font-family: "Microsoft YaHei", sans-serif; box-shadow: 0 1px 4px rgba(0,0,0,0.15); display: none; z-index: 10; }\n'
css += '#info-bar b { color: #E74C3C; }\n'
css += '</style>\n'
html = html.replace("<head>", "<head>\n" + css)

# Build sidebar HTML
sidebar = '<div id="sidebar">\n'
sidebar += '<h3>宋代社会网络中心性 Top 20</h3>\n'
for i, r in enumerate(top_persons[:20]):
    pid = r["personid"]
    name = r["name"]
    deg = r["degree"]
    sidebar += f'<div class="rank-item" data-pid="{pid}" onclick="selectFromList({pid})">'
    sidebar += f'<span class="rank-num">{i+1}.</span>'
    sidebar += f'<span class="rank-name">{name}</span>'
    sidebar += f'<span class="rank-deg">度{deg}</span>'
    sidebar += f'</div>\n'

# Legend
sidebar += '<div class="legend">\n<h4>关系大类图例</h4>\n'
cat_labels = {"文學交往":"文学交往","墓誌傳記":"墓誌传记","師生":"师生","友人":"友人","其他":"其他"}
for cat, color in CATEGORY_COLORS.items():
    sidebar += f'<div class="legend-item"><span class="legend-dot" style="background:{color}"></span>{cat_labels[cat]}</div>\n'
sidebar += '</div>\n'

sidebar += '<div class="legend">\n<h4>操作说明</h4>\n'
sidebar += '<div style="font-size:12px;color:#aaa;line-height:1.6;">'
sidebar += '点击节点：高亮该人物及其关系<br>'
sidebar += '再次点击：取消选择<br>'
sidebar += '点击空白：恢复全部<br>'
sidebar += '悬停节点：查看信息</div>\n'
sidebar += '</div>\n'
sidebar += '</div>\n'

# Wrap the graph in a div
html = html.replace('<div id="mynetwork">', '<div id="graph-wrap"><div id="info-bar"></div>\n<div id="mynetwork">')
# Find closing of mynetwork div and close graph-wrap
html = html.replace('</body>', '</div></body>')

# Replace <body> with flex container
html = html.replace("<body>", "<body>\n" + sidebar)

# Info bar element
info_bar_html = '<div id="info-bar"></div>'

# Build JS
node_data_json = json.dumps(node_data_js, ensure_ascii=False)

js = '<script>\n'
js += 'window.addEventListener("load", function() {\n'
js += '    var nodeData = ' + node_data_json + ';\n'
js += '    var selectedNodeId = null;\n'
js += '    var allNodes = network.body.data.nodes;\n'
js += '    var allEdges = network.body.data.edges;\n'
js += '    var origNodes = allNodes.get();\n'
js += '    var origEdges = allEdges.get();\n'
js += '    var infoBar = document.getElementById("info-bar");\n'
js += '    \n'
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
js += '        var nd = nodeData[String(nodeId)];\n'
js += '        var neighborNames = [];\n'
js += '        neighbors.forEach(function(nid) {\n'
js += '            if (nid !== String(nodeId) && nodeData[nid]) neighborNames.push(nodeData[nid].name);\n'
js += '        });\n'
js += '        infoBar.innerHTML = "<b>" + (nd ? nd.name : nodeId) + "</b> 的关系网 | 邻居: " + neighborNames.slice(0,15).join("、") + (neighborNames.length > 15 ? "..." : "");\n'
js += '        infoBar.style.display = "block";\n'
js += '        var newNodes = origNodes.map(function(n) {\n'
js += '            var nid = String(n.id);\n'
js += '            var nd2 = nodeData[nid];\n'
js += '            if (neighbors.has(nid)) {\n'
js += '                var lbl = (nd2 && nid !== String(nodeId)) ? nd2.name : "";\n'
js += '                if (nid === String(nodeId)) lbl = nd2 ? nd2.name : "";\n'
js += '                return Object.assign({}, n, {opacity: 1.0, label: lbl, font: {size: nid === String(nodeId) ? 14 : 10, color: "#333"}});\n'
js += '            } else {\n'
js += '                return Object.assign({}, n, {opacity: 0.03, label: ""});\n'
js += '            }\n'
js += '        });\n'
js += '        var newEdges = origEdges.map(function(e) {\n'
js += '            if (neighbors.has(String(e.from)) && neighbors.has(String(e.to))) return Object.assign({}, e, {opacity: 0.8, width: 1.5});\n'
js += '            else return Object.assign({}, e, {opacity: 0.01, width: 0.1});\n'
js += '        });\n'
js += '        allNodes.update(newNodes);\n'
js += '        allEdges.update(newEdges);\n'
js += '        // Update sidebar active state\n'
js += '        document.querySelectorAll(".rank-item").forEach(function(el) { el.classList.remove("active"); });\n'
js += '        var activeEl = document.querySelector(\'.rank-item[data-pid="\'+nodeId+\'"]\');\n'
js += '        if (activeEl) activeEl.classList.add("active");\n'
js += '    }\n'
js += '    function resetAll() {\n'
js += '        allNodes.update(origNodes);\n'
js += '        allEdges.update(origEdges);\n'
js += '        infoBar.style.display = "none";\n'
js += '        document.querySelectorAll(".rank-item").forEach(function(el) { el.classList.remove("active"); });\n'
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
js += '    window.selectFromList = function(pid) {\n'
js += '        pid = String(pid);\n'
js += '        if (selectedNodeId === pid) { selectedNodeId = null; resetAll(); }\n'
js += '        else { selectedNodeId = pid; highlightNode(pid); network.focus(pid, {scale: 0.8, animation: true}); }\n'
js += '    };\n'
js += '    console.log("Click handler installed");\n'
js += '});\n'
js += '</script>\n'
html = html.replace("</body>", js + "</body>")

html_path.write_text(html, encoding="utf-8")
print(f"Done! {html_path.stat().st_size // 1024} KB")
