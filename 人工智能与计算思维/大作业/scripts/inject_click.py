import json, re
from pathlib import Path

ROOT = Path(r"D:\虚拟C盘\study\人工智能与计算思维大作业")
OUT_DIR = ROOT / "任务d"
html_path = OUT_DIR / "network_song_full.html"
html = html_path.read_text(encoding="utf-8")

# Remove any existing click handler script block
html = re.sub(r"<script>\s*var top50_href.*?</script>", "", html, flags=re.DOTALL)

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
js += '        if (neighbors.has(nid)) {\n'
js += '            return Object.assign({}, n, {opacity: 1.0});\n'
js += '        } else {\n'
js += '            return Object.assign({}, n, {opacity: 0.05});\n'
js += '        }\n'
js += '    });\n'
js += '    var newEdges = origEdges.map(function(e) {\n'
js += '        var fromId = String(e.from), toId = String(e.to);\n'
js += '        if (neighbors.has(fromId) && neighbors.has(toId)) {\n'
js += '            return Object.assign({}, e, {opacity: 0.8, width: 2});\n'
js += '        } else {\n'
js += '            return Object.assign({}, e, {opacity: 0.02, width: 0.2});\n'
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
js += '            selectedNodeId = null;\n'
js += '            resetAll();\n'
js += '        } else {\n'
js += '            selectedNodeId = nodeId;\n'
js += '            highlightNode(nodeId);\n'
js += '        }\n'
js += '    } else {\n'
js += '        if (selectedNodeId) {\n'
js += '            selectedNodeId = null;\n'
js += '            resetAll();\n'
js += '        }\n'
js += '    }\n'
js += '});\n'
js += '</script>\n'

html = html.replace("</head>", js + "</head>")
html_path.write_text(html, encoding="utf-8")
print(f"Done. Size: {html_path.stat().st_size // 1024} KB")
