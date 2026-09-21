# -*- coding: utf-8 -*-
"""Part E-1: Song Dynasty Literati Social Circles and Political Factions.

Analyzes the Northern Song New/Old Party strife (c. 1050-1100) through
social-network community detection on CBDB association data.
"""
from __future__ import annotations
import csv, json, warnings
from collections import Counter, defaultdict
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from networkx.algorithms.community import louvain_communities

ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / "output_cbdb_v1"
OUT_DIR = ROOT / "任务e" / "专题1_宋代文人社交圈"
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# Core persons: name -> faction
CORE_PERSONS = {
    "王安石": "新党", "呂惠卿": "新党", "章惇": "新党",
    "司馬光": "旧党", "蘇軾": "旧党", "蘇轍": "旧党",
    "黃庭堅": "旧党", "秦觀": "旧党", "程頤": "旧党",
    "歐陽修": "中立", "曾鞏": "中立", "程顥": "中立",
}

FACTION_COLORS = {"新党": "#E74C3C", "旧党": "#3498DB", "中立": "#9B59B6"}

# Extended relation-type -> 5-category mapping
ASSOC_CATEGORY_MAP = {
    "文學交往": [
        "贈詩、文","收到Y的贈詩、文","獻詩集給Y","被Y獻詩集",
        "唱和","相唱和","同遊","與Y旅遊","從Y遊","與Y遊","送別","被送別",
        "致書Y","被致書由Y","答Y書","收到Y的答書",
        "致Y啓","收到Y的啓","答Y啓","收到Y的答啓",
        "獻文、書于Y","收到Y所獻詩、文、書",
        "為Y所著書作序","書序由Y所作","為Y所著書作跋","書跋由Y所作",
        "為Y所著書題辭","為Y所作詩文作序","詩文序由Y所作","詩文跋由Y所作",
        "為Y之書、畫作跋","書、畫由Y作跋","為Y之收藏作跋","收藏品由Y作跋",
        "為Y之詩文作跋","為Y之書題詞","書之題詞由Y所作","為Y所作詩文作序",
        "為Y作傳","傳由Y所作","傳記作者為Y",
        "為Y作祭文","祭文由Y所作","祭文跋由Y所作","為Y祭文作跋",
        "為Y作哀辭","哀辭由Y所作",
        "為Y作哀辭 [併入167]","哀辭由Y所作[併入166]",
        "挽詩、詞由Y所作","挽詩 ,壽詩/文序被Y所作","為y之挽詩 ,壽詩/文作序",
        "為Y作臨別贈言(送別詩、序)","臨別得到Y所作贈言(送別詩、序)",
        "為Y作硯銘","硯銘由Y所作","為Y作齋、堂銘","齋、堂銘由Y所作",
        "為Y篆匾額、器銘","匾額、器銘由Y所篆",
        "為Y作字說、名述","字說、名述由Y所作","為Y作名說","名說由Y所作",
        "為Y取名、字","名、字由Y所取",
        "為Y作畫贊(畫像記)","畫贊(畫像記)由Y所作",
        "為Y之建築物題詠、記、命名","建築物得到Y的題詠、記、命名",
        "稱道Y之文章、學問","以文章、學問受知於",
        "稱道Y之文風","文風為Y所稱道","稱道Y之節行","節行為Y所稱道",
        "稱道Y的書、畫","書、畫為Y所稱道","稱道Y的詩作","詩作為Y所稱道",
        "文風效法Y","文風為Y所效法","代Y作文","由Y代作文",
        "編輯Y之詩/文","詩/文由Y編輯","編輯Y的學術作品","其學術作品由Y編輯",
        "刊刻Y之著述","著述由Y刊刻","校訂Y之著述","著述由Y校訂",
        "著述為Y所採","採Y之著述","著作被Y評論","評論Y之著作",
        "其著作為Y所研讀","研讀Y的著作","奏錄Y之文","其文為Y所奏錄",
        "其書帖由Y作題","題Y的書帖",
        "相識","同會","為Y作祝詞","祝詞由Y所作",
        "向Y致賀","從Y處收到賀詞 (occasion)",
        "為Y作記","記由Y所作","題Y之畫作","題畫詩文的作者為Y",
        "書風為Y所模仿","模仿Y的書風","畫風師法Y","畫風為Y所師法",
        "為Y作義莊記","義莊記由Y所作","為Y之義莊規矩作序","義莊規矩序由Y所作",
        "為Y之生祠作記","其生祠由Y作記",
        "為Y的墓誌銘書丹","墓誌銘由Y書丹","墓誌銘額篆由Y所作",
        "為Y的墓誌銘作額篆","墓誌銘蓋由Y所書","為Y書墓誌蓋",
        "為Y之神道碑作書","神道碑的書法由Y所作",
        "為Y之神道碑作額篆","神道碑額篆由Y所作",
        "為Y之行狀作跋","行狀跋由Y所作","為Y之墓誌銘作跋","墓誌銘由Y作跋",
        "為Y墓誌銘作序","墓誌銘序由Y所作","為Y墓表作序","墓表序由Y所作",
        "墓表跋由Y所作","為Y神道碑作序","神道碑序由Y所作",
        "為Y神道碑作跋","神道碑跋由Y所作","為Y作碑陰","碑陰為Y所作",
        "為Y墓表作跋","為Y作諡議","諡議由Y所作",
        "為Y家譜作序","家譜由Y作序","為Y家譜作後序","家譜由Y作後序",
        "為Y之家傳作序","家傳序由Y所作","為Y之家傳作跋","家傳跋由Y所作",
        "為Y作家傳","家傳為Y所作","為Y作年譜","年譜由Y所作",
        "為Y作世系碑記","世系碑記由Y所作","為Y作佛寺記","佛寺記由Y所作",
        "為Y作去思碑/記","去思碑/記由Y所作","為Y作德政碑/頌","德政碑/頌由Y所作",
        "為Y作遺愛碑/記","遺愛碑/記由Y所作","為Y作祠記","祠記由Y所作",
        "為Y作道觀記","道觀記由Y所作","為Y作學記（書院記）","學記（書院記）由Y所作",
        "為Y作廟碑記","廟碑記由Y所作","為Y作為Y作壙記","壙記由Y所作",
        "合撰(編)著作","借書給Y","向Y借書",
        "為Y乞某事","某事由Y所乞",
        "為Y舉辦的鄉禮作序","舉辦的鄉禮得到Y所作之序",
        "書諱/填諱由Y所作","為Y書諱/填諱",
        "學術源宗由Y撰寫","為Y撰寫學術源宗",
    ],
    "墓誌傳記": [
        "為Y作墓誌銘","墓誌銘由Y所作","為Y作行狀","行狀由Y所作",
        "為Y作神道碑","神道碑由Y所作","為Y作墓表","墓表由Y所作",
        "為Y作壙記",
        "受Y的請求為他人（第三方）作墓誌銘",
        "受Y的請求為他人（第三方）作神道碑",
        "受Y的請求為他人（第三方）作行狀",
        "受Y請求作墓表","受Y請求作神道碑",
        "求Y為他人（第三方）作墓誌銘",
        "求Y為他人（第三方）作神道碑",
        "求Y為他人（第三方）作行狀",
        "求他人（第三方）為Y作墓誌銘",
        "求他人（第三方）為Y作神道碑",
        "墓誌銘係由Y向他人（第三方）求得",
        "神道碑係由Y向他人（第三方）求得",
        "向Y求墓表","向Y求神道碑",
        "為Y的神道碑/墓誌/壙誌刊/刻石",
        "神道碑/墓誌/壙誌由Y刊/刻石",
        "墓由Y題","題Y之墓","墓/碑石由 Y 所立","為 Y 墓/碑立石",
        "為Y所葬","葬",
    ],
    "師生": [
        "為Y之學生","學生為Y","為Y之門人","門人為Y",
        "為Y之弟子","弟子為Y","為Y之法嗣","法嗣為Y",
        "為 Y 的門孫 (門人之門人)","門孫 (門人之門人) 為Y","門人為Y之後代",
        "對Y執弟子禮","受Y之弟子禮","從Y學","教授Y","教授Y之學",
        "傳Y之學","其學由Y所傳","其學由Y傳授學生",
        "傳經於Y","受經於Y","宗Y之學","其學為Y所宗",
        "私淑Y之學","其學為Y所私淑","同學、同門",
        "為Y學派的成員","該學派的成員為Y","其後代出於Y之門",
        "其志業由Y傳承","以Y之志業自任","指教Y",
        "為Y所聘執教官學、書院","聘Y執教官學、書院",
        "為Y所聘執教族學","聘Y執教族學","主Y家之教席","聘Y主家之教席",
        "向Y問學","研修理學","其學得到Y之讚揚","讚揚Y之學",
    ],
    "友人": [
        "友","同年友","同僚","鄰居","同鄉","同道","相識",
        "同場屋/同應舉",
        "世交父執為Y","為Y之世交父執","禮待","受Y之禮待",
        "拜訪","受到Y拜訪","贈Y物","受Y之贈物",
        "為友人提供幫助","得到友人Y之幫助","結義",
    ],
}

