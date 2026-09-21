# -*- coding: utf-8 -*-
"""
Part C: 地图呈现历史人物迁移关系
"""
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import folium
from folium import FeatureGroup, LayerControl, PolyLine, CircleMarker
from folium import MacroElement
from jinja2 import Template
import numpy as np
import os
import math

# === 配置 ===
BASE_DIR = r'D:\虚拟C盘\study\人工智能与计算思维大作业'
INPUT_DIR = os.path.join(BASE_DIR, 'output_cbdb_v1')
OUTPUT_DIR = os.path.join(BASE_DIR, '任务c')
os.makedirs(OUTPUT_DIR, exist_ok=True)

TARGET_PERSONS = {
    3767: '蘇軾', 32540: '李白', 3915: '杜甫', 8175: '岳飛',
    35222: '袁宏道', 32227: '白居易', 32174: '王維', 19713: '李清照'
}
PERSON_ORDER = list(TARGET_PERSONS.keys())
COLORS_LIST = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8',
               '#f58231', '#911eb4', '#42d4f4', '#f032e6']
PERSON_COLORS = {pid: COLORS_LIST[i] for i, pid in enumerate(PERSON_ORDER)}

# 中文字体设置
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def darken_color(hex_color, factor):
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r = max(0, int(r * (1 - factor)))
    g = max(0, int(g * (1 - factor)))
    b = max(0, int(b * (1 - factor)))
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)


# === Step 1: 从地址表提取轨迹 ===
print("[1/10] 读取地址经历表...")
addr_df = pd.read_csv(
    os.path.join(INPUT_DIR, 'fact_person_address.csv'),
    encoding='utf-8-sig',
    usecols=['c_personid', 'c_firstyear', 'y_coord', 'x_coord', 'addr_chn', 'c_addr_desc_chn']
)

addr_df = addr_df[addr_df['c_personid'].isin(TARGET_PERSONS.keys())].copy()
addr_df.rename(columns={
    'c_firstyear': 'year',
    'y_coord': 'lat',
    'x_coord': 'lon',
    'addr_chn': 'place_name',
    'c_addr_desc_chn': 'event_type'
}, inplace=True)

addr_df['year'] = pd.to_numeric(addr_df['year'], errors='coerce')
addr_df['lat'] = pd.to_numeric(addr_df['lat'], errors='coerce')
addr_df['lon'] = pd.to_numeric(addr_df['lon'], errors='coerce')
addr_df = addr_df.dropna(subset=['lat', 'lon'])
addr_df = addr_df[(addr_df['lat'] != 0) & (addr_df['lon'] != 0)]
print("  地址表：{} 条有效记录".format(len(addr_df)))


# === Step 2: 从任官表提取轨迹 ===
print("[2/10] 读取任官驻地表...")
post_df = pd.read_csv(
    os.path.join(INPUT_DIR, 'fact_person_posting.csv'),
    encoding='utf-8-sig',
    usecols=['c_personid', 'c_firstyear', 'y_coord', 'x_coord', 'posting_addr_chn']
)

post_df = post_df[post_df['c_personid'].isin(TARGET_PERSONS.keys())].copy()
post_df.rename(columns={
    'c_firstyear': 'year',
    'y_coord': 'lat',
    'x_coord': 'lon',
    'posting_addr_chn': 'place_name'
}, inplace=True)
post_df['event_type'] = '任官駐地'

post_df['year'] = pd.to_numeric(post_df['year'], errors='coerce')
post_df['lat'] = pd.to_numeric(post_df['lat'], errors='coerce')
post_df['lon'] = pd.to_numeric(post_df['lon'], errors='coerce')
post_df = post_df.dropna(subset=['lat', 'lon'])
post_df = post_df[(post_df['lat'] != 0) & (post_df['lon'] != 0)]
print("  任官表：{} 条有效记录".format(len(post_df)))


# === Step 3: 纵向合并 ===
print("[3/10] 合并轨迹数据...")
trajectory_df = pd.concat([addr_df, post_df], ignore_index=True)
print("  合并后：{} 条记录".format(len(trajectory_df)))


# === Step 4: 补充人物信息 ===
print("[4/10] 补充人物信息...")
dim_df = pd.read_csv(
    os.path.join(INPUT_DIR, 'dim_person.csv'),
    encoding='utf-8-sig',
    usecols=['c_personid', 'c_name_chn', 'dynasty_chn']
)
dim_df = dim_df[dim_df['c_personid'].isin(TARGET_PERSONS.keys())]
trajectory_df = trajectory_df.merge(dim_df, on='c_personid', how='left')


