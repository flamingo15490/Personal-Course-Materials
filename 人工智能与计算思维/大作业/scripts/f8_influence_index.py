# -*- coding: utf-8 -*-
"""F-8: Historical Figure 'Influence Index' — 5-dimension weighted scoring."""
from __future__ import annotations

import json
import textwrap
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / 'output_cbdb_v1'
OUT_DIR = ROOT / '任务f' / '专题8_影响力指数'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Matplotlib Chinese font ──────────────────────────────────────────
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'KaiTi']
plt.rcParams['axes.unicode_minus'] = False

# ── Association category map (reuse from d_social_network.py) ─────────
ASSOC_CATEGORY_MAP = {
    '文學交往': [
        '贈詩、文', '收到Y的贈詩、文', '致書Y', '被致書由Y',
        '答Y書', '收到Y的答書', '為Y所著書作序', '書序由Y所作',
        '為Y所著書作跋', '書序由Y所作', '為Y所著書題辭',
        '為Y作傳', '傳由Y所作', '唱和', '同遊',
    ],
    '墓誌傳記': [
        '為Y作墓誌銘', '墓誌銘由Y所作', '為Y作行狀', '行狀由Y所作',
        '為Y作神道碑', '神道碑由Y所作',
    ],
    '師生': [
        '為Y之學生', '學生為Y', '為Y之門人', '門人為Y',
        '為Y之弟子', '弟子為Y',
    ],
    '友人': ['友', '同年', '同僚', '鄰居'],
}
DESC_TO_CATEGORY: dict[str, str] = {}
for _cat, _descs in ASSOC_CATEGORY_MAP.items():
    for _d in _descs:
        DESC_TO_CATEGORY[_d] = _cat

# Weights
W_A, W_B, W_C, W_D, W_E = 0.30, 0.20, 0.20, 0.15, 0.15

# Textbook list (~50 figures common in Chinese middle/high school textbooks)
TEXTBOOK_NAMES = [
    '孔子', '孟子', '荀子', '老子', '莊子', '孫子', '屈原',
    '秦始皇', '項羽', '劉邦', '張良', '韓信',
    '司馬遷', '諸葛亮', '曹操', '關羽', '劉備', '孫權',
    '王羲之', '陶淵明', '李白', '杜甫', '白居易', '王維',
    '韓愈', '柳宗元', '蘇軾', '歐陽修', '王安石',
    '司馬光', '范仲淹', '辛棄疾', '陸游', '李清照',
    '岳飛', '文天祥', '鄭和', '王陽明', '曹雪芹', '吳承恩',
    '諸葛亮', '陳勝', '吳廣', '蔡倫', '張衡', '畢昇',
    '李時珍', '徐霞客', '林則徐', '康有為', '梁啟超',
    '孫中山', '魯迅',
]
TEXTBOOK_NAMES = list(dict.fromkeys(TEXTBOOK_NAMES))  # deduplicate, preserve order

# ═══════════════════════════════════════════════════════════════════════
# Step 1 — Data Loading
# ═══════════════════════════════════════════════════════════════════════

def load_data():
    """Load all CSVs, build the association graph, return DataFrames + graph."""
    print('[Step 1] Loading data ...')

    person_df = pd.read_csv(
        IN_DIR / 'dim_person.csv',
        usecols=['c_personid', 'c_name_chn', 'dynasty_chn'],
        dtype={'c_personid': int}, encoding='utf-8', on_bad_lines='skip',
    )
    assoc_df = pd.read_csv(
        IN_DIR / 'fact_person_assoc.csv',
        dtype={'c_personid': int, 'c_assoc_id': int},
        encoding='utf-8', on_bad_lines='skip',
    )
    status_df = pd.read_csv(
        IN_DIR / 'fact_person_status.csv',
        dtype={'c_personid': int}, encoding='utf-8', on_bad_lines='skip',
    )
    address_df = pd.read_csv(
        IN_DIR / 'fact_person_address.csv',
        dtype={'c_personid': int}, encoding='utf-8', on_bad_lines='skip',
    )
    kin_df = pd.read_csv(
        IN_DIR / 'fact_person_kin.csv',
        dtype={'c_personid': int, 'c_kin_id': int},
        encoding='utf-8', on_bad_lines='skip',
    )

    # Build association graph (undirected), excluding unknown persons
    print('[Step 1] Building G_assoc ...')
    G = nx.Graph()
    for _, row in assoc_df.iterrows():
        src, tgt = int(row['c_personid']), int(row['c_assoc_id'])
        if src == 0 or tgt == 0:
            continue
        desc = str(row.get('c_assoc_desc_chn', ''))
        if desc in ('未詳', '', 'nan'):
            continue
        G.add_edge(src, tgt)

    # Person name / dynasty lookup
    name_map = {}
    dynasty_map = {}
    for _, row in person_df.iterrows():
        pid = int(row['c_personid'])
        nm = str(row['c_name_chn']) if pd.notna(row['c_name_chn']) else ''
        dy = str(row['dynasty_chn']) if pd.notna(row['dynasty_chn']) else ''
        name_map[pid] = nm
        dynasty_map[pid] = dy

    print(f'  persons: {len(person_df):,}  assoc edges: {len(assoc_df):,}  '
          f'graph nodes: {G.number_of_nodes():,}  edges: {G.number_of_edges():,}')
    return person_df, assoc_df, status_df, address_df, kin_df, G, name_map, dynasty_map


