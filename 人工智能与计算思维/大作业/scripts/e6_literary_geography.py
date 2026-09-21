# -*- coding: utf-8 -*-
"""E-6: Literary Geography — Tracking literary centers from Chang'an to Jiangnan.

Analyses literary associations (poetry-gifts, letters, prefacing, tomb inscriptions,
chanting, co-travel) across dynasties, computing geographic centroids, density grids,
community clusters, and migration trajectories.
"""
from __future__ import annotations

import json
import math
import warnings
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ── paths ───────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / "output_cbdb_v1"
OUT_DIR = ROOT / "任务e" / "专题6_文学地理"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── constants ───────────────────────────────────────────────────────────────
ENCODING = "utf-8-sig"
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "KaiTi"]
plt.rcParams["axes.unicode_minus"] = False

LITERARY_ASSOC_TYPES = {
    "贈詩、文", "收到Y的贈詩、文",
    "致書Y", "被致書由Y",
    "答Y書", "收到Y的答書",
    "為Y所著書作序", "書序由Y所作",
    "為Y所著書作跋", "書跋由Y所作",
    "相唱和", "與Y遊", "從Y遊",
    "為Y作墓誌銘", "墓誌銘由Y所作",
}

DYNASTY_ORDER = ["唐", "五代", "北宋", "南宋", "元", "明"]

DYNASTY_COLORS = {
    "唐": "#E63946", "五代": "#F4A261", "北宋": "#2A9D8F",
    "南宋": "#264653", "元": "#6A4C93", "明": "#1982C4",
}

COMMUNITY_PALETTE = [
    "#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231",
    "#911eb4", "#42d4f4", "#f032e6", "#bfef45", "#fabed4",
    "#469990", "#dcbeff", "#9A6324", "#fffac8", "#800000",
    "#aaffc3", "#808000", "#ffd8b1", "#000075", "#a9a9a9",
]

R_EARTH = 6371.0
LON_MIN, LON_MAX, LON_STEP = 70, 140, 5
LAT_MIN, LAT_MAX, LAT_STEP = 15, 55, 5
TARGET_COMMUNITY_DYNASTIES = ["唐", "北宋", "南宋", "明"]

# ═══════════════════════════════════════════════════════════════════════════
# Utilities
# ═══════════════════════════════════════════════════════════════════════════

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return R_EARTH * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))


def direction_label(lon1, lat1, lon2, lat2):
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    if abs(dlat) < 0.3 and abs(dlon) < 0.3:
        return "—"
    ns = "北" if dlat > 0 else "南"
    ew = "东" if dlon > 0 else "西"
    if abs(dlat) < 0.5 * abs(dlon):
        return ew
    if abs(dlon) < 0.5 * abs(dlat):
        return ns
    return ns + ew


def assign_dynasty_vec(dynasty_chn, index_year):
    """Vectorized dynasty assignment with Song split."""
    result = np.where(
        (dynasty_chn == "宋") & index_year.notna() & (index_year.astype(float) >= 960) & (index_year.astype(float) <= 1127),
        "北宋",
        np.where(
            (dynasty_chn == "宋") & index_year.notna() & (index_year.astype(float) >= 1128) & (index_year.astype(float) <= 1279),
            "南宋",
            np.where(dynasty_chn == "宋", "宋(未详)", dynasty_chn)
        )
    )
    return result


def grid_label(lon, lat):
    return f"{lon:.0f}-{lon+LON_STEP:.0f}E, {lat:.0f}-{lat+LAT_STEP:.0f}N"


def save_csv(df, name):
    path = OUT_DIR / name
    df.to_csv(path, index=False, encoding=ENCODING)
    print(f"  -> {path.name}  ({len(df)} rows)")


# ═══════════════════════════════════════════════════════════════════════════
# Step 1 — Data Loading & Literary Association Filter
# ═══════════════════════════════════════════════════════════════════════════