# === Step 5: 排序与去重 ===
print("[5/10] 排序与去重...")
trajectory_df.loc[trajectory_df['year'] == 0, 'year'] = np.nan
trajectory_df['_year_sort'] = trajectory_df['year'].fillna(float('inf'))
trajectory_df.sort_values(['c_personid', '_year_sort'], inplace=True)
trajectory_df.drop(columns=['_year_sort'], inplace=True)
trajectory_df.reset_index(drop=True, inplace=True)

deduped_rows = []
for pid, group in trajectory_df.groupby('c_personid'):
    group = group.reset_index(drop=True)
    keep = []
    prev_lat, prev_lon = None, None
    for idx, row in group.iterrows():
        if prev_lat is not None:
            dist = math.sqrt((row['lat'] - prev_lat)**2 + (row['lon'] - prev_lon)**2)
            if dist < 0.01:
                continue
        keep.append(idx)
        prev_lat, prev_lon = row['lat'], row['lon']
    deduped_rows.append(group.loc[keep])

trajectory_df = pd.concat(deduped_rows, ignore_index=True)
print("  去重后：{} 条记录".format(len(trajectory_df)))


# === Step 6: 保存轨迹数据 CSV ===
print("[6/10] 保存轨迹数据 CSV...")
trajectory_df.to_csv(
    os.path.join(OUTPUT_DIR, 'migration_trajectory_data.csv'),
    index=False,
    encoding='utf-8-sig'
)


# === Step 7: 生成统计摘要 ===
print("[7/10] 生成统计摘要...")
summary_records = []
for pid in PERSON_ORDER:
    sub = trajectory_df[trajectory_df['c_personid'] == pid]
    name = TARGET_PERSONS[pid]
    dynasty = sub['dynasty_chn'].iloc[0] if len(sub) > 0 else ''
    count = len(sub)
    years = sub['year'].dropna()
    min_year = int(years.min()) if len(years) > 0 else ''
    max_year = int(years.max()) if len(years) > 0 else ''
    lat_range = "{:.2f} ~ {:.2f}".format(sub['lat'].min(), sub['lat'].max()) if count > 0 else ''
    lon_range = "{:.2f} ~ {:.2f}".format(sub['lon'].min(), sub['lon'].max()) if count > 0 else ''
    summary_records.append({
        'personid': pid,
        'name': name,
        'dynasty': dynasty,
        'trajectory_count': count,
        'min_year': min_year,
        'max_year': max_year,
        'lat_range': lat_range,
        'lon_range': lon_range
    })

summary_df = pd.DataFrame(summary_records)
summary_df.to_csv(
    os.path.join(OUTPUT_DIR, 'migration_summary.csv'),
    index=False,
    encoding='utf-8-sig'
)


# === Step 8: Folium 交互式地图 ===
print("[8/10] 生成 Folium 交互式地图...")

all_lats = trajectory_df['lat'].values
all_lons = trajectory_df['lon'].values
center_lat = (all_lats.min() + all_lats.max()) / 2
center_lon = (all_lons.min() + all_lons.max()) / 2

m = folium.Map(location=[center_lat, center_lon], tiles="OpenStreetMap")

legend_template = """
{% macro html(this, kwargs) %}
<div style="
    position: fixed;
    top: 10px; right: 10px;
    z-index: 9999;
    background-color: white;
    border: 2px solid grey;
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 13px;
    font-family: Microsoft YaHei, SimHei, sans-serif;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
">
<b style="font-size:14px;">人物图例</b><br>
{% for item in this.legend_items %}
<span style="color:{{ item.color }}; font-size:16px;">&#9679;</span>
&nbsp;{{ item.name }} ({{ item.dynasty }})<br>
{% endfor %}
</div>
{% endmacro %}
"""


class Legend(MacroElement):
    def __init__(self, legend_items):
        super().__init__()
        self.legend_items = legend_items
        self._template = Template(legend_template)


legend_items = []
for pid in PERSON_ORDER:
    name = TARGET_PERSONS[pid]
    dynasty_row = trajectory_df[trajectory_df['c_personid'] == pid]
    dynasty = dynasty_row['dynasty_chn'].iloc[0] if len(dynasty_row) > 0 else ''
    legend_items.append({'name': name, 'dynasty': dynasty, 'color': PERSON_COLORS[pid]})