# ═══════════════════════════════════════════════════════════════════════
# Step 2 — Sub-indicator calculations
# ═══════════════════════════════════════════════════════════════════════

def _normalize_nonzero(series: pd.Series) -> pd.Series:
    """Normalize using only non-zero min/max; zero values stay zero."""
    nonzero = series[series > 0]
    if nonzero.empty:
        return series * 0.0
    lo, hi = nonzero.min(), nonzero.max()
    if hi == lo:
        return series.apply(lambda x: 1.0 if x > 0 else 0.0)
    return series.apply(lambda x: (x - lo) / (hi - lo) if x > 0 else 0.0)


def calc_A_pagerank(G: nx.Graph, all_pids: list[int]) -> pd.Series:
    """A: PageRank centrality on the undirected association graph."""
    print('[A] Computing PageRank ...')
    pr = nx.pagerank(G, alpha=0.85)
    s = pd.Series({pid: pr.get(pid, 0.0) for pid in all_pids}, dtype=float)
    return _normalize_nonzero(s)


def calc_B_diversity(assoc_df: pd.DataFrame, all_pids: list[int]) -> pd.Series:
    """B: Relationship diversity = (type_ratio + category_coverage/5) / 2."""
    print('[B] Computing relationship diversity ...')
    # Per-person unique type count and category coverage
    type_counts: dict[int, int] = defaultdict(int)
    cat_sets: dict[int, set[str]] = defaultdict(set)

    for _, row in assoc_df.iterrows():
        pid = int(row['c_personid'])
        desc = str(row.get('c_assoc_desc_chn', ''))
        if desc in ('未詳', '', 'nan'):
            continue
        type_counts[pid] += 1
        cat = DESC_TO_CATEGORY.get(desc, '其他')
        cat_sets[pid].add(cat)

    max_types = max(type_counts.values()) if type_counts else 1

    vals = {}
    for pid in all_pids:
        if pid in type_counts:
            type_ratio = type_counts[pid] / max_types
            cat_ratio = len(cat_sets[pid]) / 5.0
            vals[pid] = (type_ratio + cat_ratio) / 2.0
        else:
            vals[pid] = 0.0
    return pd.Series(vals, dtype=float)


def calc_C_spatial(address_df: pd.DataFrame, all_pids: list[int]) -> pd.Series:
    """C: Spatial breadth = unique_addresses × lat_span × lon_span (degrees²)."""
    print('[C] Computing spatial breadth ...')
    # Build per-person coordinate sets
    pid_coords: dict[int, list[tuple[float, float]]] = defaultdict(list)
    pid_unique_addrs: dict[int, set] = defaultdict(set)

    for _, row in address_df.iterrows():
        pid = int(row['c_personid'])
        addr_id = row.get('c_addr_id')
        lon = row.get('x_coord')
        lat = row.get('y_coord')
        if pd.notna(lon) and pd.notna(lat):
            try:
                lon_f, lat_f = float(lon), float(lat)
                if lon_f != 0 and lat_f != 0:
                    pid_coords[pid].append((lat_f, lon_f))
            except (ValueError, TypeError):
                pass
        if pd.notna(addr_id) and addr_id != 0:
            pid_unique_addrs[pid].add(addr_id)

    vals = {}
    for pid in all_pids:
        coords = pid_coords.get(pid, [])
        n_addrs = len(pid_unique_addrs.get(pid, set()))
        if len(coords) >= 2:
            lats = [c[0] for c in coords]
            lons = [c[1] for c in coords]
            lat_span = max(lats) - min(lats)
            lon_span = max(lons) - min(lons)
            vals[pid] = n_addrs * lat_span * lon_span
        elif n_addrs > 0:
            vals[pid] = float(n_addrs)
        else:
            vals[pid] = 0.0

    s = pd.Series(vals, dtype=float)
    return _normalize_nonzero(s)


