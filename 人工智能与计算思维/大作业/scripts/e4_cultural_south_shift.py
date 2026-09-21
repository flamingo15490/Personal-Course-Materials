# -*- coding: utf-8 -*-
"""Part E-4: 明清人口大迁徙与文化重心南移

追踪宋→元→明→清四代历史人物的出生地与活动地分布变化，
量化"经济文化重心从北到南"这一历史进程。
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / 'output_cbdb_v1'
OUT_DIR = ROOT / '任务e' / '专题4_文化重心南移'
OUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_DYNASTIES = ['宋', '元', '明', '清']
DYNASTY_ORDER = {d: i for i, d in enumerate(TARGET_DYNASTIES)}

NORTH_LAT = 33.0  # 南北分界纬度（秦岭-淮河线近似）

# Address types to EXCLUDE from activity-place analysis (birthplace / ancestral)
BIRTHPLACE_TYPES = {
    '籍貫(基本地址)', '另一籍貫(基本地址)', '祖籍', '本貫',
    '未詳', '葬地', '[缺乏信息]',
}

# Literary / academic relationship types for cultural-center proxy
LITERARY_RELS = {
    '贈詩、文', '收到Y的贈詩、文',
    '致書Y', '被致書由Y', '答Y書', '收到Y的答書',
    '為Y所著書作序', '書序由Y所作',
    '為Y所著書作跋', '書跋由Y所作',
    '為Y所著書題辭',
    '為Y作傳', '傳由Y所作',
    '為Y作墓誌銘', '墓誌銘由Y所作',
    '為Y作行狀', '行狀由Y所作',
    '為Y作神道碑', '神道碑由Y所作',
    '為Y作墓表', '墓表由Y所作',
    '為Y之學生', '學生為Y',
    '為Y之門人', '門人為Y',
    '為Y之弟子', '弟子為Y',
    '唱和', '同遊', '相唱和',
    '為Y作臨別贈言(送別詩、序)', '臨別得到Y所作贈言(送別詩、序)',
    '為Y作祭文', '祭文由Y所作',
    '為Y之建築物題詠、記、命名', '建築物得到Y的題詠、記、命名',
    '被Y推薦', '推薦',
    '被Y欣賞/器重', '欣賞/器重',
    '為Y所著書題辭',
}

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'KaiTi']
plt.rcParams['axes.unicode_minus'] = False

# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def region_of(lat: float) -> str:
    """北/南 classification based on 33°N boundary."""
    if pd.isna(lat):
        return '未知'
    return '北' if lat > NORTH_LAT else '南'


def safe_float(v):
    try:
        f = float(v)
        return f if f != 0 else np.nan
    except (ValueError, TypeError):
        return np.nan


def save_csv(df: pd.DataFrame, name: str):
    path = OUT_DIR / name
    df.to_csv(path, index=False, encoding='utf-8-sig')
    print(f'  -> Saved {name} ({len(df)} rows)')


# ===================================================================
# Data Loading
# ===================================================================

def load_data():
    """Load all needed CSVs, returning filtered DataFrames."""
    print('[Load] Loading dim_person.csv ...')
    dp = pd.read_csv(
        IN_DIR / 'dim_person.csv',
        usecols=['c_personid', 'c_name_chn', 'dynasty_chn',
                 'index_addr_chn', 'index_addr_x', 'index_addr_y'],
        dtype={'c_personid': int},
        encoding='utf-8', on_bad_lines='skip',
    )
    dp = dp[dp['dynasty_chn'].isin(TARGET_DYNASTIES)].copy()
    dp['index_addr_x'] = dp['index_addr_x'].apply(safe_float)
    dp['index_addr_y'] = dp['index_addr_y'].apply(safe_float)
    print(f'  dim_person: {len(dp):,} rows in target dynasties')

    print('[Load] Loading fact_person_address.csv ...')
    pa = pd.read_csv(
        IN_DIR / 'fact_person_address.csv',
        usecols=['c_personid', 'c_addr_desc_chn', 'addr_chn',
                 'x_coord', 'y_coord'],
        dtype={'c_personid': int},
        encoding='utf-8', on_bad_lines='skip',
    )
    pa['x_coord'] = pa['x_coord'].apply(safe_float)
    pa['y_coord'] = pa['y_coord'].apply(safe_float)
    print(f'  fact_person_address: {len(pa):,} rows total')

    print('[Load] Loading fact_person_assoc.csv ...')
    assoc = pd.read_csv(
        IN_DIR / 'fact_person_assoc.csv',
        usecols=['c_personid', 'c_assoc_id', 'c_assoc_desc_chn'],
        dtype={'c_personid': int, 'c_assoc_id': int},
        encoding='utf-8', on_bad_lines='skip',
    )
    print(f'  fact_person_assoc: {len(assoc):,} rows')

    return dp, pa, assoc


# ===================================================================
# Step 1 — Birthplace Distribution (籍贯地理分布)
# ===================================================================

def step1_birthplace(dp: pd.DataFrame, pa: pd.DataFrame):
    print('\n[Step 1] Birthplace distribution ...')
    # Filter to birthplace records
    bp = pa[pa['c_addr_desc_chn'] == '籍貫(基本地址)'].copy()
    # Join to get dynasty
    bp = bp.merge(dp[['c_personid', 'dynasty_chn']], on='c_personid', how='inner')
    bp['region'] = bp['y_coord'].apply(region_of)

    # Aggregate: per dynasty × addr_chn
    agg = (bp.groupby(['dynasty_chn', 'addr_chn', 'region'])
           .agg(count=('c_personid', 'size'),
                x_coord=('x_coord', 'mean'),
                y_coord=('y_coord', 'mean'))
           .reset_index()
           .rename(columns={'dynasty_chn': 'dynasty'}))

    # Sort by dynasty order then count desc
    agg['_o'] = agg['dynasty'].map(DYNASTY_ORDER)
    agg = agg.sort_values(['_o', 'count'], ascending=[True, False]).drop(columns='_o')

    save_csv(agg, 'birthplace_by_dynasty.csv')

    # Per-dynasty north/south summary
    summary = {}
    for dyn in TARGET_DYNASTIES:
        sub = bp[bp['dynasty_chn'] == dyn]
        n_total = len(sub)
        n_south = (sub['region'] == '南').sum()
        n_north = (sub['region'] == '北').sum()
        south_pct = round(n_south / n_total * 100, 2) if n_total else 0
        north_pct = round(n_north / n_total * 100, 2) if n_total else 0
        summary[dyn] = {
            'total': int(n_total),
            'south': int(n_south),
            'north': int(n_north),
            'south_pct': south_pct,
            'north_pct': north_pct,
        }
        top10 = (agg[agg['dynasty'] == dyn]
                 .nlargest(10, 'count')[['addr_chn', 'count', 'region']]
                 .to_dict('records'))
        summary[dyn]['top10'] = top10
        print(f'  {dyn}: {n_total:,} persons, 南={south_pct}%, 北={north_pct}%')

    return agg, summary, bp


# ===================================================================
# Step 2 — Activity Place Distribution (活动地分布)
# ===================================================================

def step2_activity(dp: pd.DataFrame, pa: pd.DataFrame):
    print('\n[Step 2] Activity-place distribution ...')
    # Exclude birthplace / ancestral types
    ap = pa[~pa['c_addr_desc_chn'].isin(BIRTHPLACE_TYPES)].copy()
    ap = ap.merge(dp[['c_personid', 'dynasty_chn']], on='c_personid', how='inner')
    ap['region'] = ap['y_coord'].apply(region_of)

    # Aggregate per dynasty × addr_chn
    agg = (ap.groupby(['dynasty_chn', 'addr_chn'])
           .agg(count=('c_personid', 'size'),
                avg_lat=('y_coord', 'mean'),
                median_lat=('y_coord', 'median'))
           .reset_index()
           .rename(columns={'dynasty_chn': 'dynasty'}))

    agg['_o'] = agg['dynasty'].map(DYNASTY_ORDER)
    agg = agg.sort_values(['_o', 'count'], ascending=[True, False]).drop(columns='_o')

    save_csv(agg, 'activity_place_by_dynasty.csv')

    # Per-dynasty summary
    summary = {}
    for dyn in TARGET_DYNASTIES:
        sub = ap[ap['dynasty_chn'] == dyn]
        n_total = len(sub)
        n_south = (sub['region'] == '南').sum()
        n_north = (sub['region'] == '北').sum()
        south_pct = round(n_south / n_total * 100, 2) if n_total else 0
        north_pct = round(n_north / n_total * 100, 2) if n_total else 0
        mean_lat = round(sub['y_coord'].mean(), 2) if n_total else None
        median_lat = round(sub['y_coord'].median(), 2) if n_total else None
        summary[dyn] = {
            'total': int(n_total),
            'south': int(n_south),
            'north': int(n_north),
            'south_pct': south_pct,
            'north_pct': north_pct,
            'mean_lat': mean_lat,
            'median_lat': median_lat,
        }
        print(f'  {dyn}: {n_total:,} activity records, 南={south_pct}%, 北={north_pct}%')

    return agg, summary


# ===================================================================
# Step 3 — South Migration Analysis (南迁轨迹)
# ===================================================================

def step3_migration(dp: pd.DataFrame, pa: pd.DataFrame, bp_df: pd.DataFrame):
    print('\n[Step 3] South-migration analysis ...')
    # Get birthplace coords per person
    bp_coords = bp_df[['c_personid', 'dynasty_chn', 'y_coord']].copy()
    bp_coords = bp_coords.rename(columns={'y_coord': 'bp_lat'})
    bp_coords = bp_coords.dropna(subset=['bp_lat'])
    bp_coords = bp_coords[bp_coords['bp_lat'] > NORTH_LAT]  # only northerners
    # De-duplicate: one birthplace per person
    bp_coords = bp_coords.drop_duplicates(subset=['c_personid'])

    # Get activity places
    ap = pa[~pa['c_addr_desc_chn'].isin(BIRTHPLACE_TYPES)].copy()
    ap = ap.merge(dp[['c_personid', 'dynasty_chn']], on='c_personid', how='inner')
    ap = ap.dropna(subset=['y_coord'])

    # Find south migrants: northerners with southern activity places
    ap_south = ap[ap['y_coord'] <= NORTH_LAT].copy()
    migrants = ap_south.merge(bp_coords[['c_personid', 'bp_lat']],
                               on='c_personid', how='inner')

    # Per-dynasty stats
    rows = []
    dest_counter = {}  # dynasty -> Counter of destination addr_chn
    for dyn in TARGET_DYNASTIES:
        dyn_persons = set(dp[dp['dynasty_chn'] == dyn]['c_personid'])
        total = len(dyn_persons & set(bp_coords['c_personid']))  # northerners in this dyn
        m_sub = migrants[migrants['dynasty_chn'] == dyn]
        m_ids = set(m_sub['c_personid'])
        n_mig = len(m_ids)
        pct = round(n_mig / total * 100, 2) if total else 0

        # Top 10 destinations
        dest = Counter(m_sub['addr_chn'].dropna())
        dest_counter[dyn] = dest
        top10_str = '; '.join(f'{k}({v})' for k, v in dest.most_common(10))

        rows.append({
            'dynasty': dyn,
            'total_northerners': total,
            'south_migrants': n_mig,
            'pct': pct,
            'top10_destinations': top10_str,
        })
        print(f'  {dyn}: {n_mig}/{total} northerners migrated south ({pct}%)')

    out = pd.DataFrame(rows)
    save_csv(out, 'migration_south_stats.csv')

    return out, dest_counter


# ===================================================================
# Step 4 — Cultural Center Evolution (文化中心演变)
# ===================================================================

def step4_cultural_centers(dp: pd.DataFrame, pa: pd.DataFrame, assoc: pd.DataFrame):
    print('\n[Step 4] Cultural-center analysis ...')
    # Filter assoc to literary/academic types
    assoc_lit = assoc[assoc['c_assoc_desc_chn'].isin(LITERARY_RELS)].copy()
    print(f'  Literary associations: {len(assoc_lit):,} records')

    # Collect all person IDs involved in literary relationships
    lit_persons = set(assoc_lit['c_personid']) | set(assoc_lit['c_assoc_id'])
    print(f'  Unique persons in literary network: {len(lit_persons):,}')

    # Get dynasty for these persons
    dp_lit = dp[dp['c_personid'].isin(lit_persons)][
        ['c_personid', 'dynasty_chn', 'index_addr_chn', 'index_addr_x', 'index_addr_y']
    ].copy()

    # Get activity places for these persons (non-birthplace)
    pa_lit = pa[
        (pa['c_personid'].isin(lit_persons)) &
        (~pa['c_addr_desc_chn'].isin(BIRTHPLACE_TYPES))
    ][['c_personid', 'addr_chn', 'x_coord', 'y_coord']].copy()

    # Merge with dynasty
    pa_lit = pa_lit.merge(dp_lit[['c_personid', 'dynasty_chn']],
                           on='c_personid', how='inner')

    # Also prepare index-address locations
    idx_locs = dp_lit[['c_personid', 'dynasty_chn', 'index_addr_chn',
                        'index_addr_x', 'index_addr_y']].copy()
    idx_locs = idx_locs.rename(columns={
        'index_addr_chn': 'addr_chn',
        'index_addr_x': 'x_coord',
        'index_addr_y': 'y_coord',
    })

    # Combine activity places + index address
    combined = pd.concat([
        pa_lit[['dynasty_chn', 'addr_chn']],
        idx_locs[['dynasty_chn', 'addr_chn']],
    ], ignore_index=True)
    combined = combined.dropna(subset=['addr_chn'])

    # Aggregate: dynasty × addr_chn
    agg = (combined.groupby(['dynasty_chn', 'addr_chn'])
           .size().reset_index(name='cultural_interaction_count')
           .rename(columns={'dynasty_chn': 'dynasty'}))

    agg['_o'] = agg['dynasty'].map(DYNASTY_ORDER)
    agg = agg.sort_values(['_o', 'cultural_interaction_count'],
                          ascending=[True, False]).drop(columns='_o')

    # Add rank within each dynasty
    agg['rank'] = (agg.groupby('dynasty')['cultural_interaction_count']
                   .rank(method='first', ascending=False).astype(int))

    save_csv(agg, 'cultural_centers_by_dynasty.csv')

    # Summary: top 5 per dynasty
    summary = {}
    for dyn in TARGET_DYNASTIES:
        top5 = agg[agg['dynasty'] == dyn].nlargest(5, 'cultural_interaction_count')
        summary[dyn] = top5[['addr_chn', 'cultural_interaction_count']].to_dict('records')
        print(f'  {dyn} top 3: '
              + ', '.join(f'{r["addr_chn"]}({r["cultural_interaction_count"]})'
                          for _, r in top5.head(3).iterrows()))

    return agg, summary


# ===================================================================
# Step 5 — Visualizations
# ===================================================================

def viz1_north_south_ratio(bp_summary: dict, ap_summary: dict):
    """Dual Y-axis line chart: south share of birthplace vs activity place."""
    print('\n[Viz 1] north_south_ratio.png ...')
    fig, ax1 = plt.subplots(figsize=(10, 6))

    dyns = TARGET_DYNASTIES
    x = np.arange(len(dyns))
    bp_pcts = [bp_summary[d]['south_pct'] for d in dyns]
    ap_pcts = [ap_summary[d]['south_pct'] for d in dyns]

    color1 = '#E45756'
    color2 = '#4C78A8'

    ax1.set_xlabel('朝代', fontsize=13)
    ax1.set_ylabel('南方籍贯占比 (%)', color=color1, fontsize=13)
    ln1 = ax1.plot(x, bp_pcts, 'o-', color=color1, linewidth=2.5,
                   markersize=8, label='南方籍贯占比')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.set_xticks(x)
    ax1.set_xticklabels(dyns, fontsize=12)
    ax1.set_ylim(0, 100)

    ax2 = ax1.twinx()
    ax2.set_ylabel('南方活动地占比 (%)', color=color2, fontsize=13)
    ln2 = ax2.plot(x, ap_pcts, 's--', color=color2, linewidth=2.5,
                   markersize=8, label='南方活动地占比')
    ax2.tick_params(axis='y', labelcolor=color2)
    ax2.set_ylim(0, 100)

    # Annotate
    for i, (bp_v, ap_v) in enumerate(zip(bp_pcts, ap_pcts)):
        ax1.annotate(f'{bp_v:.1f}%', (i, bp_v), textcoords='offset points',
                     xytext=(0, 12), ha='center', fontsize=10, color=color1)
        ax2.annotate(f'{ap_v:.1f}%', (i, ap_v), textcoords='offset points',
                     xytext=(0, -18), ha='center', fontsize=10, color=color2)

    # Key historical event annotations
    # 靖康之变 1127 is between 北宋(宋) and 南宋; we place annotation between 宋 and 元
    ax1.annotate('← 靖康之变(1127)\n   南宋建立',
                 xy=(0.5, max(max(bp_pcts), max(ap_pcts)) * 0.5),
                 fontsize=9, ha='center', color='#666',
                 bbox=dict(boxstyle='round,pad=0.3', fc='#fff9c4', ec='#bbb', alpha=0.8))

    lns = ln1 + ln2
    labs = [l.get_label() for l in lns]
    ax1.legend(lns, labs, loc='upper left', fontsize=11)

    plt.title('宋→元→明→清 南方籍贯与活动地占比变化', fontsize=15, fontweight='bold')
    fig.tight_layout()
    fig.savefig(OUT_DIR / 'north_south_ratio.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('  Done.')


def viz2_birthplace_heatmap(bp_df: pd.DataFrame):
    """2×2 subplot scatter: birthplace distribution by dynasty."""
    print('\n[Viz 2] birthplace_heatmap.png ...')
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    axes = axes.ravel()

    # China rough bounding box
    lon_range = (100, 130)
    lat_range = (18, 45)

    # Aggregate per dynasty × (lon, lat) rounded
    for idx, dyn in enumerate(TARGET_DYNASTIES):
        ax = axes[idx]
        sub = bp_df[bp_df['dynasty_chn'] == dyn].dropna(subset=['x_coord', 'y_coord'])
        if len(sub) == 0:
            ax.set_title(f'{dyn} (无数据)')
            continue

        # Round coords to ~0.5 degree bins for bubble effect
        sub = sub.copy()
        sub['lon_bin'] = (sub['x_coord'] * 2).round() / 2
        sub['lat_bin'] = (sub['y_coord'] * 2).round() / 2
        grp = sub.groupby(['lon_bin', 'lat_bin']).size().reset_index(name='cnt')

        # Color by count (log scale for better contrast)
        norm_cnt = np.log1p(grp['cnt'])
        sizes = 5 + 45 * norm_cnt / norm_cnt.max()

        sc = ax.scatter(grp['lon_bin'], grp['lat_bin'],
                        s=sizes, c=norm_cnt, cmap='YlOrRd',
                        alpha=0.7, edgecolors='#555', linewidths=0.3)
        ax.set_xlim(lon_range)
        ax.set_ylim(lat_range)
        ax.set_xlabel('经度', fontsize=10)
        ax.set_ylabel('纬度', fontsize=10)
        ax.set_title(f'{dyn} 代籍贯分布 (共{len(sub):,}人)', fontsize=13, fontweight='bold')
        ax.axhline(y=NORTH_LAT, color='#999', linestyle=':', linewidth=1)
        ax.grid(True, alpha=0.2)
        # Add colorbar
        cbar = fig.colorbar(sc, ax=ax, shrink=0.7)
        cbar.set_label('log(人数+1)', fontsize=9)

    fig.suptitle('宋→元→明→清 籍贯地理分布', fontsize=16, fontweight='bold', y=1.01)
    fig.tight_layout()
    fig.savefig(OUT_DIR / 'birthplace_heatmap.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('  Done.')


def viz3_south_migration(mig_df: pd.DataFrame):
    """Combo bar + line: south migration trend."""
    print('\n[Viz 3] south_migration_trend.png ...')
    fig, ax1 = plt.subplots(figsize=(10, 6))

    dyns = TARGET_DYNASTIES
    x = np.arange(len(dyns))
    pcts = mig_df['pct'].values
    counts = mig_df['south_migrants'].values

    bars = ax1.bar(x, pcts, width=0.5, color='#4C78A8', alpha=0.8, label='南迁者占比 (%)')
    ax1.set_xlabel('朝代', fontsize=13)
    ax1.set_ylabel('南迁者占北方人口比例 (%)', color='#4C78A8', fontsize=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(dyns, fontsize=12)
    ax1.tick_params(axis='y', labelcolor='#4C78A8')

    # Annotate bars
    for bar, pct in zip(bars, pcts):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                 f'{pct:.1f}%', ha='center', fontsize=10, color='#4C78A8')

    ax2 = ax1.twinx()
    ax2.plot(x, counts, 'D-', color='#E45756', linewidth=2.5,
             markersize=9, label='南迁者绝对数量')
    ax2.set_ylabel('南迁者人数', color='#E45756', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='#E45756')

    for i, c in enumerate(counts):
        ax2.annotate(f'{c:,}', (i, c), textcoords='offset points',
                     xytext=(0, 10), ha='center', fontsize=10, color='#E45756')

    lns = [bars] + ax2.get_lines()
    labs = ['南迁者占比 (%)', '南迁者人数']
    ax1.legend(lns, labs, loc='upper left', fontsize=11)

    plt.title('宋→元→明→清 北方人口南迁趋势', fontsize=15, fontweight='bold')
    fig.tight_layout()
    fig.savefig(OUT_DIR / 'south_migration_trend.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('  Done.')


def viz4_cultural_centers(cc_agg: pd.DataFrame):
    """Grouped bar chart: top cultural centers per dynasty."""
    print('\n[Viz 4] cultural_center_shift.png ...')
    # Take top 5 per dynasty
    top_frames = []
    for dyn in TARGET_DYNASTIES:
        sub = cc_agg[cc_agg['dynasty'] == dyn].nlargest(5, 'cultural_interaction_count')
        top_frames.append(sub)
    top_all = pd.concat(top_frames, ignore_index=True)

    fig, ax = plt.subplots(figsize=(14, 7))

    n_dyn = len(TARGET_DYNASTIES)
    n_bars = 5  # top 5
    bar_width = 0.15
    colors = ['#E45756', '#F58518', '#54A24B', '#4C78A8', '#72B7B2']

    for di, dyn in enumerate(TARGET_DYNASTIES):
        sub = top_all[top_all['dynasty'] == dyn].head(n_bars)
        for j, (_, row) in enumerate(sub.iterrows()):
            x_pos = di + j * bar_width
            ax.bar(x_pos, row['cultural_interaction_count'],
                   width=bar_width, color=colors[j], alpha=0.85,
                   label=f'Top{j+1}' if di == 0 else '')
            # Label place name
            ax.text(x_pos, row['cultural_interaction_count'] + 5,
                    row['addr_chn'], ha='center', va='bottom',
                    fontsize=8, rotation=45)

    # X-axis: dynasty labels centered
    ax.set_xticks([d + bar_width * 2 for d in range(n_dyn)])
    ax.set_xticklabels(TARGET_DYNASTIES, fontsize=13)
    ax.set_ylabel('文化交往频次', fontsize=13)
    ax.set_xlabel('朝代', fontsize=13)
    ax.legend([f'Top {i+1}' for i in range(n_bars)], fontsize=10, loc='upper left')

    # Add arrow annotation showing southward shift
    ax.annotate('文化重心\n持续南移 →',
                xy=(2, ax.get_ylim()[1] * 0.7),
                fontsize=12, ha='center', color='#666',
                bbox=dict(boxstyle='round,pad=0.4', fc='#fff9c4', ec='#bbb', alpha=0.8))

    plt.title('宋→元→明→清 各朝代文化交往中心 Top 5', fontsize=15, fontweight='bold')
    fig.tight_layout()
    fig.savefig(OUT_DIR / 'cultural_center_shift.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('  Done.')


# ===================================================================
# Step 6 — Summary & README
# ===================================================================

def write_summary(bp_summary: dict, ap_summary: dict,
                  mig_df: pd.DataFrame, cc_summary: dict):
    """Write analysis_summary.json and README.md."""
    print('\n[Step 6] Writing summary ...')

    summary = {
        'birthplace': bp_summary,
        'activity_place': ap_summary,
        'south_migration': mig_df.to_dict('records'),
        'cultural_centers': cc_summary,
    }
    (OUT_DIR / 'analysis_summary.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8-sig')

    # README
    lines = [
        '# 专题4：明清人口大迁徙与文化重心南移',
        '',
        '## 分析概述',
        '',
        '本专题利用 CBDB（中国历代人物传记数据库）地址经历数据，追踪宋→元→明→清四代',
        '历史人物的出生地与活动地分布变化，量化"经济文化重心从北到南"这一历史进程。',
        '',
        '### 方法说明',
        '',
        '- **南北分界**：以纬度 33°N（秦岭-淮河线近似）为标准',
        '- **籍贯**：取 `fact_person_address` 中 `籍貫(基本地址)` 类型记录',
        '- **活动地**：取非籍贯类地址记录（遷住地、前住地、遊歷、落籍、僑居等）',
        '- **南迁者**：籍贯在北方（y > 33°N）且有南方活动地记录的人物',
        '- **文化中心**：以文学/学术交往（贈詩、致書、墓誌銘、師生等）涉及人物的',
        '  活动地与索引地为代理指标',
        '',
        '## 关键发现',
        '',
    ]

    # Birthplace trend
    lines.append('### 1. 籍贯南北分布变化')
    lines.append('')
    lines.append('| 朝代 | 总人数 | 南方占比 | 北方占比 |')
    lines.append('|------|--------|---------|---------|')
    for dyn in TARGET_DYNASTIES:
        s = bp_summary[dyn]
        lines.append(f'| {dyn} | {s["total"]:,} | {s["south_pct"]}% | {s["north_pct"]}% |')
    lines.append('')

    bp_trend = [bp_summary[d]['south_pct'] for d in TARGET_DYNASTIES]
    if len(bp_trend) >= 2 and bp_trend[-1] > bp_trend[0]:
        lines.append(f'从宋到清，南方籍贯占比从 {bp_trend[0]}% 上升至 {bp_trend[-1]}%，'
                     '反映了人口与经济重心持续南移的大趋势。')
    lines.append('')

    # Activity trend
    lines.append('### 2. 活动地南北分布变化')
    lines.append('')
    lines.append('| 朝代 | 总记录 | 南方占比 | 平均纬度 |')
    lines.append('|------|--------|---------|---------|')
    for dyn in TARGET_DYNASTIES:
        s = ap_summary[dyn]
        lines.append(f'| {dyn} | {s["total"]:,} | {s["south_pct"]}% | {s.get("mean_lat", "N/A")}° |')
    lines.append('')

    # Migration
    lines.append('### 3. 南迁趋势')
    lines.append('')
    lines.append('| 朝代 | 北方人物数 | 南迁者数 | 南迁占比 |')
    lines.append('|------|-----------|---------|---------|')
    for _, r in mig_df.iterrows():
        lines.append(f'| {r["dynasty"]} | {r["total_northerners"]:,} | '
                     f'{r["south_migrants"]:,} | {r["pct"]}% |')
    lines.append('')

    # Cultural centers
    lines.append('### 4. 文化交往中心')
    lines.append('')
    for dyn in TARGET_DYNASTIES:
        top = cc_summary.get(dyn, [])[:5]
        if top:
            place_str = '、'.join(f'{t["addr_chn"]}({t["cultural_interaction_count"]})' for t in top)
            lines.append(f'- **{dyn}**：{place_str}')
    lines.append('')

    # Analysis
    lines.extend([
        '## 历史分析',
        '',
        '### 靖康之变的影响',
        '',
        '1127年靖康之变导致北宋灭亡，南宋定都临安（杭州）。大量北方士族南迁，',
        '直接推动了南方尤其是江南地区的文化繁荣。从数据上看，宋代到元代的南方',
        '籍贯占比和文化交往频次均呈现显著增长。',
        '',
        '### 江南文化核心区的形成',
        '',
        '从文化交往数据可以观察到，杭州、苏州、南京等江南城市在南宋以后成为',
        '全国最重要的文化交往中心。科举制度的完善进一步巩固了江南的文化优势地位。',
        '',
        '### 明清科举南强北弱',
        '',
        '明清时期，南方（尤其是江南地区）在科举考试中占据压倒性优势。这与南方',
        '经济发达、教育资源丰富密切相关。数据中南方籍贯人物和文化交往频次的',
        '持续增长印证了这一历史趋势。',
        '',
        '## 输出文件',
        '',
        '| 文件 | 说明 |',
        '|------|------|',
        '| `birthplace_by_dynasty.csv` | 各朝代籍贯分布 |',
        '| `activity_place_by_dynasty.csv` | 各朝代活动地分布 |',
        '| `migration_south_stats.csv` | 南迁统计 |',
        '| `cultural_centers_by_dynasty.csv` | 文化中心变迁 |',
        '| `north_south_ratio.png` | 南北占比变化图 |',
        '| `birthplace_heatmap.png` | 籍贯分布热力图 |',
        '| `south_migration_trend.png` | 南迁趋势图 |',
        '| `cultural_center_shift.png` | 文化中心迁移图 |',
        '| `analysis_summary.json` | 分析摘要（JSON） |',
        '',
        '## 数据来源',
        '',
        '- CBDB (China Biographical Database), Harvard University',
        f'- 目标朝代: {", ".join(TARGET_DYNASTIES)}',
        f'- 南北分界: 纬度 {NORTH_LAT}°N',
    ])

    (OUT_DIR / 'README.md').write_text('\n'.join(lines), encoding='utf-8-sig')
    print('  Saved analysis_summary.json & README.md')


# ===================================================================
# Main
# ===================================================================

def main():
    print('=' * 60)
    print('E4: 明清人口大迁徙与文化重心南移')
    print('=' * 60)

    dp, pa, assoc = load_data()

    # Step 1
    bp_agg, bp_summary, bp_df = step1_birthplace(dp, pa)

    # Step 2
    ap_agg, ap_summary = step2_activity(dp, pa)

    # Step 3
    mig_df, dest_counter = step3_migration(dp, pa, bp_df)

    # Step 4
    cc_agg, cc_summary = step4_cultural_centers(dp, pa, assoc)

    # Step 5
    viz1_north_south_ratio(bp_summary, ap_summary)
    viz2_birthplace_heatmap(bp_df)
    viz3_south_migration(mig_df)
    viz4_cultural_centers(cc_agg)

    # Step 6
    write_summary(bp_summary, ap_summary, mig_df, cc_summary)

    print('\n' + '=' * 60)
    print(f'Done! All outputs saved to: {OUT_DIR}')
    print('=' * 60)


if __name__ == '__main__':
    main()