import json, re, csv
from pathlib import Path

ROOT = Path(r"D:\虚拟C盘\study\人工智能与计算思维大作业")
html_path = ROOT / "任务d" / "network_song_full.html"
html = html_path.read_text(encoding="utf-8")

# Remove old click handler
html = re.sub(r"<script>\s*window\.addEventListener.*?</script>\s*</body>", "</body>", html, flags=re.DOTALL)

# Node data is already in the file as nodeData variable from previous injection - need to extract it
# Actually, let me re-read and find nodeData
import json as _json
# The nodeData was injected inside the load handler which we just removed
# We need to re-inject it. Let me find the nodes data from the vis DataSet instead.

# Build nodeData from the vis.js node definitions
node_data = {}
# Parse all node entries: {"id": N, "title": "...name...", ...}
for m in re.finditer(r'"id":\s*(\d+).*?"title":\s*"([^"]*)"', html):
    nid = m.group(1)
    title = m.group(2)
    # Extract name from title: <b>NAME</b> ...
    name_m = re.search(r'\\u003cb\\u003e([^\\]*)\\u003c', title)
    if not name_m:
        name_m = re.search(r'<b>([^<]*)<', title)
    name = name_m.group(1) if name_m else nid
    node_data[nid] = name

print(f"Parsed {len(node_data)} node names")

# Build JS that runs immediately after drawGraph()
node_data_json = _json.dumps(node_data, ensure_ascii=False)

js = '<script>\n'
js += '(function() {\n'
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
js += '        var ndName = nodeData[String(nodeId)] || String(nodeId);\n'
js += '        var neighborNames = [];\n'
js += '        neighbors.forEach(function(nid) {\n'
js += '            if (nid !== String(nodeId)) neighborNames.push(nodeData[nid] || nid);\n'
js += '        });\n'
js += '        infoBar.innerHTML = "<b>" + ndName + "</b> 的关系网 | 邻居: " + neighborNames.slice(0,15).join("\u3001") + (neighborNames.length > 15 ? "..." : "");\n'
js += '        infoBar.style.display = "block";\n'
js += '        var updates = [];\n'
js += '        origNodes.forEach(function(n) {\n'
js += '            var nid = String(n.id);\n'
js += '            if (neighbors.has(nid)) {\n'
js += '                var lbl = nodeData[nid] || "";\n'
js += '                updates.push({id: n.id, opacity: 1.0, label: lbl, font: {size: nid === String(nodeId) ? 14 : 9, color: "#222", face: "Microsoft YaHei"}});\n'
js += '            } else {\n'
js += '                updates.push({id: n.id, opacity: 0.03, label: ""});\n'
js += '            }\n'
js += '        });\n'
js += '        allNodes.update(updates);\n'
js += '        var edgeUpdates = [];\n'
js += '        origEdges.forEach(function(e) {\n'
js += '            if (neighbors.has(String(e.from)) && neighbors.has(String(e.to))) {\n'
js += '                edgeUpdates.push({id: e.id, opacity: 0.8, width: 1.5});\n'
js += '            } else {\n'
js += '                edgeUpdates.push({id: e.id, opacity: 0.01, width: 0.1});\n'
js += '            }\n'
js += '        });\n'
js += '        allEdges.update(edgeUpdates);\n'
js += '        document.querySelectorAll(".rank-item").forEach(function(el) { el.classList.remove("active"); });\n'
js += '        var activeEl = document.querySelector(\'.rank-item[data-pid="\' + nodeId + \'"]\');\n'
js += '        if (activeEl) activeEl.classList.add("active");\n'
js += '    }\n'
js += '    function resetAll() {\n'
js += '        var resetNodes = origNodes.map(function(n) { return {id: n.id, opacity: 1.0, label: "", font: {size: 0}}; });\n'
js += '        allNodes.update(resetNodes);\n'
js += '        var resetEdges = origEdges.map(function(e) { return {id: e.id, opacity: 1.0, width: 0.3}; });\n'
js += '        allEdges.update(resetEdges);\n'
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
js += '    console.log("Click handler ready, " + origNodes.length + " nodes, " + origEdges.length + " edges");\n'
js += '})();\n'
js += '</script>\n'

html = html.replace("</body>", js + "</body>")
html_path.write_text(html, encoding="utf-8")
print(f"Done! {html_path.stat().st_size // 1024} KB")