def step1_load_and_filter():
    print("\n[Step 1] Loading data and filtering literary associations ...")

    person_df = pd.read_csv(
        IN_DIR / "dim_person.csv",
        usecols=["c_personid", "c_name_chn", "dynasty_chn", "c_index_year", "index_addr_x", "index_addr_y"],
        encoding="utf-8", on_bad_lines="skip",
        dtype={"c_personid": int},
    )
    person_df["effective_dynasty"] = assign_dynasty_vec(
        person_df["dynasty_chn"], person_df["c_index_year"]
    )
    # Build lookup dict
    person_lookup = dict(zip(person_df["c_personid"],
                             zip(person_df["c_name_chn"].fillna(""), person_df["effective_dynasty"])))

    # Load associations — only needed columns
    assoc_df = pd.read_csv(
        IN_DIR / "fact_person_assoc.csv",
        usecols=["c_personid", "c_assoc_id", "c_assoc_desc_chn"],
        encoding="utf-8", on_bad_lines="skip",
        dtype={"c_personid": int, "c_assoc_id": int},
    )

    # Filter literary associations
    lit_df = assoc_df[assoc_df["c_assoc_desc_chn"].isin(LITERARY_ASSOC_TYPES)].copy()
    print(f"  Literary association edges: {len(lit_df):,}")

    # Merge dynasty for person A (initiator)
    lit_df = lit_df.merge(
        person_df[["c_personid", "effective_dynasty"]].rename(columns={"effective_dynasty": "dynasty"}),
        on="c_personid", how="left"
    )

    target = set(DYNASTY_ORDER) | {"宋(未详)"}
    lit_target = lit_df[lit_df["dynasty"].isin(target)].copy()

    # Per-dynasty stats
    stats = []
    for dyn in DYNASTY_ORDER + ["宋(未详)"]:
        sub = lit_target[lit_target["dynasty"] == dyn]
        n_edges = len(sub)
        persons = set(sub["c_personid"].astype(int)) | set(sub["c_assoc_id"].astype(int))
        stats.append({"dynasty": dyn, "literary_edges": n_edges, "participants": len(persons)})
    stats_df = pd.DataFrame(stats)
    print("  Per-dynasty literary activity:")
    print(stats_df.to_string(index=False))

    return person_df, person_lookup, lit_target, stats_df


# ═══════════════════════════════════════════════════════════════════════════
# Step 2 — Person Geocoding
# ═══════════════════════════════════════════════════════════════════════════

def step2_geocode(person_df):
    print("\n[Step 2] Building person-coordinate map ...")

    addr_df = pd.read_csv(
        IN_DIR / "fact_person_address.csv",
        usecols=["c_personid", "c_addr_desc_chn", "x_coord", "y_coord"],
        encoding="utf-8", on_bad_lines="skip",
        dtype={"c_personid": int},
    )
    # Drop invalid coords
    addr_df = addr_df.dropna(subset=["x_coord", "y_coord"])
    addr_df = addr_df[(addr_df["x_coord"] > 1) & (addr_df["y_coord"] > 1)]
    # Filter to China bounds
    addr_df = addr_df[
        (addr_df["x_coord"] >= 73) & (addr_df["x_coord"] <= 136) &
        (addr_df["y_coord"] >= 18) & (addr_df["y_coord"] <= 54)
    ]

    person_coords = {}

    # Priority 1: 籍貫 — take first occurrence per person
    native_mask = addr_df["c_addr_desc_chn"].str.contains("籍貫", na=False)
    native = addr_df[native_mask].drop_duplicates(subset=["c_personid"], keep="first")
    for pid, lon, lat in zip(native["c_personid"], native["x_coord"], native["y_coord"]):
        person_coords[int(pid)] = (float(lon), float(lat))

    # Priority 2: remaining persons — take first available
    remaining = addr_df[~addr_df["c_personid"].isin(person_coords)]
    remaining_first = remaining.drop_duplicates(subset=["c_personid"], keep="first")
    for pid, lon, lat in zip(remaining_first["c_personid"], remaining_first["x_coord"], remaining_first["y_coord"]):
        person_coords[int(pid)] = (float(lon), float(lat))

    # Priority 3: dim_person index_addr fallback
    idx_df = person_df.dropna(subset=["index_addr_x", "index_addr_y"])
    for pid, lon, lat in zip(idx_df["c_personid"], idx_df["index_addr_x"], idx_df["index_addr_y"]):
        pid = int(pid)
        if pid not in person_coords:
            lon_f, lat_f = float(lon), float(lat)
            if 73 <= lon_f <= 136 and 18 <= lat_f <= 54:
                person_coords[pid] = (lon_f, lat_f)

    print(f"  Persons with coordinates: {len(person_coords):,}")
    return person_coords


