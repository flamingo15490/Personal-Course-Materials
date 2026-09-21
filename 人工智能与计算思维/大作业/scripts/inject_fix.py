import re, json
from pathlib import Path

ROOT = Path(r"D:\虚拟C盘\study\人工智能与计算思维大作业")
html_path = ROOT / "任务d" / "network_song_full.html"
html = html_path.read_text(encoding="utf-8")

# Fix 1: Change dragNodes from true to false
html = html.replace('"dragNodes": true', '"dragNodes": false')

# Fix 2: Remove old click handler
html = re.sub(r"<script>\s*var nodeNames.*?</script>", "", html, flags=re.DOTALL)

# Fix 3: Replace numeric labels with empty string in the DataSet
html = re.sub(r'"label":\s*\d+,', '"label": "",', html)

# Parse node names using the already-decoded title HTML
node_names = {}
for m in re.finditer(r'"id":\s*(\d+).*?"title":\s*"([^"]*)"', html):
    nid = m.group(1)
    raw_title = m.group(2)
    # Decode \uXXXX manually, replacing surrogates with ?
    def decode_unicode(s):
        def repl(match):
            cp = int(match.group(1), 16)
            if 0xD800 <= cp <= 0xDFFF: return "?"
            try: return chr(cp)
            except: return "?"
        return re.sub(r'\\u([0-9a-fA-F]{4})', repl, s)
    title = decode_unicode(raw_title)
    name_m = re.search(r'<b>([^<]+)</b>', title)
    name = name_m.group(1) if name_m else nid
    node_names[nid] = name

names_json = json.dumps(node_names, ensure_ascii=False)
print(f"Parsed {len(node_names)} names, sample: {list(node_names.items())[:3]}")

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
js += '    var allNodeIds = network.body.data.nodes.getIds();\n'
js += '    var nodeUpdates = allNodeIds.map(function(id) {\n'
js += '        var sid = String(id);\n'
js += '        if (neighbors.has(sid)) {\n'
js += '            var nm = nodeNames[sid] || sid;\n'
js += '            var fs = (sid === String(nodeId)) ? 16 : 11;\n'
js += '            return {id: id, label: nm, font: {size: fs, color: "#111"}, opacity: 1.0};\n'
js += '        } else {\n'
js += '            return {id: id, label: "", opacity: 0.04};\n'
js += '        }\n'
js += '    });\n'
js += '    network.body.data.nodes.update(nodeUpdates);\n'
js += '    var allEdgeIds = network.body.data.edges.getIds();\n'
js += '    var edgeUpdates = allEdgeIds.map(function(id) {\n'
js += '        var e = network.body.data.edges.get(id);\n'
js += '        if (neighbors.has(String(e.from)) && neighbors.has(String(e.to))) {\n'
js += '            return {id: id, opacity: 0.9, width: 2};\n'
js += '        } else {\n'
js += '            return {id: id, opacity: 0.02, width: 0.1};\n'
js += '        }\n'
js += '    });\n'
js += '    network.body.data.edges.update(edgeUpdates);\n'
js += '    network.setOptions({physics: {enabled: false}});\n'
js += '    var ndName = nodeNames[String(nodeId)] || String(nodeId);\n'
js += '    var nArr = [];\n'
js += '    neighbors.forEach(function(nid) { if (nid !== String(nodeId)) nArr.push(nodeNames[nid] || nid); });\n'
js += '    var infoBar = document.getElementById("info-bar");\n'
js += '    infoBar.innerHTML = "<b>" + ndName + "</b> | 度数: " + (neighbors.size-1) + " | 邻居: " + nArr.slice(0,10).join(",") + (nArr.length>10?"...":"");\n'
js += '    infoBar.style.display = "block";\n'
js += '    document.querySelectorAll(".rank-item").forEach(function(el) { el.classList.remove("active"); });\n'
js += '    var act = document.querySelector(\'.rank-item[data-pid="\' + nodeId + \'"]\');\n'
js += '    if (act) act.classList.add("active");\n'
js += '}\n'
js += 'function doReset() {\n'
js += '    var allNodeIds = network.body.data.nodes.getIds();\n'
js += '    network.body.data.nodes.update(allNodeIds.map(function(id) { return {id: id, label: "", opacity: 1.0, font: {size: 0}}; }));\n'
js += '    var allEdgeIds = network.body.data.edges.getIds();\n'
js += '    network.body.data.edges.update(allEdgeIds.map(function(id) { return {id: id, opacity: 1.0, width: 0.3}; }));\n'
js += '    network.setOptions({physics: {enabled: false}});\n'
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
