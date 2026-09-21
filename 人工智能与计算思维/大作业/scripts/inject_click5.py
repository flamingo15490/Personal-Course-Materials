import re, json
from pathlib import Path

ROOT = Path(r"D:\虚拟C盘\study\人工智能与计算思维大作业")
html_path = ROOT / "任务d" / "network_song_full.html"
html = html_path.read_text(encoding="utf-8")

# Remove old handler
html = re.sub(r"<script>\s*document\.addEventListener.*?</script>", "", html, flags=re.DOTALL)

# Parse node names from vis DataSet
node_names = {}
for m in re.finditer(r'"id":\s*(\d+).*?"title":\s*"([^"]*)"', html):
    nid = m.group(1)
    title = m.group(2)
    name_m = re.search(r'\\u003cb\\u003e([^\\]*)\\u003c', title)
    if not name_m:
        name_m = re.search(r'<b>([^<]*)<', title)
    name = name_m.group(1) if name_m else nid
    node_names[nid] = name

print(f"Parsed {len(node_names)} names")
names_json = json.dumps(node_names, ensure_ascii=False)

js = '<script>\n'
js += 'document.addEventListener("DOMContentLoaded", function() {\n'
js += '    var nodeNames = ' + names_json + ';\n'
js += '    var selectedNodeId = null;\n'
js += '    function init() {\n'
js += '        if (typeof network === "undefined") { setTimeout(init, 200); return; }\n'
js += '        console.log("READY");\n'
js += '        var infoBar = document.getElementById("info-bar");\n'
js += '        \n'
js += '        function doHighlight(nodeId) {\n'
js += '            var connectedEdges = network.getConnectedEdges(nodeId);\n'
js += '            var neighborIds = new Set();\n'
js += '            neighborIds.add(String(nodeId));\n'
js += '            connectedEdges.forEach(function(eid) {\n'
js += '                var edge = network.body.data.edges.get(eid);\n'
js += '                if (edge) {\n'
js += '                    neighborIds.add(String(edge.from));\n'
js += '                    neighborIds.add(String(edge.to));\n'
js += '                }\n'
js += '            });\n'
js += '            var nodeUpdates = [];\n'
js += '            network.body.data.nodes.forEach(function(n) {\n'
js += '                var sid = String(n.id);\n'
js += '                if (neighborIds.has(sid)) {\n'
js += '                    var lbl = nodeNames[sid] || "";\n'
js += '                    var fs = (sid === String(nodeId)) ? 14 : 10;\n'
js += '                    nodeUpdates.push({id: n.id, opacity: 1.0, hidden: false, label: lbl, font: {size: fs, color: "#222", face: "Microsoft YaHei"}});\n'
js += '                } else {\n'
js += '                    nodeUpdates.push({id: n.id, opacity: 0.05, hidden: false, label: ""});\n'
js += '                }\n'
js += '            });\n'
js += '            var edgeUpdates = [];\n'
js += '            network.body.data.edges.forEach(function(e) {\n'
js += '                var fid = String(e.from), tid = String(e.to);\n'
js += '                if (neighborIds.has(fid) && neighborIds.has(tid)) {\n'
js += '                    edgeUpdates.push({id: e.id, opacity: 0.9, width: 2, hidden: false});\n'
js += '                } else {\n'
js += '                    edgeUpdates.push({id: e.id, opacity: 0.02, width: 0.1, hidden: false});\n'
js += '                }\n'
js += '            });\n'
js += '            network.body.data.nodes.update(nodeUpdates);\n'
js += '            network.body.data.edges.update(edgeUpdates);\n'
js += '            network.redraw();\n'
js += '            // Info bar\n'
js += '            var ndName = nodeNames[String(nodeId)] || nodeId;\n'
js += '            var nNames = [];\n'
js += '            neighborIds.forEach(function(nid) { if (nid !== String(nodeId)) nNames.push(nodeNames[nid] || nid); });\n'
js += '            infoBar.innerHTML = "<b>" + ndName + "</b> | 度数: " + (neighborIds.size-1) + " | 邻居: " + nNames.slice(0,12).join("\u3001") + (nNames.length>12?"...":"");\n'
js += '            infoBar.style.display = "block";\n'
js += '            document.querySelectorAll(".rank-item").forEach(function(el) { el.classList.remove("active"); });\n'
js += '            var act = document.querySelector(\'.rank-item[data-pid="\' + nodeId + \'"]\');\n'
js += '            if (act) act.classList.add("active");\n'
js += '        }\n'
js += '        function doReset() {\n'
js += '            var nodeUpdates = [];\n'
js += '            network.body.data.nodes.forEach(function(n) {\n'
js += '                nodeUpdates.push({id: n.id, opacity: 1.0, hidden: false, label: ""});\n'
js += '            });\n'
js += '            var edgeUpdates = [];\n'
js += '            network.body.data.edges.forEach(function(e) {\n'
js += '                edgeUpdates.push({id: e.id, opacity: 1.0, width: 0.3, hidden: false});\n'
js += '            });\n'
js += '            network.body.data.nodes.update(nodeUpdates);\n'
js += '            network.body.data.edges.update(edgeUpdates);\n'
js += '            network.redraw();\n'
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
js += '    }\n'
js += '    init();\n'
js += '});\n'
js += '</script>\n'

html = html.replace("</body>", js + "</body>")
html_path.write_text(html, encoding="utf-8")
print(f"Done! {html_path.stat().st_size // 1024} KB")
