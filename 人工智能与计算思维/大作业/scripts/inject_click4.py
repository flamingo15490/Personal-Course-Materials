import re
from pathlib import Path

ROOT = Path(r"D:\虚拟C盘\study\人工智能与计算思维大作业")
html_path = ROOT / "任务d" / "network_song_full.html"
html = html_path.read_text(encoding="utf-8")

# Remove ALL old click handlers
html = re.sub(r"<script>\s*\(function\(\).*?</script>", "", html, flags=re.DOTALL)
html = re.sub(r"<script>\s*window\.addEventListener.*?</script>", "", html, flags=re.DOTALL)
html = re.sub(r"<script>\s*var selectedNodeId.*?</script>", "", html, flags=re.DOTALL)

# Inject a minimal test handler directly after </body> before </html>
# Actually, inject right before </html>
js = """<script>
document.addEventListener("DOMContentLoaded", function() {
    // Wait for network to be available
    function init() {
        if (typeof network === "undefined") {
            setTimeout(init, 200);
            return;
        }
        console.log("NETWORK FOUND");
        var selectedNodeId = null;
        
        network.on("click", function(params) {
            console.log("CLICK EVENT", params.nodes.length);
            var nodeIds = network.body.data.nodes.getIds();
            var edgeIds = network.body.data.edges.getIds();
            
            if (params.nodes.length > 0) {
                var nodeId = params.nodes[0];
                console.log("Clicked node:", nodeId);
                
                if (selectedNodeId === nodeId) {
                    // Deselect - restore all
                    selectedNodeId = null;
                    var nodeUpdates = nodeIds.map(function(id) {
                        return {id: id, opacity: 1.0, hidden: false};
                    });
                    var edgeUpdates = edgeIds.map(function(id) {
                        return {id: id, opacity: 1.0, hidden: false, width: 0.3};
                    });
                    network.body.data.nodes.update(nodeUpdates);
                    network.body.data.edges.update(edgeUpdates);
                    network.redraw();
                    console.log("RESET");
                } else {
                    selectedNodeId = nodeId;
                    // Find neighbors
                    var connectedEdges = network.getConnectedEdges(nodeId);
                    var neighborIds = new Set();
                    neighborIds.add(nodeId);
                    connectedEdges.forEach(function(eid) {
                        var edge = network.body.data.edges.get(eid);
                        if (edge) {
                            if (String(edge.from) === String(nodeId)) neighborIds.add(String(edge.to));
                            if (String(edge.to) === String(nodeId)) neighborIds.add(String(edge.from));
                        }
                    });
                    console.log("Neighbors:", neighborIds.size);
                    
                    var nodeUpdates = nodeIds.map(function(id) {
                        var sid = String(id);
                        if (neighborIds.has(sid)) {
                            return {id: id, opacity: 1.0, hidden: false};
                        } else {
                            return {id: id, opacity: 0.05, hidden: false};
                        }
                    });
                    var edgeUpdates = edgeIds.map(function(id) {
                        var edge = network.body.data.edges.get(id);
                        var fromId = String(edge.from);
                        var toId = String(edge.to);
                        if (neighborIds.has(fromId) && neighborIds.has(toId)) {
                            return {id: id, opacity: 0.9, width: 2, hidden: false};
                        } else {
                            return {id: id, opacity: 0.02, width: 0.1, hidden: false};
                        }
                    });
                    network.body.data.nodes.update(nodeUpdates);
                    network.body.data.edges.update(edgeUpdates);
                    network.redraw();
                    console.log("HIGHLIGHTED");
                }
            }
        });
        console.log("Handler attached");
    }
    init();
});
</script>"""

html = html.replace("</body>", js + "\n</body>")
html_path.write_text(html, encoding="utf-8")
print(f"Done! {html_path.stat().st_size // 1024} KB")