# Build reverse lookup
DESC_TO_CATEGORY = {}
for _cat, _dd in ASSOC_CATEGORY_MAP.items():
    for _d in _dd:
        DESC_TO_CATEGORY[_d] = _cat

CATEGORY_ORDER = ["文學交往", "墓誌傳記", "師生", "友人", "其他"]
CATEGORY_COLORS = {
    "文學交往": "#4C78A8", "墓誌傳記": "#72B7B2", "師生": "#F58518",
    "友人": "#54A24B", "其他": "#B279A2",
}

# ======================================================================
# Step 1: Build Song Dynasty social network
# ======================================================================
def load_person_map():
    print("[Step 1] Loading dim_person.csv ...")
    pm = {}
    df = pd.read_csv(IN_DIR / "dim_person.csv",
        usecols=["c_personid","c_name_chn","dynasty_chn"],
        dtype={"c_personid":int}, encoding="utf-8", on_bad_lines="skip")
    for _, row in df.iterrows():
        pid = int(row["c_personid"])
        name = str(row["c_name_chn"]) if pd.notna(row["c_name_chn"]) else ""
        dyn = str(row["dynasty_chn"]) if pd.notna(row["dynasty_chn"]) else ""
        pm[pid] = (name, dyn)
    print(f"  Loaded {len(pm):,} persons")
    return pm

