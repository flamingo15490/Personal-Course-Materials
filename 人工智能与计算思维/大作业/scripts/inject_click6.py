import re, json
from pathlib import Path

ROOT = Path(r"D:\虚拟C盘\study\人工智能与计算思维大作业")
html_path = ROOT / "任务d" / "network_song_full.html"
html = html_path.read_text(encoding="utf-8")

# Remove old handler
html = re.sub(r"<script>\s*document\.addEventListener.*?</script>", "", html, flags=re.DOTALL)

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
js += '            // Update nodes\n'
js += '            network.body.data.nodes.forEach(function(n) {\n'
js += '                var sid = String(n.id);\n'
js += '                if (neighbors.has(sid)) {\n'
js += '                    var nm = nodeNames[sid] || sid;\n'
js += '                    var fs = (sid === String(nodeId)) ? 16 : 11;\n'
js += '                    n.label = nm;\n'
js += '                    n.font = {size: fs, color: "#111", face: "Microsoft YaHei"};\n'
js += '                    n.opacity = 1.0;\n'
js += '                    n.hidden = false;\n'
js += '                } else {\n'
js += '                    n.label = "";\n'
js += '                    n.opacity = 0.04;\n'
js += '                    n.hidden = false;\n'
js += '                }\n'
js += '            });\n'
js += '            network.body.data.nodes.update(network.body.data.nodes.get());\n'
js += '            // Update edges\n'
js += '            network.body.data.edges.forEach(function(e) {\n'
js += '                var fid = String(e.from), tid = String(e.to);\n'
js += '                if (neighbors.has(fid) && neighbors.has(tid)) {\n'
js += '                    e.opacity = 0.9;\n'
js += '                    e.width = 2;\n'
js += '                    e.hidden = false;\n'
js += '                } else {\n'
js += '                    e.opacity = 0.02;\n'
js += '                    e.width = 0.1;\n'
js += '                    e.hidden = false;\n'
js += '                }\n'
js += '            });\n'
js += '            network.body.data.edges.update(network.body.data.edges.get());\n'
js += '            network.setOptions({physics: false});\n'
js += '            network.redraw();\n'
js += '            // Info bar\n'
js += '            var ndName = nodeNames[String(nodeId)] || nodeId;\n'
js += '            var nNames = [];\n'
js += '            neighbors.forEach(function(nid) { if (nid !== String(nodeId)) nNames.push(nodeNames[nid] || nid); });\n'
js += '            infoBar.innerHTML = "<b>" + ndName + "</b> | 度数: " + (neighbors.size-1) + " | 邻居: " + nNames.slice(0,12).join("\u3001") + (nNames.length>12?"...":"");\n'
js += '            infoBar.style.display = "block";\n'
js += '            document.querySelectorAll(".rank-item").forEach(function(el) { el.classList.remove("active"); });\n'
js += '            var act = document.querySelector(\'.rank-item[data-pid="\' + nodeId + \'"]\');\n'
js += '            if (act) act.classList.add("active");\n'
js += '        }\n'
js += '        function doReset() {\n'
js += '            network.body.data.nodes.forEach(function(n) {\n'
js += '                n.label = "";\n'
js += '                n.opacity = 1.0;\n'
js += '                n.hidden = false;\n'
js += '            });\n'
js += '            network.body.data.nodes.update(network.body.data.nodes.get());\n'
js += '            network.body.data.edges.forEach(function(e) {\n'
js += '                e.opacity = 1.0;\n'
js += '                e.width = 0.3;\n'
js += '                e.hidden = false;\n'
js += '            });\n'
js += '            network.body.data.edges.update(network.body.data.edges.get());\n'
js += '            network.setOptions({physics: false});\n'
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
js += '        console.log("Handler ready");\n'
js += '    }\n'
js += '    init();\n'
js += '});\n'
js += '</script>\n'

html = html.replace("</body>", js + "</body>")
html_path.write_text(html, encoding="utf-8")
print(f"Done! {html_path.stat().st_size // 1024} KB, parsed {len(node_names)} names")
