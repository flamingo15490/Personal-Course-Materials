import re, json
from pathlib import Path

ROOT = Path(r"D:\虚拟C盘\study\人工智能与计算思维大作业")
html_path = ROOT / "任务d" / "network_song_full.html"
html = html_path.read_text(encoding="utf-8")

# Remove old handler
html = re.sub(r"<script>\s*document\.addEventListener.*?</script>", "", html, flags=re.DOTALL)

# Disable node dragging by modifying the options JSON in the HTML
# Find the options block and add interaction settings
if '"interaction"' not in html:
    html = html.replace('"manipulation": {', '"interaction": {"dragNodes": false, "dragView": true, "zoomView": true}, "manipulation": {')

# Parse node names
node_names = {}
for m in re.finditer(r'"id":\s*(\d+).*?"title":\s*"([^"]*)"', html):
    nid = m.group(1)
    title = m.group(2)
    name_m = re.search(r'\\u003cb\\u003e([^\\]*)\\u003c', title)
    if not name_m:
        name_m = re.search(r'<b>([^<]*)<', title)
    name = name_m.group(1) if name_m else nid
    node_names[nid] = name

names_json = json.dumps(node_names, ensure_ascii=False)

js = '<script>\n'
js += 'document.addEventListener("DOMContentLoaded", function() {\n'
js += '    var nodeNames = ' + names_json + ';\n'
js += '    var selectedNodeId = null;\n'
js += '    function init() {\n'
js += '        if (typeof network === "undefined") { setTimeout(init, 200); return; }\n'
js += '        // Disable node dragging\n'
js += '        network.setOptions({interaction: {dragNodes: false, dragView: true, zoomView: true}});\n'
js += '        var infoBar = document.getElementById("info-bar");\n'
js += '        \n'
js += '        function doHighlight(nodeId) {\n'
js += '            var connEdges = network.getConnectedEdges(nodeId);\n'
js += '            var neighbors = new Set();\n'
js += '            neighbors.add(String(nodeId));\n'
js += '            connEdges.forEach(function(eid) {\n'
js += '                var e = network.body.data.edges.get(eid);\n'
js += '                if (e) { neighbors.add(String(e.from)); neighbors.add(String(e.to)); }\n'
js += '            });\n'
js += '            // Build update arrays\n'
js += '            var nodeUpdates = [];\n'
js += '            network.body.data.nodes.forEach(function(n) {\n'
js += '                var sid = String(n.id);\n'
js += '                if (neighbors.has(sid)) {\n'
js += '                    var nm = nodeNames[sid] || sid;\n'
js += '                    var fs = (sid === String(nodeId)) ? 16 : 11;\n'
js += '                    nodeUpdates.push({id: n.id, label: nm, font: {size: fs, color: "#111", face: "Microsoft YaHei"}, opacity: 1.0, hidden: false});\n'
js += '                } else {\n'
js += '                    nodeUpdates.push({id: n.id, label: "", opacity: 0.04, hidden: false});\n'
js += '                }\n'
js += '            });\n'
js += '            network.body.data.nodes.update(nodeUpdates);\n'
js += '            var edgeUpdates = [];\n'
js += '            network.body.data.edges.forEach(function(e) {\n'
js += '                var fid = String(e.from), tid = String(e.to);\n'
js += '                if (neighbors.has(fid) && neighbors.has(tid)) {\n'
js += '                    edgeUpdates.push({id: e.id, opacity: 0.9, width: 2, hidden: false});\n'
js += '                } else {\n'
js += '                    edgeUpdates.push({id: e.id, opacity: 0.02, width: 0.1, hidden: false});\n'
js += '                }\n'
js += '            });\n'
js += '            network.body.data.edges.update(edgeUpdates);\n'
js += '            network.setOptions({physics: false});\n'
js += '            // Info bar\n'
js += '            var ndName = nodeNames[String(nodeId)] || String(nodeId);\n'
js += '            var nArr = [];\n'
js += '            neighbors.forEach(function(nid) { if (nid !== String(nodeId)) nArr.push(nodeNames[nid] || nid); });\n'
js += '            infoBar.innerHTML = "<b>" + ndName + "</b> | 度数: " + (neighbors.size-1) + " | 邻居: " + nArr.slice(0,12).join("\u3001") + (nArr.length>12?"...":"");\n'
js += '            infoBar.style.display = "block";\n'
js += '            document.querySelectorAll(".rank-item").forEach(function(el) { el.classList.remove("active"); });\n'
js += '            var act = document.querySelector(\'.rank-item[data-pid="\' + nodeId + \'"]\');\n'
js += '            if (act) act.classList.add("active");\n'
js += '        }\n'
js += '        function doReset() {\n'
js += '            var nodeUpdates = [];\n'
js += '            network.body.data.nodes.forEach(function(n) {\n'
js += '                nodeUpdates.push({id: n.id, label: "", opacity: 1.0, hidden: false});\n'
js += '            });\n'
js += '            network.body.data.nodes.update(nodeUpdates);\n'
js += '            var edgeUpdates = [];\n'
js += '            network.body.data.edges.forEach(function(e) {\n'
js += '                edgeUpdates.push({id: e.id, opacity: 1.0, width: 0.3, hidden: false});\n'
js += '            });\n'
js += '            network.body.data.edges.update(edgeUpdates);\n'
js += '            network.setOptions({physics: false});\n'
js += '            infoBar.style.display = "none";\n'
js += '            selectedNodeId = null;\n'
js += '            document.querySelectorAll(".rank-item").forEach(function(el) { el.classList.remove("active"); });\n'
js += '        }\n'
js += '        network.on("click", function(params) {\n'
js += '            if (params.nodes.length > 0) {\n'
js += '                var nodeId = params.nodes[0];\n'
js += '                if (selectedNodeId === nodeId) { doReset(); }\n'
js += '                else { selectedNodeId = nodeId; doHighlight(nodeId); }\n'
js += '            } else {\n'
js += '                if (selectedNodeId !== null) doReset();\n'
js += '            }\n'
js += '        });\n'
js += '        window.selectFromList = function(pid) {\n'
js += '            if (selectedNodeId === pid) { doReset(); }\n'
js += '            else { selectedNodeId = pid; doHighlight(pid); network.focus(pid, {scale:0.8, animation:true}); }\n'
js += '        };\n'
js += '        console.log("Handler ready, names:", Object.keys(nodeNames).length);\n'
js += '        // Debug: log a few names\n'
js += '        var keys = Object.keys(nodeNames);\n'
js += '        console.log("Sample:", keys[0], "=", nodeNames[keys[0]], keys[1], "=", nodeNames[keys[1]]);\n'
js += '    }\n'
js += '    init();\n'
js += '});\n'
js += '</script>\n'

html = html.replace("</body>", js + "</body>")
html_path.write_text(html, encoding="utf-8")
print(f"Done! {html_path.stat().st_size // 1024} KB, parsed {len(node_names)} names")
# Print a few samples
for i, (k, v) in enumerate(node_names.items()):
    if i < 5: print(f"  {k} -> {v}")