def calc_D_identity(status_df: pd.DataFrame, all_pids: list[int]) -> pd.Series:
    """D: Identity multiplicity = unique status label count."""
    print('[D] Computing identity multiplicity ...')
    pid_statuses: dict[int, set] = defaultdict(set)
    for _, row in status_df.iterrows():
        pid = int(row['c_personid'])
        code = str(row.get('c_status_desc_chn', ''))
        if code and code not in ('nan', '', '未詳'):
            pid_statuses[pid].add(code)

    vals = {pid: float(len(pid_statuses.get(pid, set()))) for pid in all_pids}
    s = pd.Series(vals, dtype=float)
    return _normalize_nonzero(s)


def calc_E_citations(assoc_df: pd.DataFrame, kin_df: pd.DataFrame,
                     all_pids: list[int]) -> pd.Series:
    """E: Citation frequency from assoc + kin source records."""
    print('[E] Computing citation frequency ...')
    citations: dict[int, int] = Counter()

    for _, row in assoc_df.iterrows():
        pid = int(row['c_personid'])
        src = row.get('c_source')
        if pd.notna(src) and str(src) not in ('0', '', 'nan'):
            citations[pid] += 1
        # Also count as cited if appearing as target
        aid = int(row['c_assoc_id'])
        if aid != 0:
            citations[aid] += 1

    for _, row in kin_df.iterrows():
        pid = int(row['c_personid'])
        src = row.get('c_source')
        if pd.notna(src) and str(src) not in ('0', '', 'nan'):
            citations[pid] += 1
        kid = int(row['c_kin_id']) if pd.notna(row.get('c_kin_id')) else 0
        if kid != 0:
            citations[kid] += 1

    vals = {pid: float(citations.get(pid, 0)) for pid in all_pids}
    s = pd.Series(vals, dtype=float)
    return _normalize_nonzero(s)


# ═══════════════════════════════════════════════════════════════════════
# Step 3 — Composite index & output
# ═══════════════════════════════════════════════════════════════════════

def build_composite(person_df: pd.DataFrame, A: pd.Series, B: pd.Series,
                    C: pd.Series, D: pd.Series, E: pd.Series,
                    name_map: dict, dynasty_map: dict):
    """Calculate weighted influence index, output CSVs."""
    print('[Step 3] Building composite index ...')
    all_pids = person_df['c_personid'].astype(int).tolist()

    influence = (W_A * A + W_B * B + W_C * C + W_D * D + W_E * E).round(4)

    result = pd.DataFrame({
        'c_personid': all_pids,
        'name': [name_map.get(p, '') for p in all_pids],
        'dynasty': [dynasty_map.get(p, '') for p in all_pids],
        'A_pagerank': A.round(4).values,
        'B_diversity': B.round(4).values,
        'C_spatial': C.round(4).values,
        'D_identity': D.round(4).values,
        'E_citations': E.round(4).values,
        'influence': influence.values,
    })

    # Sort by influence descending
    result = result.sort_values('influence', ascending=False).reset_index(drop=True)
    result['rank'] = range(1, len(result) + 1)

    # Top 200
    top200 = result.head(200).copy()
    top200.to_csv(OUT_DIR / 'influence_top200.csv', index=False, encoding='utf-8-sig')
    print(f'  Top 200 saved. Top 5: {top200["name"].head(5).tolist()}')

    # All with at least one non-zero sub-indicator
    mask = (result['A_pagerank'] > 0) | (result['B_diversity'] > 0) | \
           (result['C_spatial'] > 0) | (result['D_identity'] > 0) | \
           (result['E_citations'] > 0)
    all_nonzero = result[mask].copy()
    all_nonzero.to_csv(OUT_DIR / 'influence_all.csv', index=False, encoding='utf-8-sig')
    print(f'  influence_all.csv: {len(all_nonzero):,} persons')

    return result, top200, all_nonzero