def build_song_graph(person_map):
    print("[Step 1] Loading fact_person_assoc.csv ...")
    song_ids = {pid for pid, (_, dyn) in person_map.items() if dyn == "宋"}
    print(f"  Song dynasty persons: {len(song_ids):,}")
    df = pd.read_csv(IN_DIR / "fact_person_assoc.csv",
        usecols=["c_personid","c_assoc_id","c_assoc_desc_chn"],
        dtype={"c_personid":int,"c_assoc_id":int}, encoding="utf-8", on_bad_lines="skip")
    total = len(df)
    df = df[(df["c_personid"].isin(song_ids)) & (df["c_assoc_id"].isin(song_ids))
            & (df["c_assoc_desc_chn"] != "未詳")].copy()
    print(f"  Filtered: {total} -> {len(df)} edges")
    edge_map = {}
    for _, row in df.iterrows():
        a, b = int(row["c_personid"]), int(row["c_assoc_id"])
        key = (min(a,b), max(a,b))
        desc = str(row["c_assoc_desc_chn"])
        if key not in edge_map:
            edge_map[key] = set()
        edge_map[key].add(desc)
    G = nx.Graph()
    for (a,b), types in edge_map.items():
        cats = set(DESC_TO_CATEGORY.get(t, "其他") for t in types)
        G.add_edge(a, b, types=types, categories=cats, type_count=len(types))
    print(f"  Built graph: {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges")
    return G