m.get_root().add_child(Legend(legend_items))

for pid in PERSON_ORDER:
    sub = trajectory_df[trajectory_df['c_personid'] == pid].copy()
    if len(sub) == 0:
        continue
    name = TARGET_PERSONS[pid]
    color = PERSON_COLORS[pid]
    fg = FeatureGroup(name=name, show=True)

    sub = sub.sort_values('year', na_position='last').reset_index(drop=True)

    points = sub[['lat', 'lon']].values.tolist()
    if len(points) >= 2:
        PolyLine(locations=points, color=color, weight=2.5, opacity=0.7).add_to(fg)

    years_valid = sub['year'].dropna()
    if len(years_valid) > 0:
        min_year_val = years_valid.min()
        max_year_val = years_valid.max()
        start_idx = sub[sub['year'] == min_year_val].index[0]
        end_idx = sub[sub['year'] == max_year_val].index[0]
    else:
        start_idx = sub.index[0]
        end_idx = sub.index[-1]

    for idx, row in sub.iterrows():
        year_str = str(int(row['year'])) if pd.notna(row['year']) else '未知'
        popup_html = (
            "<table style='font-size:12px;'>"
            "<tr><td><b>人物</b></td><td>{}</td></tr>"
            "<tr><td><b>年份</b></td><td>{}</td></tr>"
            "<tr><td><b>地点</b></td><td>{}</td></tr>"
            "<tr><td><b>类型</b></td><td>{}</td></tr>"
            "</table>"
        ).format(row.get('c_name_chn', name), year_str, row['place_name'], row['event_type'])

        if idx == start_idx:
            CircleMarker(
                location=[row['lat'], row['lon']],
                radius=8, color=color, weight=3,
                fill=True, fill_color=color, fill_opacity=0.9,
                popup=folium.Popup(popup_html, max_width=300)
            ).add_to(fg)
        elif idx == end_idx and end_idx != start_idx:
            darker = darken_color(color, 0.3)
            CircleMarker(
                location=[row['lat'], row['lon']],
                radius=7, color=darker, weight=3,
                fill=True, fill_color=darker, fill_opacity=0.9,
                popup=folium.Popup(popup_html, max_width=300)
            ).add_to(fg)
        else:
            CircleMarker(
                location=[row['lat'], row['lon']],
                radius=5, color=color, weight=1.5,
                fill=True, fill_color=color, fill_opacity=0.7,
                popup=folium.Popup(popup_html, max_width=300)
            ).add_to(fg)

    fg.add_to(m)

m.fit_bounds([[all_lats.min(), all_lons.min()], [all_lats.max(), all_lons.max()]])
LayerControl(collapsed=False).add_to(m)

folium_path = os.path.join(OUTPUT_DIR, 'migration_map.html')
m.save(folium_path)
print("  Folium 交互式地图已保存")


# === Step 9: Matplotlib 静态地图 ===
print("[9/10] 生成 Matplotlib 静态地图...")

fig, ax = plt.subplots(figsize=(14, 10))
fig.patch.set_facecolor('#f5f5f5')
ax.set_facecolor('#f5f5f5')

lat_pad = (all_lats.max() - all_lats.min()) * 0.05
lon_pad = (all_lons.max() - all_lons.min()) * 0.05
ax.set_xlim(all_lons.min() - lon_pad, all_lons.max() + lon_pad)
ax.set_ylim(all_lats.min() - lat_pad, all_lats.max() + lat_pad)

for pid in PERSON_ORDER:
    sub = trajectory_df[trajectory_df['c_personid'] == pid].copy()
    if len(sub) == 0:
        continue
    name = TARGET_PERSONS[pid]
    dynasty_val = sub['dynasty_chn'].iloc[0]
    color = PERSON_COLORS[pid]
    label = "{} ({})".format(name, dynasty_val)

    sub = sub.sort_values('year', na_position='last').reset_index(drop=True)

    ax.plot(sub['lon'].values, sub['lat'].values,
            color=color, linewidth=1.5, alpha=0.7, label=label)
    ax.scatter(sub['lon'].values, sub['lat'].values,
               color=color, s=20, zorder=3)

    years_valid = sub['year'].dropna()
    if len(years_valid) > 0:
        start_row = sub[sub['year'] == years_valid.min()].iloc[0]
        end_row = sub[sub['year'] == years_valid.max()].iloc[0]
    else:
        start_row = sub.iloc[0]
        end_row = sub.iloc[-1]

    ax.scatter(start_row['lon'], start_row['lat'],
               color=color, marker='*', s=100, zorder=4, edgecolors='black', linewidths=0.5)
    if len(sub) > 1:
        ax.scatter(end_row['lon'], end_row['lat'],
                   color=color, marker='s', s=80, zorder=4, edgecolors='black', linewidths=0.5)