# ═══════════════════════════════════════════════════════════════════════
# Step 4 — Dynasty distribution analysis
# ═══════════════════════════════════════════════════════════════════════

def dynasty_analysis(result: pd.DataFrame, top200: pd.DataFrame):
    """Compare dynasty representation in Top 200 vs total population."""
    print('[Step 4] Dynasty distribution analysis ...')

    # Total population by dynasty (exclude empty)
    all_dy = result[result['dynasty'] != '']['dynasty']
    total_counts = all_dy.value_counts()
    total_pct = total_counts / total_counts.sum()

    # Top 200 by dynasty
    top_dy = top200[top200['dynasty'] != '']['dynasty']
    top_counts = top_dy.value_counts()
    top_pct = top_counts / top_counts.sum()

    # Merge
    dyn_df = pd.DataFrame({
        'dynasty': top_pct.index,
        'top200_count': [top_counts.get(d, 0) for d in top_pct.index],
        'top200_pct': top_pct.values.round(4),
        'total_pct': [total_pct.get(d, 0) for d in top_pct.index],
    })
    dyn_df['total_pct'] = dyn_df['total_pct'].round(4)
    dyn_df['over_representation'] = (dyn_df['top200_pct'] - dyn_df['total_pct']).round(4)
    dyn_df = dyn_df.sort_values('top200_count', ascending=False).reset_index(drop=True)

    dyn_df.to_csv(OUT_DIR / 'influence_by_dynasty.csv', index=False, encoding='utf-8-sig')
    print(f'  Dynasty analysis saved. Top dynasty: {dyn_df.iloc[0]["dynasty"]}')
    return dyn_df, total_pct, top_pct


# ═══════════════════════════════════════════════════════════════════════
# Step 5 — Textbook vs CBDB comparison
# ═══════════════════════════════════════════════════════════════════════

def textbook_comparison(result: pd.DataFrame, name_map: dict):
    """Compare textbook figures with CBDB influence ranking."""
    print('[Step 5] Textbook vs CBDB comparison ...')

    # Build name -> personid lookup (handle duplicates: keep first / highest influence)
    name_to_pids: dict[str, list[int]] = defaultdict(list)
    for pid, nm in name_map.items():
        if nm:
            name_to_pids[nm].append(pid)

    rows = []
    for tname in TEXTBOOK_NAMES:
        pids = name_to_pids.get(tname, [])
        if not pids:
            rows.append({
                'name': tname, 'cbdb_rank': None, 'cbdb_influence': None,
                'in_textbook_top50': True, 'status': '不在 CBDB 中',
            })
            continue
        # Pick the one with highest influence
        sub = result[result['c_personid'].isin(pids)].sort_values('influence', ascending=False)
        best = sub.iloc[0]
        rows.append({
            'name': tname,
            'cbdb_rank': int(best['rank']),
            'cbdb_influence': round(float(best['influence']), 4),
            'in_textbook_top50': True,
            'status': 'found',
        })

    tb_df = pd.DataFrame(rows)
    tb_df.to_csv(OUT_DIR / 'textbook_vs_cbdb.csv', index=False, encoding='utf-8-sig')

    # Identify "underestimated" (high CBDB rank, not in textbook top) and "overestimated"
    found = tb_df[tb_df['status'] == 'found'].copy()
    found = found.sort_values('cbdb_rank')
    print(f'  Textbook match: {len(found)}/{len(TEXTBOOK_NAMES)} found in CBDB')
    if len(found) > 0:
        top5 = found.head(5)[['name', 'cbdb_rank']].values.tolist()
        print(f'  Highest-ranked textbook figures: {top5}')

    return tb_df


# ═══════════════════════════════════════════════════════════════════════
# Step 6 — Visualizations
# ═══════════════════════════════════════════════════════════════════════