# ======================================================================
# Step 2: Core persons & social circles
# ======================================================================
def lookup_core_persons(person_map):
    print("[Step 2] Looking up core persons ...")
    name_index = {}
    for pid, (name, dyn) in person_map.items():
        if dyn == "宋":
            name_index[name] = pid
    resolved = {}
    for name, faction in CORE_PERSONS.items():
        if name in name_index:
            resolved[name_index[name]] = (name, faction)
            print(f"  {name} -> id={name_index[name]} (exact)")
            continue
        matches = [(pid, pname) for pname, pid in name_index.items() if name in pname]
        if matches:
            matches.sort(key=lambda x: x[0])
            pid, pname = matches[0]
            resolved[pid] = (pname, faction)
            print(f"  {name} -> id={pid} (fuzzy: '{pname}')")
        else:
            warnings.warn(f"Core person '{name}' not found in dim_person")
    print(f"  Resolved {len(resolved)}/{len(CORE_PERSONS)}")
    return resolved

def extract_core_subgraph(G, core_info):
    print("[Step 2] Extracting core circle subgraph ...")
    core_nodes = set(core_info.keys())
    neighbors = set()
    for pid in core_nodes:
        if pid in G:
            neighbors |= set(G.neighbors(pid))
    subG = G.subgraph(core_nodes | neighbors).copy()
    print(f"  Core subgraph: {subG.number_of_nodes():,} nodes, {subG.number_of_edges():,} edges")
    return subG

def compute_core_stats(G, core_info, partition):
    print("[Step 2] Computing core person stats ...")
    new_ids = {p for p,(_,f) in core_info.items() if f == "新党"}
    old_ids = {p for p,(_,f) in core_info.items() if f == "旧党"}
    rows = []
    for pid, (name, faction) in sorted(core_info.items()):
        if pid not in G:
            rows.append({"personid":pid,"name":name,"faction":faction,
                "degree":0,"community":-1,
                "文学交往":0,"墓誌传记":0,"师生":0,"友人":0,"其他":0,
                "cross_new":0,"cross_old":0})
            continue
        deg = G.degree(pid)
        cat_counts = {c:0 for c in CATEGORY_ORDER}
        for nbr in G.neighbors(pid):
            for c in G[pid][nbr].get("categories", {"其他"}):
                cat_counts[c] = cat_counts.get(c, 0) + 1
        comm = partition.get(pid, -1)
        cross_new = sum(1 for nbr in G.neighbors(pid) if nbr in new_ids and faction != "新党")
        cross_old = sum(1 for nbr in G.neighbors(pid) if nbr in old_ids and faction != "旧党")
        if faction == "中立":
            cross_new = sum(1 for nbr in G.neighbors(pid) if nbr in new_ids)
            cross_old = sum(1 for nbr in G.neighbors(pid) if nbr in old_ids)
        rows.append({"personid":pid,"name":name,"faction":faction,"degree":deg,
            "community":comm,
            "文学交往":cat_counts["文學交往"],"墓誌传记":cat_counts["墓誌傳記"],
            "师生":cat_counts["師生"],"友人":cat_counts["友人"],"其他":cat_counts["其他"],
            "cross_new_connections":cross_new,"cross_old_connections":cross_old})
    return rows

# ======================================================================
# Step 3: Community detection & faction analysis
# ======================================================================
def run_community_detection(G_song):
    print("[Step 3] Community detection (Louvain) on Song LCC ...")
    components = list(nx.connected_components(G_song))
    lcc_nodes = max(components, key=len)
    G_lcc = G_song.subgraph(lcc_nodes).copy()
    print(f"  LCC: {G_lcc.number_of_nodes():,} nodes, {G_lcc.number_of_edges():,} edges")
    communities = louvain_communities(G_lcc, seed=42)
    comm_sizes = sorted(enumerate(communities), key=lambda x: -len(x[1]))
    partition = {}
    for new_idx, (_, members) in enumerate(comm_sizes):
        for node in members:
            partition[node] = new_idx
    num_communities = len(communities)
    comm_list = [set() for _ in range(num_communities)]
    for node, cid in partition.items():
        comm_list[cid].add(node)
    modularity = nx.community.modularity(G_lcc, comm_list)
    print(f"  Found {num_communities} communities, modularity={modularity:.4f}")
    return G_lcc, partition, num_communities, modularity

