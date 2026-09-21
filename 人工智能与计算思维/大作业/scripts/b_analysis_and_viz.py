# -*- coding: utf-8 -*-
"""
B 问：历史人物维度 + 各朝代数量分布（改进版 v2）
读取 output_cbdb_v1/ 的已数据化 CSV，输出统计 CSV 与论文图表。

改进点：
1. 修复"未知"重复出现 bug（归一化后去重）
2. 增加"主朝代"聚合（先秦~清），其余归为"其他/非主朝代"
3. 过滤非中国朝代噪声（朝鮮、韓國、高麗、新羅、中華人民共和國）
4. 增加主朝代聚合图表，更适合论文展示
5. 改进图表样式与可读性
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / "output_cbdb_v1"
OUT_DIR = ROOT / "analysis_b"
CHART_DIR = OUT_DIR / "charts"
OUT_DIR.mkdir(exist_ok=True)
CHART_DIR.mkdir(exist_ok=True)

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ========== 主朝代定义 ==========
# 按历史时间顺序排列的主要朝代
MAIN_DYNASTY_ORDER = [
    '先秦', '秦', '西漢', '東漢', '三國', '西晉', '東晉',
    '南北朝', '隋', '唐', '五代十國', '北宋', '南宋', '遼', '金', '元', '明', '清'
]

# 原始朝代 → 主朝代映射
DYNASTY_TO_MAIN = {
    # 主朝代直接映射
    '西漢': '西漢', '東漢': '東漢', '三國': '三國',
    '西晉': '西晉', '東晉': '東晉', '南北朝': '南北朝',
    '隋': '隋', '唐': '唐', '遼': '遼', '金': '金',
    '元': '元', '明': '明', '清': '清',
    # 三國子朝代
    '三國魏': '三國', '三國吳': '三國', '三國蜀': '三國',
    # 南北朝子朝代
    '北魏': '南北朝', '北齊': '南北朝', '北周': '南北朝',
    '東魏': '南北朝', '西魏': '南北朝',
    '南梁': '南北朝', '南齊': '南北朝', '陳': '南北朝',
    '宋(劉)': '南北朝',  # 南朝宋
    '前秦': '南北朝', '後秦': '南北朝', '前燕': '南北朝',
    '後燕': '南北朝', '南燕': '南北朝', '西燕': '南北朝',
    '後趙': '南北朝', '前趙': '南北朝', '前涼': '南北朝',
    '後涼': '南北朝', '西涼': '南北朝', '北涼': '南北朝',
    '南平': '南北朝', '西秦': '南北朝', '北燕': '南北朝',
    '東梁': '南北朝', '西梁': '南北朝', '代': '南北朝',
    # 五代十國
    '五代': '五代十國', '後梁': '五代十國', '後唐': '五代十國',
    '後晉': '五代十國', '後漢': '五代十國', '後周': '五代十國',
    '後蜀': '五代十國', '前蜀': '五代十國',
    '南唐': '五代十國', '南漢': '五代十國',
    '吳越': '五代十國', '閩國': '五代十國',
    '吳(楊)': '五代十國', '楚(馬)': '五代十國',
    '北漢': '五代十國', '偽齊': '五代十國',
    '鄭（王世充）': '五代十國',
    # 宋
    '宋': '南宋',  # CBDB 中"宋"主要指南宋时期
    # 先秦
    '周': '先秦', '贏秦': '先秦', '秦漢': '先秦', '漢前': '先秦',
    '吳': '先秦', '晉': '先秦', '新': '西漢',  # 新朝归入西漢
    '西遼': '遼',
}

# 非中国朝代（噪声）
NON_CHINESE_DYNASTIES = {'朝鮮', '韓國', '高麗', '新羅'}


def norm_dynasty(v: str) -> str:
    """标准化朝代名：空值/未詳 → 未知"""
    if v is None:
        return '未知'
    s = str(v).strip()
    if s in ('', '未詳', 'None', 'null'):
        return '未知'
    return s


def norm_gender(v: str) -> str:
    """标准化性别：0→男, 1→女, 其他→未知"""
    if v is None:
        return '未知'
    s = str(v).strip()
    if s == '0':
        return '男'
    if s == '1':
        return '女'
    return '未知'


def to_main_dynasty(dyn: str) -> str:
    """将原始朝代映射到主朝代"""
    if dyn == '未知':
        return '未知'
    if dyn in NON_CHINESE_DYNASTIES:
        return '非中国朝代'
    if dyn in DYNASTY_TO_MAIN:
        return DYNASTY_TO_MAIN[dyn]
    return '其他'


def write_csv(path: Path, header, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(header)
        for row in rows:
            w.writerow(row)


def sorted_dynasties(counter: Counter, use_main: bool = False):
    """按时间顺序排列朝代，未知放最后"""
    if use_main:
        order = MAIN_DYNASTY_ORDER
    else:
        # 保留原始顺序（按样本量降序）
        order = []
    known = [d for d in (order if use_main else []) if d in counter]
    if not use_main:
        # 按样本量降序排列非未知项
        known = sorted([d for d in counter if d != '未知'], key=lambda x: (-counter[x], x))
    extra = [d for d in counter if d not in known and d != '未知']
    out = known + sorted(extra)
    if '未知' in counter:
        out.append('未知')
    return out


# ========== 图表函数 ==========
def plot_bar(path: Path, title, labels, values, rotate=45, color='#4C78A8', figsize=(14, 6)):
    plt.figure(figsize=figsize, dpi=200)
    bars = plt.bar(range(len(labels)), values, color=color, edgecolor='white', linewidth=0.5)
    plt.xticks(range(len(labels)), labels, rotation=rotate, ha='right', fontsize=9)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.ylabel('人物数量', fontsize=11)
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()
    plt.savefig(path, bbox_inches='tight')
    plt.close()


def plot_stacked_bar(path: Path, title, labels, group_labels, data, figsize=(16, 8)):
    plt.figure(figsize=figsize, dpi=200)
    bottom = [0] * len(labels)
    colors = ['#4C78A8', '#F58518', '#E45756', '#72B7B2', '#54A24B',
              '#EECA3B', '#B279A2', '#FF9DA6', '#9D755D', '#BAB0AC',
              '#499894', '#D7B5A6']
    for i, grp in enumerate(group_labels):
        vals = [data[grp].get(l, 0) for l in labels]
        plt.bar(range(len(labels)), vals, bottom=bottom, label=grp,
                color=colors[i % len(colors)], edgecolor='white', linewidth=0.3)
        bottom = [b + v for b, v in zip(bottom, vals)]
    plt.xticks(range(len(labels)), labels, rotation=45, ha='right', fontsize=9)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.ylabel('事实记录数', fontsize=11)
    plt.legend(ncol=2, fontsize=8, bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()
    plt.savefig(path, bbox_inches='tight')
    plt.close()


def plot_stacked_percent(path: Path, title, labels, group_labels, data, figsize=(14, 7)):
    plt.figure(figsize=figsize, dpi=200)
    totals = []
    for l in labels:
        totals.append(sum(data[g].get(l, 0) for g in group_labels) or 1)
    bottom = [0] * len(labels)
    colors = ['#4C78A8', '#F58518', '#E45756', '#72B7B2', '#54A24B']
    for i, grp in enumerate(group_labels):
        vals = [data[grp].get(l, 0) / t * 100 for l, t in zip(labels, totals)]
        plt.bar(range(len(labels)), vals, bottom=bottom, label=grp,
                color=colors[i % len(colors)], edgecolor='white', linewidth=0.3)
        bottom = [b + v for b, v in zip(bottom, vals)]
    plt.xticks(range(len(labels)), labels, rotation=45, ha='right', fontsize=9)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.ylabel('百分比 (%)', fontsize=11)
    plt.legend(ncol=2, fontsize=9)
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()
    plt.savefig(path, bbox_inches='tight')
    plt.close()


def plot_horizontal_bar(path: Path, title, labels, values, figsize=(10, 8)):
    """水平柱状图，适合标签较长的情况"""
    plt.figure(figsize=figsize, dpi=200)
    y_pos = range(len(labels))
    plt.barh(y_pos, values, color='#4C78A8', edgecolor='white', linewidth=0.5)
    plt.yticks(y_pos, labels, fontsize=10)
    plt.xlabel('数量', fontsize=11)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.grid(axis='x', alpha=0.3, linestyle='--')
    plt.tight_layout()
    plt.savefig(path, bbox_inches='tight')
    plt.close()


def main():
    dim_path = IN_DIR / "dim_person.csv"
    status_path = IN_DIR / "fact_person_status.csv"
    addr_path = IN_DIR / "fact_person_address.csv"

    # ========== 读取 dim_person ==========
    print("读取 dim_person.csv ...")
    dyn_counter = Counter()          # 原始朝代计数
    main_dyn_counter = Counter()     # 主朝代计数
    gender_counter = Counter()
    dyn_gender = defaultdict(Counter)
    main_dyn_gender = defaultdict(Counter)
    dyn_map = {}                     # personid → 原始朝代
    main_dyn_map = {}                # personid → 主朝代

    with dim_path.open('r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            dyn = norm_dynasty(row['dynasty_chn'])
            main_dyn = to_main_dynasty(dyn)
            gen = norm_gender(row['c_female'])
            pid = row['c_personid']

            dyn_counter[dyn] += 1
            main_dyn_counter[main_dyn] += 1
            gender_counter[gen] += 1
            dyn_gender[dyn][gen] += 1
            main_dyn_gender[main_dyn][gen] += 1
            dyn_map[pid] = dyn
            main_dyn_map[pid] = main_dyn

    print(f"  人物总数（唯一 c_personid）: {len(dyn_map)}")
    print(f"  原始朝代种类: {len(dyn_counter)}")
    print(f"  主朝代种类: {len(main_dyn_counter)}")

    # ========== 读取 fact_person_status ==========
    print("读取 fact_person_status.csv ...")
    dyn_status = defaultdict(Counter)
    main_dyn_status = defaultdict(Counter)
    status_counter = Counter()

    with status_path.open('r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            st = (row.get('c_status_desc_chn') or '').strip() or '未知'
            dyn = dyn_map.get(row['c_personid'], '未知')
            main_dyn = main_dyn_map.get(row['c_personid'], '未知')
            dyn_status[dyn][st] += 1
            main_dyn_status[main_dyn][st] += 1
            status_counter[st] += 1

    # ========== 读取 fact_person_address ==========
    print("读取 fact_person_address.csv ...")
    dyn_addr = defaultdict(Counter)
    main_dyn_addr = defaultdict(Counter)
    addr_counter = Counter()

    with addr_path.open('r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            at = (row.get('c_addr_desc_chn') or '').strip() or '未知'
            dyn = dyn_map.get(row['c_personid'], '未知')
            main_dyn = main_dyn_map.get(row['c_personid'], '未知')
            dyn_addr[dyn][at] += 1
            main_dyn_addr[main_dyn][at] += 1
            addr_counter[at] += 1

    # ========== 输出 CSV：原始朝代 ==========
    print("输出 CSV ...")
    dyns = sorted_dynasties(dyn_counter)
    write_csv(OUT_DIR / 'person_dynasty_counts.csv',
              ['dynasty_chn', 'person_count'],
              [(d, dyn_counter[d]) for d in dyns])

    # ========== 输出 CSV：主朝代 ==========
    main_dyns = sorted_dynasties(main_dyn_counter, use_main=True)
    # 过滤掉非中国朝代和未知后的主朝代列表
    main_dyns_china = [d for d in main_dyns if d not in ('非中国朝代', '其他', '未知')]
    main_dyns_all = main_dyns  # 含其他和未知

    write_csv(OUT_DIR / 'person_main_dynasty_counts.csv',
              ['main_dynasty', 'person_count'],
              [(d, main_dyn_counter[d]) for d in main_dyns_all])

    # ========== 身份统计 ==========
    top_status = [s for s, _ in status_counter.most_common(10)]
    rows = []
    for d in main_dyns_all:
        for s in top_status:
            rows.append((d, s, main_dyn_status[d][s]))
    write_csv(OUT_DIR / 'status_by_dynasty_counts.csv',
              ['main_dynasty', 'status_desc', 'fact_count'], rows)

    # ========== 地址类型统计 ==========
    top_addr = [s for s, _ in addr_counter.most_common(10)]
    rows = []
    for d in main_dyns_all:
        for a in top_addr:
            rows.append((d, a, main_dyn_addr[d][a]))
    write_csv(OUT_DIR / 'address_type_by_dynasty_counts.csv',
              ['main_dynasty', 'address_type_desc', 'fact_count'], rows)

    # ========== 性别统计 ==========
    genders = ['男', '女', '未知']
    rows = []
    for d in main_dyns_all:
        for g in genders:
            rows.append((d, g, main_dyn_gender[d][g]))
    write_csv(OUT_DIR / 'gender_by_dynasty_counts.csv',
              ['main_dynasty', 'gender', 'person_count'], rows)

    # ========== 图表 ==========
    print("生成图表 ...")

    # 图1：主朝代人物数量（中国朝代，不含非中国/其他/未知）
    china_counts = [main_dyn_counter[d] for d in main_dyns_china]
    plot_bar(CHART_DIR / 'dynasty_person_counts.png',
             '中国主要朝代历史人物数量分布',
             main_dyns_china, china_counts,
             color='#4C78A8', figsize=(14, 6))

    # 图2：主朝代身份类型堆叠柱状图
    data = {s: {d: main_dyn_status[d][s] for d in main_dyns_china} for s in top_status}
    plot_stacked_bar(CHART_DIR / 'status_by_dynasty_stacked.png',
                     '各朝代主要身份类型分布（Top 10）',
                     main_dyns_china, top_status, data)

    # 图3：主朝代地址类型堆叠柱状图
    data = {a: {d: main_dyn_addr[d][a] for d in main_dyns_china} for a in top_addr}
    plot_stacked_bar(CHART_DIR / 'address_type_by_dynasty_stacked.png',
                     '各朝代主要地址类型分布（Top 10）',
                     main_dyns_china, top_addr, data)

    # 图4：主朝代性别结构百分比
    data = {g: {d: main_dyn_gender[d][g] for d in main_dyns_china} for g in genders}
    plot_stacked_percent(CHART_DIR / 'gender_by_dynasty_percent.png',
                         '各朝代性别结构（百分比）',
                         main_dyns_china, genders, data)

    # 图5：原始朝代明细（Top 30，不含未知）
    top30_dyns = sorted([d for d in dyn_counter if d != '未知'],
                        key=lambda x: -dyn_counter[x])[:30]
    plot_horizontal_bar(CHART_DIR / 'dynasty_detail_top30.png',
                        '朝代明细 Top 30（原始分类）',
                        top30_dyns, [dyn_counter[d] for d in top30_dyns],
                        figsize=(12, 10))

    # 图6：主朝代性别绝对数量柱状图（分组）
    fig, ax = plt.subplots(figsize=(16, 7), dpi=200)
    x = range(len(main_dyns_china))
    width = 0.25
    male_vals = [main_dyn_gender[d]['男'] for d in main_dyns_china]
    female_vals = [main_dyn_gender[d]['女'] for d in main_dyns_china]
    unknown_vals = [main_dyn_gender[d]['未知'] for d in main_dyns_china]
    ax.bar([i - width for i in x], male_vals, width, label='男', color='#4C78A8')
    ax.bar(x, female_vals, width, label='女', color='#F58518')
    ax.bar([i + width for i in x], unknown_vals, width, label='未知', color='#BAB0AC')
    ax.set_xticks(x)
    ax.set_xticklabels(main_dyns_china, rotation=45, ha='right', fontsize=9)
    ax.set_ylabel('人物数量', fontsize=11)
    ax.set_title('各朝代性别数量对比', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()
    plt.savefig(CHART_DIR / 'gender_by_dynasty_grouped.png', bbox_inches='tight')
    plt.close()

    # ========== 校验摘要 ==========
    summary = {
        'dynasty_total_raw': len(dyns),
        'dynasty_total_main': len(main_dyns),
        'main_dynasty_list': main_dyns_china,
        'top_status': top_status[:5],
        'top_addr_types': top_addr[:5],
        'gender_groups': genders,
        'non_chinese_excluded': list(NON_CHINESE_DYNASTIES),
        'total_persons': len(dyn_map),
    }
    (OUT_DIR / 'analysis_b_summary.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

    print("\n===== B 问分析摘要 =====")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\n输出目录: {OUT_DIR}")
    print(f"图表目录: {CHART_DIR}")
    print("完成！")


if __name__ == '__main__':
    main()