def viz_top50_bar(top200: pd.DataFrame):
    """Stacked horizontal bar chart of Top 50 influence by sub-indicator."""
    print('[Viz 1] Top 50 bar chart ...')
    df = top200.head(50).copy()
    df = df.sort_values('influence', ascending=True)  # bottom-up on chart

    labels = [f"{row['name']} ({row['dynasty']})" for _, row in df.iterrows()]
    y = np.arange(len(labels))

    colors = ['#4C78A8', '#F58518', '#E45756', '#72B7B2', '#54A24B']
    dims = ['A_pagerank', 'B_diversity', 'C_spatial', 'D_identity', 'E_citations']
    dim_labels = ['社交中心性', '关系多样性', '空间广度', '身份多重性', '文献记载量']
    weights = [W_A, W_B, W_C, W_D, W_E]

    fig, ax = plt.subplots(figsize=(14, 12))
    left = np.zeros(len(df))
    for dim, color, label, w in zip(dims, colors, dim_labels, weights):
        vals = (df[dim] * w).values
        ax.barh(y, vals, left=left, height=0.7, color=color, label=f'{label} (×{w})')
        left += vals

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel('影响力指数贡献')
    ax.set_title('Top 50 历史人物影响力指数（分段着色）', fontsize=14, fontweight='bold')
    ax.legend(loc='lower right', fontsize=9)
    ax.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_DIR / 'influence_top50_bar.png', dpi=150)
    plt.close()


def viz_sub_index_correlation(all_nonzero: pd.DataFrame):
    """5×5 scatter matrix with regression lines and correlation coefficients."""
    print('[Viz 2] Sub-index correlation matrix ...')
    dims = ['A_pagerank', 'B_diversity', 'C_spatial', 'D_identity', 'E_citations']
    dim_labels = ['社交中心性', '关系多样性', '空间广度', '身份多重性', '文献记载量']
    n = len(dims)

    # Sample if too large
    plot_df = all_nonzero[dims].copy()
    if len(plot_df) > 5000:
        plot_df = plot_df.sample(5000, random_state=42)

    fig, axes = plt.subplots(n, n, figsize=(14, 14))
    for i in range(n):
        for j in range(n):
            ax = axes[i][j]
            x = plot_df[dims[j]].values
            y = plot_df[dims[i]].values
            if i == j:
                ax.hist(x, bins=30, color='#4C78A8', alpha=0.7)
            else:
                ax.scatter(x, y, s=3, alpha=0.3, color='#4C78A8')
                # Regression line
                mask = (x > 0) | (y > 0)
                if mask.sum() > 2:
                    m, b = np.polyfit(x[mask], y[mask], 1)
                    xs = np.linspace(x.min(), x.max(), 100)
                    ax.plot(xs, m * xs + b, color='red', linewidth=1)
                # Correlation
                corr = np.corrcoef(x, y)[0, 1]
                ax.text(0.05, 0.92, f'r={corr:.2f}', transform=ax.transAxes,
                        fontsize=8, color='red', fontweight='bold')
            if i == n - 1:
                ax.set_xlabel(dim_labels[j], fontsize=8)
            if j == 0:
                ax.set_ylabel(dim_labels[i], fontsize=8)
            ax.tick_params(labelsize=6)

    fig.suptitle('子指标相关性矩阵', fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(OUT_DIR / 'sub_index_correlation.png', dpi=150)
    plt.close()


def viz_dynasty_distribution(dyn_df: pd.DataFrame):
    """Grouped bar chart: Top 200 share vs total population share by dynasty."""
    print('[Viz 3] Dynasty distribution chart ...')
    df = dyn_df.head(12).copy()  # Top 12 dynasties
    x = np.arange(len(df))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 6))
    bars1 = ax.bar(x - width / 2, df['top200_pct'], width, label='Top 200 占比',
                   color='#4C78A8')
    bars2 = ax.bar(x + width / 2, df['total_pct'], width, label='总人数占比',
                   color='#F58518')

    ax.set_xticks(x)
    ax.set_xticklabels(df['dynasty'], rotation=45, ha='right', fontsize=10)
    ax.set_ylabel('占比')
    ax.set_title('各朝代在 Top 200 中的占比 vs 总人数占比', fontsize=13, fontweight='bold')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # Annotate over/under-represented
    for _, row in df.iterrows():
        idx = row.name
        diff = row['over_representation']
        if diff > 0.05:
            ax.annotate('超产', xy=(x[idx] - width / 2, row['top200_pct']),
                        fontsize=8, color='green', fontweight='bold',
                        xytext=(0, 5), textcoords='offset points', ha='center')
        elif diff < -0.05:
            ax.annotate('欠产', xy=(x[idx] - width / 2, row['top200_pct']),
                        fontsize=8, color='red', fontweight='bold',
                        xytext=(0, 5), textcoords='offset points', ha='center')

    plt.tight_layout()
    plt.savefig(OUT_DIR / 'influence_by_dynasty.png', dpi=150)
    plt.close()