def analyze_faction_community(G_lcc, partition, core_info):
    print("[Step 3] Analyzing faction-community alignment ...")
    was_id = smg_id = sush_id = None
    for pid, (name, _) in core_info.items():
        if name == "王安石": was_id = pid
        elif name == "司馬光": smg_id = pid
        elif name == "蘇軾": sush_id = pid
    result = {}
    was_comm = partition.get(was_id, -1) if was_id else -1
    smg_comm = partition.get(smg_id, -1) if smg_id else -1
    sush_comm = partition.get(sush_id, -1) if sush_id else -1
    result["wang_anshi_community"] = was_comm
    result["sima_guang_community"] = smg_comm
    result["su_shi_community"] = sush_comm
    result["wang_vs_sima_same"] = (was_comm == smg_comm) if was_comm >= 0 else None
    result["wang_vs_su_same"] = (was_comm == sush_comm) if was_comm >= 0 else None
    if was_comm >= 0 and smg_comm >= 0 and was_comm != smg_comm:
        was_nodes = {n for n,c in partition.items() if c == was_comm}
        smg_nodes = {n for n,c in partition.items() if c == smg_comm}
        inter = sum(1 for u,v in G_lcc.edges()
                    if (u in was_nodes and v in smg_nodes) or (u in smg_nodes and v in was_nodes))
        poss = len(was_nodes) * len(smg_nodes)
        result["density_between_camps"] = round(inter / poss, 8) if poss > 0 else 0
        result["density_within_wang_comm"] = round(nx.density(G_lcc.subgraph(was_nodes)), 8)
        result["density_within_sima_comm"] = round(nx.density(G_lcc.subgraph(smg_nodes)), 8)
    print(f"  Wang Anshi comm: {was_comm}, Sima Guang comm: {smg_comm}, Su Shi comm: {sush_comm}")
    return result

def find_cross_camp_persons(G_song, core_info, person_map):
    print("[Step 3] Finding cross-camp bridge persons ...")
    new_ids = {p for p,(_,f) in core_info.items() if f == "新党"}
    old_ids = {p for p,(_,f) in core_info.items() if f == "旧党"}
    core_ids = set(core_info.keys())
    cross = []
    for node in G_song.nodes():
        if node in core_ids:
            continue
        n_nbrs = set(G_song.neighbors(node))
        has_new = bool(n_nbrs & new_ids)
        has_old = bool(n_nbrs & old_ids)
        if has_new and has_old:
            rel_types = []
            for nbr in n_nbrs & (new_ids | old_ids):
                for t in G_song[node][nbr].get("types", set()):
                    rel_types.append(t)
            top_types = [t for t,_ in Counter(rel_types).most_common(5)]
            name, _ = person_map.get(node, (str(node), ""))
            cross.append({"personid":node,"name":name,"degree":G_song.degree(node),
                "new_camp_connections":len(n_nbrs & new_ids),
                "old_camp_connections":len(n_nbrs & old_ids),
                "main_relation_types":"; ".join(top_types)})
    cross.sort(key=lambda x: -(x["new_camp_connections"] + x["old_camp_connections"]))
    print(f"  Found {len(cross)} cross-camp bridge persons")
    return cross