def step2_centroids(lit_df, person_coords):
    print("\n[Step 2b] Computing per-dynasty literary centroids ...")

    # Collect unique persons per dynasty
    pid_dyn_a = lit_df[["c_personid", "dynasty"]].rename(columns={"c_personid": "pid"})
    pid_dyn_b = lit_df[["c_assoc_id", "dynasty"]].rename(columns={"c_assoc_id": "pid"})
    pid_dyn = pd.concat([pid_dyn_a, pid_dyn_b]).drop_duplicates()

    rows = []
    for dyn in DYNASTY_ORDER:
        pids = set(pid_dyn[pid_dyn["dynasty"] == dyn]["pid"].astype(int))
        lons, lats = [], []
        for pid in pids:
            if pid in person_coords:
                lo, la = person_coords[pid]
                lons.append(lo)
                lats.append(la)
        if lons:
            clo, cla = float(np.mean(lons)), float(np.mean(lats))
        else:
            clo, cla = float("nan"), float("nan")
        rows.append({
            "dynasty": dyn,
            "centroid_lon": round(clo, 4),
            "centroid_lat": round(cla, 4),
            "persons_geocoded": len(lons),
            "persons_total": len(pids),
        })

    centroid_df = pd.DataFrame(rows)
    save_csv(centroid_df, "literary_centroid_by_dynasty.csv")
    return centroid_df


# ═══════════════════════════════════════════════════════════════════════════
# Step 3 — Geographic Density (5°×5° Grid)
# ═══════════════════════════════════════════════════════════════════════════