def viz_textbook_comparison(result: pd.DataFrame, tb_df: pd.DataFrame, name_map: dict):
    """Scatter plot: CBDB rank vs textbook membership."""
    print('[Viz 4] Textbook vs CBDB scatter ...')
    fig, ax = plt.subplots(figsize=(12, 7))

    # Background: all persons (sample for performance)
    bg = result[result['influence'] > 0].sample(min(10000, len(result[result['influence'] > 0])),
                                                 random_state=42)
    ax.scatter(bg['rank'], bg['influence'], s=5, alpha=0.15, color='gray', label='其他人物')

    # Textbook figures
    found = tb_df[tb_df['status'] == 'found'].copy()
    if len(found) > 0:
        ax.scatter(found['cbdb_rank'], found['cbdb_influence'], s=60, color='#E45756',
                   edgecolors='black', linewidths=0.5, zorder=5, label='课本常见人物')
        # Label extremes
        for _, row in found.iterrows():
            rank = row['cbdb_rank']
            if rank <= 50 or rank > len(result) - 100:
                ax.annotate(row['name'], (rank, row['cbdb_influence']),
                            fontsize=7, ha='left', va='bottom',
                            xytext=(5, 3), textcoords='offset points')

    # Not found in CBDB
    missing = tb_df[tb_df['status'] == '不在 CBDB 中']
    if len(missing) > 0:
        print(f'  {len(missing)} textbook figures not found in CBDB: '
              f'{missing["name"].tolist()}')

    ax.set_xlabel('CBDB 影响力排名（越小越靠前）')
    ax.set_ylabel('影响力指数')
    ax.set_title('课本常见人物 vs CBDB 影响力排名', fontsize=13, fontweight='bold')
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_DIR / 'textbook_vs_cbdb.png', dpi=150)
    plt.close()


# ═══════════════════════════════════════════════════════════════════════
# Step 7 — Summary outputs
# ═══════════════════════════════════════════════════════════════════════