# ======================================================================
# Step 4: Relation type analysis by faction
# ======================================================================
def analyze_relation_by_faction(G_song, core_info):
    print("[Step 4] Analyzing relation types by faction ...")
    new_ids = {p for p,(_,f) in core_info.items() if f == "新党"}
    old_ids = {p for p,(_,f) in core_info.items() if f == "旧党"}
    def circle_cats(center_ids):
        cats = Counter()
        for pid in center_ids:
            if pid not in G_song: continue
            for nbr in G_song.neighbors(pid):
                for c in G_song[pid][nbr].get("categories", {"其他"}):
                    cats[c] += 1
        return cats
    nc = circle_cats(new_ids)
    oc = circle_cats(old_ids)
    result = {"new_party":{}, "old_party":{}}
    for cat in CATEGORY_ORDER:
        result["new_party"][cat] = nc.get(cat, 0)
        result["old_party"][cat] = oc.get(cat, 0)
    tn = sum(result["new_party"].values())
    to = sum(result["old_party"].values())
    if tn > 0:
        result["new_party_pct"] = {k:round(v/tn*100,1) for k,v in result["new_party"].items()}
    if to > 0:
        result["old_party_pct"] = {k:round(v/to*100,1) for k,v in result["old_party"].items()}
    print("  New:", result.get("new_party_pct", result["new_party"]))
    print("  Old:", result.get("old_party_pct", result["old_party"]))
    return result

# ======================================================================
# Step 5: Visualizations
# ======================================================================
def viz_core_network(G_song, core_info, out_path):
    print("[Step 5] Drawing core_network.png ...")
    core_ids = set(core_info.keys())
    keep = set()
    for pid in core_ids:
        if pid in G_song:
            keep.add(pid)
            keep |= set(G_song.neighbors(pid))
    subG = G_song.subgraph(keep).copy()
    pm = {}
    df = pd.read_csv(IN_DIR / "dim_person.csv", usecols=["c_personid","c_name_chn"],
        dtype={"c_personid":int}, encoding="utf-8", on_bad_lines="skip")
    for _, r in df.iterrows():
        pm[int(r["c_personid"])] = str(r["c_name_chn"]) if pd.notna(r["c_name_chn"]) else ""
    node_colors = [FACTION_COLORS[core_info[n][1]] if n in core_info else "#CCCCCC" for n in subG.nodes()]
    degrees = [subG.degree(n) for n in subG.nodes()]
    max_deg = max(degrees) if degrees else 1
    node_sizes = [max(8, 100 * (d / max_deg) ** 0.5 * 2) for d in degrees]
    edge_widths = [max(0.3, min(3.0, subG[u][v].get("type_count",1) * 0.3)) for u,v in subG.edges()]
    fig, ax = plt.subplots(figsize=(18, 14))
    pos = nx.spring_layout(subG, k=2.0, iterations=100, seed=42)
    nx.draw_networkx_edges(subG, pos, ax=ax, alpha=0.15, width=edge_widths, edge_color="#999999")
    nx.draw_networkx_nodes(subG, pos, ax=ax, node_size=node_sizes, node_color=node_colors, alpha=0.8)
    labels = {pid: pm.get(pid, str(pid)) for pid in core_ids if pid in subG}
    nx.draw_networkx_labels(subG, pos, labels=labels, ax=ax, font_size=10, font_weight="bold",
                            font_family="Microsoft YaHei")
    ax.set_title("北宋新旧党争核心圈网络图", fontsize=16, fontweight="bold")
    for faction, color in FACTION_COLORS.items():
        ax.scatter([], [], c=color, s=80, label=faction)
    ax.scatter([], [], c="#CCCCCC", s=40, label="一度邻居")
    ax.legend(loc="upper left", fontsize=11)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out_path.name} ({out_path.stat().st_size // 1024} KB)")

def viz_community_heatmap(G_lcc, partition, core_info, out_path):
    print("[Step 5] Drawing community_party_heatmap.png ...")
    comm_sizes = Counter(partition.values())
    top_comms = [c for c,_ in comm_sizes.most_common(10)]
    factions = ["新党","旧党","中立"]
    matrix = np.zeros((3, len(top_comms)), dtype=int)
    for node, cid in partition.items():
        if node not in core_info: continue
        _, faction = core_info[node]
        if cid in top_comms and faction in factions:
            matrix[factions.index(faction), top_comms.index(cid)] += 1
    fig, ax = plt.subplots(figsize=(12, 4))
    im = ax.imshow(matrix, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(top_comms)))
    ax.set_xticklabels([f"C{c}\n({comm_sizes[c]}人)" for c in top_comms], fontsize=10)
    ax.set_yticks(range(3))
    ax.set_yticklabels(factions, fontsize=12)
    for i in range(3):
        for j in range(len(top_comms)):
            v = matrix[i,j]
            if v > 0:
                ax.text(j, i, str(v), ha="center", va="center", fontsize=12, fontweight="bold")
    ax.set_title("核心人物阵营 vs Louvain 社区分布", fontsize=14, fontweight="bold")
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out_path.name} ({out_path.stat().st_size // 1024} KB)")

def viz_relation_comparison(relation_analysis, out_path):
    print("[Step 5] Drawing relation_type_comparison.png ...")
    new_pct = relation_analysis.get("new_party_pct", relation_analysis.get("new_party", {}))
    old_pct = relation_analysis.get("old_party_pct", relation_analysis.get("old_party", {}))
    cats = CATEGORY_ORDER
    new_vals = [new_pct.get(c, 0) for c in cats]
    old_vals = [old_pct.get(c, 0) for c in cats]
    x = np.arange(len(cats))
    width = 0.35
    fig, ax = plt.subplots(figsize=(10, 6))
    bars1 = ax.bar(x - width/2, new_vals, width, label="新党核心圈", color="#E74C3C", alpha=0.85)
    bars2 = ax.bar(x + width/2, old_vals, width, label="旧党核心圈", color="#3498DB", alpha=0.85)
    ax.set_ylabel("占比 (%)", fontsize=12)
    ax.set_title("新党 vs 旧党核心圈关系类型分布对比", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=11)
    ax.legend(fontsize=11)
    for bars in [bars1, bars2]:
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width()/2, h + 0.3, f"{h:.1f}%",
                        ha="center", va="bottom", fontsize=9)
    ymax = max(max(new_vals), max(old_vals)) if new_vals else 100
    ax.set_ylim(0, ymax * 1.15)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out_path.name} ({out_path.stat().st_size // 1024} KB)")

# ======================================================================
# Step 6: Write outputs
# ======================================================================
def write_cross_camp_csv(cross, out_path):
    fields = ["personid","name","degree","new_camp_connections","old_camp_connections","main_relation_types"]
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(cross)
    print(f"  Saved {out_path.name} ({len(cross)} rows)")

def write_core_stats_csv(rows, out_path):
    fields = ["personid","name","faction","degree","community",
        "文学交往","墓誌传记","师生","友人","其他","cross_new_connections","cross_old_connections"]
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"  Saved {out_path.name} ({len(rows)} rows)")

def write_summary_json(summary, out_path):
    with open(out_path, "w", encoding="utf-8-sig") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"  Saved {out_path.name}")