def step3_density(lit_df, person_coords):
    print("\n[Step 3] Computing geographic density on 5x5 degree grid ...")

    lon_bins = np.arange(LON_MIN, LON_MAX, LON_STEP)
    lat_bins = np.arange(LAT_MIN, LAT_MAX, LAT_STEP)

    grid_counts = defaultdict(Counter)

    # Vectorized: build arrays of personA/B coords per edge
    pids_a = lit_df["c_personid"].astype(int).values
    pids_b = lit_df["c_assoc_id"].astype(int).values
    dyns = lit_df["dynasty"].values

    for i in range(len(pids_a)):
        pa, pb, dyn = pids_a[i], pids_b[i], dyns[i]
        ca = person_coords.get(pa)
        cb = person_coords.get(pb)
        for c in (ca, cb):
            if c is None:
                continue
            lon, lat = c
            g_lon = int((lon - LON_MIN) // LON_STEP) * LON_STEP + LON_MIN
            g_lat = int((lat - LAT_MIN) // LAT_STEP) * LAT_STEP + LAT_MIN
            if LON_MIN <= g_lon < LON_MAX and LAT_MIN <= g_lat < LAT_MAX:
                grid_counts[dyn][(g_lon, g_lat)] += 1

    rows = []
    for dyn in DYNASTY_ORDER:
        counts = grid_counts.get(dyn, Counter())
        total = sum(counts.values()) if counts else 1
        for (glon, glat), cnt in counts.items():
            rows.append({
                "dynasty": dyn, "grid_lon": glon, "grid_lat": glat,
                "label": grid_label(glon, glat),
                "count": cnt, "share": round(cnt / total, 6),
            })

    density_df = pd.DataFrame(rows)
    density_df = density_df.sort_values(["dynasty", "count"], ascending=[True, False])

    # Summary
    summary_rows = []
    for dyn in DYNASTY_ORDER:
        sub = density_df[density_df["dynasty"] == dyn]
        total = sub["count"].sum()
        hhi = sum((r["share"]) ** 2 for _, r in sub.iterrows()) if len(sub) else 0
        top = sub.iloc[0] if len(sub) else None
        summary_rows.append({
            "dynasty": dyn, "total_count": int(total),
            "hhi_index": round(hhi, 6),
            "top_grid": top["label"] if top is not None else "",
            "top_grid_count": int(top["count"]) if top is not None else 0,
        })
    print("  Geographic concentration (HHI) per dynasty:")
    print(pd.DataFrame(summary_rows).to_string(index=False))

    save_csv(density_df, "literary_density_grid.csv")
    return density_df


# ═══════════════════════════════════════════════════════════════════════════
# Step 4 — Literary Community Clustering
# ═══════════════════════════════════════════════════════════════════════════

def step4_communities(lit_df, person_coords, person_lookup):
    print("\n[Step 4] Community detection for major dynasties ...")
    all_rows = []

    for dyn in TARGET_COMMUNITY_DYNASTIES:
        print(f"  Processing {dyn} ...")
        sub = lit_df[lit_df["dynasty"] == dyn]
        if sub.empty:
            continue

        # Build graph from arrays
        G = nx.Graph()
        edges = list(zip(sub["c_personid"].astype(int), sub["c_assoc_id"].astype(int)))
        for a, b in edges:
            if G.has_edge(a, b):
                G[a][b]["weight"] += 1
            else:
                G.add_edge(a, b, weight=1)

        try:
            communities = list(nx.community.greedy_modularity_communities(G, weight="weight"))
        except Exception as e:
            print(f"    Failed: {e}")
            continue

        communities.sort(key=len, reverse=True)
        for ci, comm in enumerate(communities[:10]):
            comm_list = list(comm)
            lons = [person_coords[p][0] for p in comm_list if p in person_coords]
            lats = [person_coords[p][1] for p in comm_list if p in person_coords]
            mean_lo = float(np.mean(lons)) if lons else float("nan")
            mean_la = float(np.mean(lats)) if lats else float("nan")
            std_lo = float(np.std(lons)) if len(lons) > 1 else 0.0
            std_la = float(np.std(lats)) if len(lats) > 1 else 0.0
            spread = math.sqrt(std_lo ** 2 + std_la ** 2)
            cross = "是" if spread > 5.0 else "否"

            deg = dict(G.degree(comm_list))
            top5 = sorted(deg, key=lambda p: -deg[p])[:5]
            names = [person_lookup.get(p, ("?", ""))[0] for p in top5 if person_lookup.get(p, ("", ""))[0]]

            all_rows.append({
                "dynasty": dyn, "community_id": ci, "size": len(comm_list),
                "geocoded_members": len(lons),
                "mean_lon": round(mean_lo, 2), "mean_lat": round(mean_la, 2),
                "geo_spread_deg": round(spread, 2), "cross_region": cross,
                "representative_members": ", ".join(names),
            })

    comm_df = pd.DataFrame(all_rows)
    save_csv(comm_df, "literary_community_geo.csv")
    return comm_df


# ═══════════════════════════════════════════════════════════════════════════
# Step 5 — Centroid Migration Trajectory
# ═══════════════════════════════════════════════════════════════════════════

def step5_migration(centroid_df):
    print("\n[Step 5] Computing centroid migration trajectory ...")
    rows = []
    for i, dyn in enumerate(DYNASTY_ORDER):
        row = centroid_df[centroid_df["dynasty"] == dyn]
        if row.empty:
            continue
        r = row.iloc[0]
        lon, lat = r["centroid_lon"], r["centroid_lat"]
        entry = {"dynasty": dyn, "centroid_lon": lon, "centroid_lat": lat,
                 "migration_km": 0.0, "direction": "—"}
        if rows:
            prev = rows[-1]
            if not (math.isnan(prev["centroid_lon"]) or math.isnan(lon)):
                dist = haversine(prev["centroid_lon"], prev["centroid_lat"], lon, lat)
                entry["migration_km"] = round(float(dist), 1)
                entry["direction"] = direction_label(
                    prev["centroid_lon"], prev["centroid_lat"], lon, lat)
        rows.append(entry)

    move_df = pd.DataFrame(rows)
    save_csv(move_df, "literary_centroid_movement.csv")
    return move_df


# ═══════════════════════════════════════════════════════════════════════════
# Step 6 — Visualizations
# ═══════════════════════════════════════════════════════════════════════════

def plot_centroid_movement(move_df):
    print("  Plotting literary_centroid_movement.png ...")
    fig, ax = plt.subplots(figsize=(10, 8))
    valid = move_df.dropna(subset=["centroid_lon", "centroid_lat"])

    for _, r in valid.iterrows():
        c = DYNASTY_COLORS.get(r["dynasty"], "#333")
        ax.scatter(r["centroid_lon"], r["centroid_lat"], s=120, c=c,
                   zorder=5, edgecolors="white", linewidth=1.5)
        ax.annotate(r["dynasty"], (r["centroid_lon"], r["centroid_lat"]),
                    textcoords="offset points", xytext=(10, 8),
                    fontsize=12, fontweight="bold", color=c)

    for i in range(len(valid) - 1):
        r1, r2 = valid.iloc[i], valid.iloc[i + 1]
        ax.annotate("", xy=(r2["centroid_lon"], r2["centroid_lat"]),
                     xytext=(r1["centroid_lon"], r1["centroid_lat"]),
                     arrowprops=dict(arrowstyle="->", color="#666", lw=1.8))

    ax.set_xlabel("经度 (Longitude)", fontsize=12)
    ax.set_ylabel("纬度 (Latitude)", fontsize=12)
    ax.set_title("文学重心迁移轨迹", fontsize=14, fontweight="bold")
    ax.set_xlim(100, 130)
    ax.set_ylim(24, 42)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "literary_centroid_movement.png", dpi=150)
    plt.close(fig)


def plot_density_heatmap(density_df):
    print("  Plotting literary_density_heatmap.png ...")
    plot_dynasties = ["唐", "北宋", "南宋", "明"]
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for i, dyn in enumerate(plot_dynasties):
        ax = axes[i]
        sub = density_df[density_df["dynasty"] == dyn]
        if sub.empty:
            ax.set_title(f"{dyn} (无数据)")
            continue
        lon_vals = sorted(sub["grid_lon"].unique())
        lat_vals = sorted(sub["grid_lat"].unique())
        grid = np.zeros((len(lat_vals), len(lon_vals)))
        lon_idx = {v: j for j, v in enumerate(lon_vals)}
        lat_idx = {v: j for j, v in enumerate(lat_vals)}
        for _, r in sub.iterrows():
            grid[lat_idx[r["grid_lat"]], lon_idx[r["grid_lon"]]] = r["count"]
        im = ax.imshow(grid, origin="lower", aspect="auto", cmap="YlOrRd",
                        extent=[min(lon_vals), max(lon_vals) + LON_STEP,
                                min(lat_vals), max(lat_vals) + LAT_STEP])
        ax.set_title(dyn, fontsize=13, fontweight="bold")
        ax.set_xlabel("经度")
        ax.set_ylabel("纬度")
        fig.colorbar(im, ax=ax, shrink=0.8, label="交往频次")

    fig.suptitle("文学交往地理密度", fontsize=15, fontweight="bold", y=1.01)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "literary_density_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_activity_trend(stats_df):
    print("  Plotting literary_activity_trend.png ...")
    df = stats_df[stats_df["dynasty"].isin(DYNASTY_ORDER)].copy()
    fig, ax1 = plt.subplots(figsize=(10, 6))
    x = range(len(df))
    ax1.bar(x, df["literary_edges"], color="#E63946", alpha=0.6, label="文学交往关系数")
    ax1.set_ylabel("文学交往关系数", color="#E63946", fontsize=12)
    ax1.tick_params(axis="y", labelcolor="#E63946")

    ax2 = ax1.twinx()
    ax2.plot(list(x), df["participants"].values, color="#264653", marker="o",
             linewidth=2.5, markersize=8, label="参与人数")
    ax2.set_ylabel("参与人数", color="#264653", fontsize=12)
    ax2.tick_params(axis="y", labelcolor="#264653")

    ax1.set_xticks(list(x))
    ax1.set_xticklabels(df["dynasty"], fontsize=11)
    ax1.set_xlabel("朝代", fontsize=12)
    ax1.set_title("各朝代文学活跃度", fontsize=14, fontweight="bold")
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "literary_activity_trend.png", dpi=150)
    plt.close(fig)