ax.set_xlabel('经度', fontsize=12)
ax.set_ylabel('纬度', fontsize=12)
ax.set_title('中国历代名人迁移轨迹', fontsize=16, fontweight='bold')
ax.legend(loc='upper left', bbox_to_anchor=(1.15, 1), fontsize=10)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'migration_map_static.png'), dpi=200, bbox_inches='tight')
plt.close()
print("  静态总图已保存")


# --- 9b: 按朝代分子图 ---
dynasty_person_map = {}
for pid in PERSON_ORDER:
    sub = trajectory_df[trajectory_df['c_personid'] == pid]
    if len(sub) > 0:
        dy = sub['dynasty_chn'].iloc[0]
        if dy not in dynasty_person_map:
            dynasty_person_map[dy] = []
        dynasty_person_map[dy].append(pid)

dynasty_order = ['唐', '宋', '明']

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.patch.set_facecolor('#f5f5f5')

for i, dy in enumerate(dynasty_order):
    ax = axes[i]
    ax.set_facecolor('#f5f5f5')

    pids_in_dynasty = dynasty_person_map.get(dy, [])

    if len(pids_in_dynasty) == 0:
        ax.set_title(dy, fontsize=14, fontweight='bold')
        ax.text(0.5, 0.5, '无数据', transform=ax.transAxes,
                ha='center', va='center', fontsize=14, color='grey')
        continue

    dy_lats = []
    dy_lons = []

    for pid in pids_in_dynasty:
        sub = trajectory_df[trajectory_df['c_personid'] == pid].copy()
        if len(sub) == 0:
            continue
        dy_lats.extend(sub['lat'].values.tolist())
        dy_lons.extend(sub['lon'].values.tolist())

        name = TARGET_PERSONS[pid]
        color = PERSON_COLORS[pid]
        sub = sub.sort_values('year', na_position='last').reset_index(drop=True)

        ax.plot(sub['lon'].values, sub['lat'].values,
                color=color, linewidth=1.5, alpha=0.7, label=name)
        ax.scatter(sub['lon'].values, sub['lat'].values,
                   color=color, s=20, zorder=3)

        years_valid = sub['year'].dropna()
        if len(years_valid) > 0:
            start_row = sub[sub['year'] == years_valid.min()].iloc[0]
            end_row = sub[sub['year'] == years_valid.max()].iloc[0]
        else:
            start_row = sub.iloc[0]
            end_row = sub.iloc[-1]

        ax.scatter(start_row['lon'], start_row['lat'],
                   color=color, marker='*', s=100, zorder=4, edgecolors='black', linewidths=0.5)
        if len(sub) > 1:
            ax.scatter(end_row['lon'], end_row['lat'],
                       color=color, marker='s', s=80, zorder=4, edgecolors='black', linewidths=0.5)

    if dy_lats and dy_lons:
        lp = (max(dy_lats) - min(dy_lats)) * 0.05
        lop = (max(dy_lons) - min(dy_lons)) * 0.05
        if lp < 0.1:
            lp = 0.5
        if lop < 0.1:
            lop = 0.5
        ax.set_xlim(min(dy_lons) - lop, max(dy_lons) + lop)
        ax.set_ylim(min(dy_lats) - lp, max(dy_lats) + lp)

    ax.set_title(dy, fontsize=14, fontweight='bold')
    ax.set_xlabel('经度', fontsize=10)
    ax.set_ylabel('纬度', fontsize=10)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'migration_by_dynasty.png'), dpi=200, bbox_inches='tight')
plt.close()
print("  按朝代分子图已保存")


# === Step 10: 校验打印 ===
print("")
print("=" * 60)
print("校验摘要")
print("=" * 60)
for rec in summary_records:
    print("  {} ({})：轨迹点 {} 个，年份 {} ~ {}，纬度 {}，经度 {}".format(
        rec['name'], rec['dynasty'], rec['trajectory_count'],
        rec['min_year'], rec['max_year'], rec['lat_range'], rec['lon_range']))
print("=" * 60)
print("Part C 完成！")