def write_readme(summary, core_rows, cross, relation_analysis, out_path):
    was_sep = summary.get("wang_vs_sima_same") is False
    mod = summary.get("modularity", "?")
    num_comm = summary.get("num_communities", "?")
    lines = [
        "# 任务 E-1：宋代文人社交圈与政治命运", "",
        "## 分析目标",
        "聚焦北宋新旧党争时期（约 1050-1100 年），分析以王安石（新党）和司馬光/蘇軾（旧党）",
        "为核心的社交圈是否在数据上呈现为两个独立社区，量化『政治派系』在社会关系网络中的结构特征。",
        "", "## 数据概况",
        f"- 宋代社会网络节点数：{summary.get('song_nodes', '?'):,}",
        f"- 宋代社会网络边数：{summary.get('song_edges', '?'):,}",
        f"- 最大连通分量节点数：{summary.get('lcc_nodes', '?'):,}",
        f"- Louvain 社区数：{num_comm}",
        f"- 模块度 (modularity)：{mod}",
        "", "## 核心发现", "",
    ]
    if was_sep:
        lines += ["### 1. 王安石与司馬光/蘇軾确实处于不同社区",
            f"- 王安石所在社区：C{summary.get('wang_anshi_community', '?')}",
            f"- 司馬光所在社区：C{summary.get('sima_guang_community', '?')}",
            f"- 蘇軾所在社区：C{summary.get('su_shi_community', '?')}",
            "", "这表明北宋新旧党争的社会关系结构在数据中确实呈现为两个独立社区。"]
    else:
        lines += ["### 1. 王安石与司馬光/蘇軾在同一社区",
            "数据中他们处于同一社区，可能是因为直接交往导致的紧密连接。"]
    if "density_between_camps" in summary:
        lines += ["", "### 2. 社区间密度对比",
            f"- 两社区之间的边密度：{summary['density_between_camps']}",
            f"- 王安石社区内部密度：{summary['density_within_wang_comm']}",
            f"- 司馬光社区内部密度：{summary['density_within_sima_comm']}"]
    lines += ["", f"### 3. 跨阵营连接人物",
        f"共有 **{len(cross)}** 位人物同时与新党和旧党核心成员有直接交往。"]
    if cross:
        lines.append("最重要的跨阵营人物：")
        for c in cross[:5]:
            lines.append(f"- {c['name']}（ID={c['personid']}）：与新党{c['new_camp_connections']}人、旧党{c['old_camp_connections']}人有交往")
    new_pct = relation_analysis.get("new_party_pct", {})
    old_pct = relation_analysis.get("old_party_pct", {})
    lines += ["", "### 4. 关系类型差异",
        "| 关系类型 | 新党核心圈 (%) | 旧党核心圈 (%) |",
        "|----------|---------------|---------------|"]
    for cat in CATEGORY_ORDER:
        lines.append(f"| {cat} | {new_pct.get(cat, 0)} | {old_pct.get(cat, 0)} |")
    lines += ["", "## 输出文件", "| 文件 | 说明 |", "|------|------|",
        "| core_network.png | 党争核心圈网络图 |",
        "| community_party_heatmap.png | 社区-阵营热力图 |",
        "| relation_type_comparison.png | 关系类型分布对比 |",
        "| cross_camp_persons.csv | 跨阵营连接人物表 |",
        "| core_person_stats.csv | 核心人物统计 |",
        "| analysis_summary.json | 分析摘要 |", ""]
    with open(out_path, "w", encoding="utf-8-sig") as f:
        f.write("\n".join(lines))
    print(f"  Saved {out_path.name}")