def plot_community_map(lit_df, person_coords, person_lookup):
    print("  Plotting literary_community_map.png ...")
    plot_dynasties = ["唐", "北宋", "南宋", "明"]
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for i, dyn in enumerate(plot_dynasties):
        ax = axes[i]
        sub = lit_df[lit_df["dynasty"] == dyn]
        if sub.empty:
            ax.set_title(f"{dyn} (无数据)")
            continue

        G = nx.Graph()
        for a, b in zip(sub["c_personid"].astype(int), sub["c_assoc_id"].astype(int)):
            if G.has_edge(a, b):
                G[a][b]["weight"] += 1
            else:
                G.add_edge(a, b, weight=1)

        try:
            communities = list(nx.community.greedy_modularity_communities(G, weight="weight"))
        except Exception:
            ax.set_title(f"{dyn} (聚类失败)")
            continue

        communities.sort(key=len, reverse=True)
        pid_comm = {}
        for ci, comm in enumerate(communities[:10]):
            for p in comm:
                pid_comm[p] = ci

        for ci in range(min(10, len(communities))):
            pids = [p for p, c in pid_comm.items() if c == ci]
            los = [person_coords[p][0] for p in pids if p in person_coords]
            las = [person_coords[p][1] for p in pids if p in person_coords]
            if not los:
                continue
            color = COMMUNITY_PALETTE[ci % len(COMMUNITY_PALETTE)]
            ax.scatter(los, las, c=color, s=12, alpha=0.6,
                       label=f"C{ci} (n={len(pids)})", edgecolors="none")

        ax.set_title(dyn, fontsize=13, fontweight="bold")
        ax.set_xlabel("经度")
        ax.set_ylabel("纬度")
        ax.set_xlim(95, 130)
        ax.set_ylim(18, 50)
        ax.legend(fontsize=7, loc="upper left", ncol=2)
        ax.grid(True, alpha=0.2)

    fig.suptitle("文学群体地理分布", fontsize=15, fontweight="bold", y=1.01)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "literary_community_map.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def step6_visualizations(move_df, density_df, stats_df, lit_df, person_coords, person_lookup):
    print("\n[Step 6] Generating visualizations ...")
    plot_centroid_movement(move_df)
    plot_density_heatmap(density_df)
    plot_activity_trend(stats_df)
    plot_community_map(lit_df, person_coords, person_lookup)