def write_summary(result: pd.DataFrame, top200: pd.DataFrame,
                  tb_df: pd.DataFrame, dyn_df: pd.DataFrame,
                  all_nonzero: pd.DataFrame):
    """Write analysis_summary.json and README.md."""
    print('[Step 7] Writing summary ...')

    # Top 10
    top10 = top200.head(10)[['rank', 'name', 'dynasty', 'influence',
                              'A_pagerank', 'B_diversity', 'C_spatial',
                              'D_identity', 'E_citations']].to_dict(orient='records')

    # Key findings
    textbook_found = tb_df[tb_df['status'] == 'found']
    textbook_missing = tb_df[tb_df['status'] == '不在 CBDB 中']
    top_dyn = dyn_df.iloc[0] if len(dyn_df) > 0 else None

    findings = {
        'total_persons': len(result),
        'persons_with_nonzero_index': len(all_nonzero),
        'top10': top10,
        'weights': {'A_pagerank': W_A, 'B_diversity': W_B,
                     'C_spatial': W_C, 'D_identity': W_D, 'E_citations': W_E},
        'textbook_match_rate': f'{len(textbook_found)}/{len(TEXTBOOK_NAMES)}',
        'textbook_missing': textbook_missing['name'].tolist() if len(textbook_missing) > 0 else [],
        'top_dynasty_in_top200': str(top_dyn['dynasty']) if top_dyn is not None else '',
        'over_represented_dynasties': dyn_df[dyn_df['over_representation'] > 0.05]['dynasty'].tolist(),
        'under_represented_dynasties': dyn_df[dyn_df['over_representation'] < -0.05]['dynasty'].tolist(),
    }

    with open(OUT_DIR / 'analysis_summary.json', 'w', encoding='utf-8') as f:
        json.dump(findings, f, ensure_ascii=False, indent=2)

    # README
    readme = textwrap.dedent(f"""\
    # 任务 F-8：历史人物"影响力指数"

    ## 方法论

    ### 数据来源
    - CBDB（中国历代人物传记资料库）已数据化 CSV，共 {len(result):,} 位人物。

    ### 子指标与权重

    | 维度 | 子指标 | 权重 | 说明 |
    |------|--------|------|------|
    | A | 社交网络中心性 (PageRank) | {W_A:.0%} | 在无向社会关系网络上计算 |
    | B | 关系多样性 | {W_B:.0%} | Shannon 多样性（关系类型数）+ 5 类大类覆盖率 |
    | C | 空间活动广度 | {W_C:.0%} | 活动地数 × 经纬度跨度（度²） |
    | D | 身份多重性 | {W_D:.0%} | 身份标签种类数 |
    | E | 文献记载量 | {W_E:.0%} | 社会关系 + 亲属关系中被引用记录数 |

    综合指数：`Influence = 0.30×A + 0.20×B + 0.20×C + 0.15×D + 0.15×E`，取值 [0, 1]。

    ### 归一化策略
    - 仅对非零值计算 min/max 归一化，避免大量孤立人物拉低分布。
    - 空值统一为 0。

    ## 权重选择理由
    - 权重基于专家判断，反映"社交影响力"与"空间影响力"并重的思路。
    - 社交中心性（30%）权重最高，因为社会关系网络是影响力的核心载体。
    - 文献记载量和身份多重性权重较低，避免数据偏差（CBDB 偏文人/官员）过度放大。

    ## 局限性
    1. **数据偏差**：CBDB 系统性偏重文人和官员，武将、商人、工匠等群体代表性不足。
    2. **课本人物匹配**：使用精确姓名匹配，未处理同名问题（如"王維"可能对应多个 CBDB 人物）。
    3. **权重主观性**：权重的选择是主观的，可根据研究需要调整。
    4. **文献记载代理变量**：source/pages 字段作为"被引用量"的代理变量，可能不完全等价。
    5. **空间广度偏倚**：任官驻地多的朝代（如宋代）人物天然占优。

    ## 输出文件

    | 文件 | 内容 |
    |------|------|
    | `influence_top200.csv` | Top 200 影响力人物 |
    | `influence_all.csv` | 全量影响力指数（{len(all_nonzero):,} 人） |
    | `influence_by_dynasty.csv` | 朝代影响力分布 |
    | `textbook_vs_cbdb.csv` | 课本人物 CBDB 排名对比 |
    | `influence_top50_bar.png` | Top 50 影响力柱状图 |
    | `sub_index_correlation.png` | 子指标相关性矩阵 |
    | `influence_by_dynasty.png` | 朝代影响力分布图 |
    | `textbook_vs_cbdb.png` | 课本 vs CBDB 散点图 |
    | `analysis_summary.json` | 分析摘要 |
    | `README.md` | 本说明文档 |
    """)

    with open(OUT_DIR / 'README.md', 'w', encoding='utf-8') as f:
        f.write(readme)


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

def main():
    print('=' * 60)
    print('F-8: 历史人物影响力指数')
    print('=' * 60)

    # Step 1: Load data
    person_df, assoc_df, status_df, address_df, kin_df, G, name_map, dynasty_map = load_data()
    all_pids = person_df['c_personid'].astype(int).tolist()

    # Step 2: Sub-indicators
    A = calc_A_pagerank(G, all_pids)
    B = calc_B_diversity(assoc_df, all_pids)
    C = calc_C_spatial(address_df, all_pids)
    D = calc_D_identity(status_df, all_pids)
    E = calc_E_citations(assoc_df, kin_df, all_pids)

    # Step 3: Composite index
    result, top200, all_nonzero = build_composite(person_df, A, B, C, D, E,
                                                   name_map, dynasty_map)

    # Step 4: Dynasty analysis
    dyn_df, total_pct, top_pct = dynasty_analysis(result, top200)

    # Step 5: Textbook comparison
    tb_df = textbook_comparison(result, name_map)

    # Step 6: Visualizations
    viz_top50_bar(top200)
    viz_sub_index_correlation(all_nonzero)
    viz_dynasty_distribution(dyn_df)
    viz_textbook_comparison(result, tb_df, name_map)

    # Step 7: Summary
    write_summary(result, top200, tb_df, dyn_df, all_nonzero)

    print('=' * 60)
    print('Done! All outputs in:', OUT_DIR)
    print('=' * 60)


if __name__ == '__main__':
    main()
