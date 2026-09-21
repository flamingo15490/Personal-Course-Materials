import json, re
from pathlib import Path

ROOT = Path(r"D:\虚拟C盘\study\人工智能与计算思维大作业")
EGO_DIR = ROOT / "任务d" / "ego_pages"

js = '<script>\n'
js += 'var selectedNodeId = null;\n'
js += 'var allNodes = network.body.data.nodes;\n'
js += 'var allEdges = network.body.data.edges;\n'
js += 'var origNodes = allNodes.get();\n'
js += 'var origEdges = allEdges.get();\n'
js += 'function buildNeighborSet(nodeId) {\n'
js += '    var neighbors = new Set();\n'
js += '    neighbors.add(String(nodeId));\n'
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
js += '        if (neighbors.has(nid)) { return Object.assign({}, n, {opacity: 1.0}); }\n'
js += '        else { return Object.assign({}, n, {opacity: 0.05}); }\n'
js += '    });\n'
js += '    var newEdges = origEdges.map(function(e) {\n'
js += '        var fromId = String(e.from), toId = String(e.to);\n'
js += '        if (neighbors.has(fromId) && neighbors.has(toId)) { return Object.assign({}, e, {opacity: 0.8, width: 2}); }\n'
js += '        else { return Object.assign({}, e, {opacity: 0.02, width: 0.2}); }\n'
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
js += '        if (selectedNodeId === nodeId) { selectedNodeId = null; resetAll(); }\n'
js += '        else { selectedNodeId = nodeId; highlightNode(nodeId); }\n'
js += '    } else {\n'
js += '        if (selectedNodeId) { selectedNodeId = null; resetAll(); }\n'
js += '    }\n'
js += '});\n'
js += '</script>\n'

count = 0
for f in EGO_DIR.glob("*.html"):
    html = f.read_text(encoding="utf-8")
    # Remove old click handlers
    html = re.sub(r"<script>\s*var top50_href.*?</script>", "", html, flags=re.DOTALL)
    if "selectedNodeId" not in html:
        html = html.replace("</head>", js + "</head>")
        f.write_text(html, encoding="utf-8")
        count += 1

print(f"Updated {count} ego pages")