# ======================================================================
# Main
# ======================================================================
def main():
    print("=" * 60)
    print("Part E-1: Song Dynasty Literati Social Circles")
    print("=" * 60)
    person_map = load_person_map()
    G_song = build_song_graph(person_map)
    core_info = lookup_core_persons(person_map)
    G_lcc, partition, num_comm, modularity = run_community_detection(G_song)
    faction_analysis = analyze_faction_community(G_lcc, partition, core_info)
    cross_camp = find_cross_camp_persons(G_song, core_info, person_map)
    core_rows = compute_core_stats(G_song, core_info, partition)
    relation_analysis = analyze_relation_by_faction(G_song, core_info)
    viz_core_network(G_song, core_info, OUT_DIR / "core_network.png")
    viz_community_heatmap(G_lcc, partition, core_info, OUT_DIR / "community_party_heatmap.png")
    viz_relation_comparison(relation_analysis, OUT_DIR / "relation_type_comparison.png")
    print("[Step 6] Writing output files ...")
    write_cross_camp_csv(cross_camp, OUT_DIR / "cross_camp_persons.csv")
    write_core_stats_csv(core_rows, OUT_DIR / "core_person_stats.csv")
    summary = {
        "song_nodes": G_song.number_of_nodes(),
        "song_edges": G_song.number_of_edges(),
        "lcc_nodes": G_lcc.number_of_nodes(),
        "num_communities": num_comm,
        "modularity": round(modularity, 6),
        "core_persons_found": len(core_info),
        "cross_camp_count": len(cross_camp),
        **faction_analysis,
        "relation_comparison": relation_analysis,
    }
    write_summary_json(summary, OUT_DIR / "analysis_summary.json")
    write_readme(summary, core_rows, cross_camp, relation_analysis, OUT_DIR / "README.md")
    print("=" * 60)
    print("Done! All outputs in:", OUT_DIR)
    print("=" * 60)

if __name__ == "__main__":
    main()