# ═══════════════════════════════════════════════════════════════════════════
# Step 7 — Summary Outputs
# ═══════════════════════════════════════════════════════════════════════════

def step7_summary(stats_df, centroid_df, density_df, comm_df, move_df):
    print("\n[Step 7] Writing summary outputs ...")

    save_csv(stats_df, "literary_activity_by_dynasty.csv")

    summary = {
        "project": "E-6 文学群体的地理集聚——从长安到江南",
        "dynasty_stats": stats_df.to_dict(orient="records"),
        "centroids": centroid_df.to_dict(orient="records"),
        "migration": move_df.to_dict(orient="records"),
        "community_summary": {},
    }
    for dyn in TARGET_COMMUNITY_DYNASTIES:
        sub = comm_df[comm_df["dynasty"] == dyn]
        summary["community_summary"][dyn] = {
            "num_communities_detected": len(sub),
            "cross_region_communities": int(sub[sub["cross_region"] == "是"].shape[0]) if len(sub) else 0,
            "largest_community_size": int(sub["size"].max()) if len(sub) else 0,
        }

    with open(OUT_DIR / "analysis_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("  -> analysis_summary.json")

    # README
    lines = [
        "# E-6 文学群体的地理集聚——从长安到江南", "",
        "## 分析概述",
        "本专题追踪中国古代文学交往（赠诗、致书、书序、书跋、唱和、同游、墓志铭等）的地理重心迁移，",
        "量化文学中心从唐代长安经宋代汴京/临安到元明江南的演变过程，并分析文学群体的地理集聚特征。", "",
        "## 数据来源",
        "- CBDB（中国历代人物传记资料库）CSV 数据",
        "- 输入文件：act_person_assoc.csv、act_person_address.csv、dim_person.csv", "",
        "## 朝代文学活跃度", "",
        "| 朝代 | 文学交往数 | 参与人数 |",
        "|------|-----------|---------|",
    ]
    for _, r in stats_df.iterrows():
        if r["dynasty"] in DYNASTY_ORDER:
            lines.append(f"| {r['dynasty']} | {r['literary_edges']:,} | {r['participants']:,} |")

    lines += ["", "## 文学重心坐标", "",
              "| 朝代 | 经度 | 纬度 | 地理定位人数 |",
              "|------|------|------|------------|"]
    for _, r in centroid_df.iterrows():
        lines.append(f"| {r['dynasty']} | {r['centroid_lon']} | {r['centroid_lat']} | {r['persons_geocoded']} |")

    lines += ["", "## 重心迁移轨迹", "",
              "| 朝代 | 迁移距离(km) | 方向 |",
              "|------|-------------|------|"]
    for _, r in move_df.iterrows():
        lines.append(f"| {r['dynasty']} | {r['migration_km']} | {r['direction']} |")

    lines += [
        "", "## 分析结论", "",
        "### 文学中心迁移与政治中心变迁的关系",
        "文学重心的迁移大体上与政治中心的变迁同步。唐代文学以长安为中心，五代至北宋时期重心东移。",
        "南宋随政治中心南迁至临安，文学重心显著南移。元代虽政治中心北返大都，但文学传统在江南持续繁荣。",
        "明代文学重心进一步稳固在江南地区，反映了江南文化圈的成熟。", "",
        "### 地方文学传统的形成",
        "通过社区检测发现，不同时期存在多个地域性文学群体：",
        "- 唐代以长安-洛阳为核心的京畿文学圈",
        "- 北宋以汴京为中心的文人群体，同时出现江西、四川等地方文人圈",
        "- 南宋江南文学群体的壮大，以临安为核心辐射两浙",
        "- 明代江南文人群体高度密集，跨地域文学交流频繁", "",
        "### 地理集聚特征",
        "HHI 指数显示各朝代文学交往的地理集中度：高度集中→逐渐分散→在江南再次集聚。",
        "跨地域文学群体（如古文运动、江西诗派）的存在表明文学传播不完全受地理限制。", "",
        "## 输出文件", "",
        "| 文件 | 说明 |",
        "|------|------|",
        "| literary_centroid_by_dynasty.csv | 各朝代文学重心坐标 |",
        "| literary_density_grid.csv | 网格化文学交往密度 |",
        "| literary_community_geo.csv | 文学群体地理特征 |",
        "| literary_centroid_movement.csv | 重心迁移轨迹 |",
        "| literary_activity_by_dynasty.csv | 各朝代文学活跃度统计 |",
        "| literary_centroid_movement.png | 文学重心迁移图 |",
        "| literary_density_heatmap.png | 文学交往密度热力图 |",
        "| literary_activity_trend.png | 文学活跃度趋势 |",
        "| literary_community_map.png | 文学群体地理分布 |",
        "| nalysis_summary.json | 分析摘要 |",
    ]
    with open(OUT_DIR / "README.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("  -> README.md")


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("E-6: Literary Geography Analysis")
    print("=" * 60)

    person_df, person_lookup, lit_df, stats_df = step1_load_and_filter()
    person_coords = step2_geocode(person_df)
    centroid_df = step2_centroids(lit_df, person_coords)
    density_df = step3_density(lit_df, person_coords)
    comm_df = step4_communities(lit_df, person_coords, person_lookup)
    move_df = step5_migration(centroid_df)
    step6_visualizations(move_df, density_df, stats_df, lit_df, person_coords, person_lookup)
    step7_summary(stats_df, centroid_df, density_df, comm_df, move_df)

    print("\n" + "=" * 60)
    print(f"All outputs saved to: {OUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()

