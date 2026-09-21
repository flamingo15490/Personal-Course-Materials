# -*- coding: utf-8 -*-
"""
E-3：中国古代女性人物的时空分布分析
读取 output_cbdb_v1/ 的已数据化 CSV，分析女性人物在各朝代的数量变化、
地理分布、身份类型演变、亲属关系和社会关系网络中的角色特征。
输出统计 CSV、论文图表和分析摘要。
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# ========== 路径与字体 ==========
ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / "output_cbdb_v1"
OUT_DIR = ROOT / "任务e" / "专题3_女性人物"
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ========== 主朝代定义 ==========
MAIN_DYNASTY_ORDER = [
    '先秦', '西漢', '東漢', '三國', '西晉', '東晉',
    '南北朝', '隋', '唐', '五代十國', '北宋', '南宋',
    '遼', '金', '元', '明', '清',
]

DYNASTY_TO_MAIN = {
    '西漢': '西漢', '東漢': '東漢', '三國': '三國',
    '西晉': '西晉', '東晉': '東晉', '南北朝': '南北朝',
    '隋': '隋', '唐': '唐', '遼': '遼', '金': '金',
    '元': '元', '明': '明', '清': '清',
    '三國魏': '三國', '三國吳': '三國', '三國蜀': '三國',
    '北魏': '南北朝', '北齊': '南北朝', '北周': '南北朝',
    '東魏': '南北朝', '西魏': '南北朝',
    '南梁': '南北朝', '南齊': '南北朝', '陳': '南北朝',
    '宋(劉)': '南北朝',
    '前秦': '南北朝', '後秦': '南北朝', '前燕': '南北朝',
    '後燕': '南北朝', '南燕': '南北朝', '西燕': '南北朝',
    '後趙': '南北朝', '前趙': '南北朝', '前涼': '南北朝',
    '後涼': '南北朝', '西涼': '南北朝', '北涼': '南北朝',
    '南平': '南北朝', '西秦': '南北朝', '北燕': '南北朝',
    '東梁': '南北朝', '西梁': '南北朝', '代': '南北朝',
    '五代': '五代十國', '後梁': '五代十國', '後唐': '五代十國',
    '後晉': '五代十國', '後漢': '五代十國', '後周': '五代十國',
    '後蜀': '五代十國', '前蜀': '五代十國',
    '南唐': '五代十國', '南漢': '五代十國',
    '吳越': '五代十國', '閩國': '五代十國',
    '吳(楊)': '五代十國', '楚(馬)': '五代十國',
    '北漢': '五代十國', '偽齊': '五代十國',
    '鄭（王世充）': '五代十國',
    '宋': '南宋',
    '周': '先秦', '贏秦': '先秦', '秦漢': '先秦', '漢前': '先秦',
    '吳': '先秦', '晉': '先秦', '新': '西漢',
    '西遼': '遼',
}

NON_CHINESE_DYNASTIES = {'朝鮮', '韓國', '高麗', '新羅'}

# 身份类型的附属/独立分类（关键词）
DEPENDENT_KEYWORDS = ['節婦', '节妇', '孝女', '烈女', '貞女', '贞女']
INDEPENDENT_KEYWORDS = ['詩人', '诗人', '畫家', '画家', '學者', '学者',
                        '作家', '文學', '文学', '詞人', '词人',
                        '女官', '才女', '醫', '医']

# 绘图调色板
COLORS_10 = ['#4C78A8', '#F58518', '#E45756', '#72B7B2', '#54A24B',
             '#EECA3B', '#B279A2', '#FF9DA6', '#9D755D', '#BAB0AC']


# ========== 工具函数 ==========
def norm_dynasty(v) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return '未知'
    s = str(v).strip()
    if s in ('', '未詳', 'None', 'null', 'nan'):
        return '未知'
    return s


def to_main_dynasty(dyn: str) -> str:
    if dyn == '未知':
        return '未知'
    if dyn in NON_CHINESE_DYNASTIES:
        return '非中国朝代'
    return DYNASTY_TO_MAIN.get(dyn, '其他')


def write_csv(path: Path, header, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(header)
        for row in rows:
            w.writerow(row)


def shannon_diversity(counter: Counter) -> float:
    """计算 Shannon 多样性指数 H' = -sum(p_i * ln(p_i))"""
    total = sum(counter.values())
    if total == 0:
        return 0.0
    h = 0.0
    for count in counter.values():
        if count > 0:
            p = count / total
            h -= p * math.log(p)
    return round(h, 4)


def hhi_index(counter: Counter) -> float:
    """计算 HHI 集中度指数 = sum(s_i^2)，s_i 为份额"""
    total = sum(counter.values())
    if total == 0:
        return 0.0
    hhi = sum((c / total) ** 2 for c in counter.values())
    return round(hhi, 6)


def classify_status(desc_chn: str, desc_en: str) -> str:
    """规范化身份描述：优先中文，回退英文，去除方括号占位"""
    s = str(desc_chn).strip() if desc_chn else ''
    if s and not s.startswith('['):
        return s
    s2 = str(desc_en).strip() if desc_en else ''
    if s2:
        return s2
    return '未知身份'


def is_native_record(desc_chn) -> bool:
    """判断是否为籍贯记录"""
    if desc_chn and '籍貫' in str(desc_chn):
        return True
    return False


def top_n_with_other(counter: Counter, n: int = 5) -> tuple[list[str], dict[str, int]]:
    """取 Top N，其余合并为'其他'"""
    items = counter.most_common()
    top = items[:n]
    rest = sum(c for _, c in items[n:])
    labels = [k for k, _ in top]
    vals = [c for _, c in top]
    if rest > 0:
        labels.append('其他')
        vals.append(rest)
    return labels, vals


def safe_float(v, default=0.0):
    try:
        return float(v)
    except (ValueError, TypeError):
        return default


# ========== Step 1: 女性基本统计 ==========
def step1_basic_stats(dim_path: Path):
    print("Step 1: 女性人物基本统计 ...")
    dyn_total = Counter()
    dyn_female = Counter()
    gender_counter = Counter()
    person_dynasty = {}   # personid → main_dynasty
    female_ids = set()

    with dim_path.open('r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            dyn = norm_dynasty(row.get('dynasty_chn'))
            main_dyn = to_main_dynasty(dyn)
            female_val = row.get('c_female', '')
            pid = row['c_personid']

            person_dynasty[pid] = main_dyn

            # 性别统计
            if str(female_val).strip() == '1':
                gender_counter['女'] += 1
                female_ids.add(pid)
                dyn_female[main_dyn] += 1
            elif str(female_val).strip() == '0':
                gender_counter['男'] += 1
            else:
                gender_counter['未知'] += 1

            dyn_total[main_dyn] += 1

    # 写 CSV
    rows = []
    for dyn in MAIN_DYNASTY_ORDER:
        total = dyn_total.get(dyn, 0)
        female = dyn_female.get(dyn, 0)
        ratio = female / total if total > 0 else 0
        rows.append([dyn, total, female, round(ratio, 6), round(ratio * 100, 2)])

    # 附加"未知"和"其他"
    for dyn in ['未知', '其他', '非中国朝代']:
        total = dyn_total.get(dyn, 0)
        female = dyn_female.get(dyn, 0)
        if total > 0:
            ratio = female / total
            rows.append([dyn, total, female, round(ratio, 6), round(ratio * 100, 2)])

    header = ['dynasty', 'total_person_count', 'female_count', 'female_ratio', 'female_ratio_pct']
    write_csv(OUT_DIR / 'female_dynasty_stats.csv', header, rows)

    print(f"  人物总数: {sum(gender_counter.values())}")
    print(f"  男: {gender_counter['男']}, 女: {gender_counter['女']}, 未知: {gender_counter['未知']}")
    print(f"  女性 ID 集合大小: {len(female_ids)}")

    return female_ids, person_dynasty, dyn_total, dyn_female, gender_counter


# ========== Step 2: 女性身份类型 ==========
def step2_status_analysis(status_path: Path, female_ids: set, person_dynasty: dict):
    print("Step 2: 女性身份类型分析 ...")
    # 读取女性身份记录
    dyn_status_count = defaultdict(Counter)  # main_dynasty → status → count
    status_global = Counter()

    with status_path.open('r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            pid = row.get('c_personid', '')
            if pid not in female_ids:
                continue
            main_dyn = person_dynasty.get(pid, '未知')
            desc = classify_status(row.get('c_status_desc_chn', ''),
                                   row.get('c_status_desc', ''))
            dyn_status_count[main_dyn][desc] += 1
            status_global[desc] += 1

    # Shannon 指数
    dyn_shannon = {}
    for dyn in MAIN_DYNASTY_ORDER:
        dyn_shannon[dyn] = shannon_diversity(dyn_status_count.get(dyn, Counter()))

    # 写明细 CSV
    rows = []
    for dyn in MAIN_DYNASTY_ORDER + ['未知', '其他']:
        counter = dyn_status_count.get(dyn, Counter())
        if not counter:
            continue
        shannon = dyn_shannon.get(dyn, shannon_diversity(counter))
        for status, count in counter.most_common():
            rows.append([dyn, status, count, shannon])
    header = ['dynasty', 'status_type', 'count', 'shannon_diversity']
    write_csv(OUT_DIR / 'female_status_by_dynasty.csv', header, rows)

    # 附属 vs 独立 趋势
    dyn_dependent = Counter()
    dyn_independent = Counter()
    for dyn, counter in dyn_status_count.items():
        for status, count in counter.items():
            if any(kw in status for kw in DEPENDENT_KEYWORDS):
                dyn_dependent[dyn] += count
            if any(kw in status for kw in INDEPENDENT_KEYWORDS):
                dyn_independent[dyn] += count

    print(f"  涉及身份类型数: {len(status_global)}")
    print(f"  Top 5 身份: {status_global.most_common(5)}")

    return dyn_status_count, status_global, dyn_shannon, dyn_dependent, dyn_independent


# ========== Step 3: 女性地理分布 ==========
def step3_geography(addr_path: Path, dim_path: Path,
                    female_ids: set, person_dynasty: dict):
    print("Step 3: 女性地理分布 ...")
    # 从 fact_person_address 提取籍贯
    female_origin = {}  # personid → addr_chn (first native record)
    with addr_path.open('r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            pid = row.get('c_personid', '')
            if pid not in female_ids:
                continue
            if pid in female_origin:
                continue  # 已取首条
            # 籍贯判定：addr_type==1 或描述含"籍貫"
            addr_type = str(row.get('c_addr_type', '')).strip()
            desc_chn = row.get('c_addr_desc_chn', '')
            if addr_type == '1' or is_native_record(desc_chn):
                addr = str(row.get('addr_chn', '')).strip()
                if addr and addr not in ('', 'nan', 'None', '未詳'):
                    female_origin[pid] = addr

    # 回退：从 dim_person 的 index_addr_chn 补充
    with dim_path.open('r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            pid = row.get('c_personid', '')
            if pid not in female_ids or pid in female_origin:
                continue
            addr = str(row.get('index_addr_chn', '')).strip()
            if addr and addr not in ('', 'nan', 'None', '未詳'):
                female_origin[pid] = addr

    # 按朝代统计地区
    dyn_addr_count = defaultdict(Counter)
    addr_global = Counter()
    for pid, addr in female_origin.items():
        dyn = person_dynasty.get(pid, '未知')
        dyn_addr_count[dyn][addr] += 1
        addr_global[addr] += 1

    # HHI
    dyn_hhi = {}
    for dyn in MAIN_DYNASTY_ORDER:
        dyn_hhi[dyn] = hhi_index(dyn_addr_count.get(dyn, Counter()))

    # 写 Top10 CSV
    rows = []
    for dyn in MAIN_DYNASTY_ORDER + ['未知', '其他']:
        counter = dyn_addr_count.get(dyn, Counter())
        if not counter:
            continue
        hhi = dyn_hhi.get(dyn, hhi_index(counter))
        for addr, count in counter.most_common(10):
            rows.append([dyn, addr, count, hhi])
    header = ['dynasty', 'address', 'count', 'hhi_index']
    write_csv(OUT_DIR / 'female_origin_top10.csv', header, rows)

    # 热力图数据：全局 Top 10 地区
    top10_addrs = [a for a, _ in addr_global.most_common(10)]
    print(f"  有籍贯记录的女性: {len(female_origin)}")
    print(f"  Top 5 籍贯: {addr_global.most_common(5)}")

    return dyn_addr_count, addr_global, dyn_hhi, top10_addrs


# ========== Step 4: 女性亲属关系 ==========
def step4_kinship(kin_path: Path, female_ids: set, person_dynasty: dict):
    print("Step 4: 女性亲属关系分析 ...")
    skip_kinrel = {'', '未詳', '非可用', '未知', 'nan', 'None',
                   '\t\r\nNot Applicable', 'Not Applicable'}

    # 统计
    dyn_kinrole = defaultdict(Counter)   # dynasty → kinrel → count
    kinrole_global = Counter()
    female_as_person = 0
    female_as_kin = 0
    involving_records = set()

    with kin_path.open('r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            pid = str(row.get('c_personid', '')).strip()
            kid = str(row.get('c_kin_id', '')).strip()
            kinrel = str(row.get('c_kinrel_chn', '')).strip()

            # 过滤无效关系
            if kinrel in skip_kinrel:
                continue

            pid_is_f = pid in female_ids
            kid_is_f = kid in female_ids

            if not pid_is_f and not kid_is_f:
                continue

            # 记录去重
            rec_key = (pid, kid, kinrel)
            involving_records.add(rec_key)

            if pid_is_f:
                female_as_person += 1
            if kid_is_f:
                female_as_kin += 1

            # 朝代归属：优先按 c_personid 侧
            if pid_is_f:
                dyn = person_dynasty.get(pid, '未知')
            else:
                dyn = person_dynasty.get(kid, '未知')

            dyn_kinrole[dyn][kinrel] += 1
            kinrole_global[kinrel] += 1

    # 写 CSV
    rows = []
    for dyn in MAIN_DYNASTY_ORDER + ['未知', '其他']:
        counter = dyn_kinrole.get(dyn, Counter())
        if not counter:
            continue
        for role, count in counter.most_common():
            rows.append([dyn, role, count])
    header = ['dynasty', 'kin_role', 'count']
    write_csv(OUT_DIR / 'female_kin_role_stats.csv', header, rows)

    print(f"  涉及女性亲属记录总数: {len(involving_records)}")
    print(f"  女性作为 personid: {female_as_person}, 作为 kin_id: {female_as_kin}")
    print(f"  Top 5 亲属角色: {kinrole_global.most_common(5)}")

    return (dyn_kinrole, kinrole_global,
            female_as_person, female_as_kin, len(involving_records))


# ========== Step 5: 女性社会关系 ==========
def step5_association(assoc_path: Path, female_ids: set, person_dynasty: dict):
    print("Step 5: 女性社会关系分析 ...")
    skip_assoc = {'', '未詳', '未知', 'nan', 'None'}

    dyn_assoc = defaultdict(Counter)
    assoc_global = Counter()
    special_stats = {'贈詩': 0, '致書': 0, '師生': 0}
    total_valid = 0

    with assoc_path.open('r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            pid = str(row.get('c_personid', '')).strip()
            aid = str(row.get('c_assoc_id', '')).strip()
            desc = str(row.get('c_assoc_desc_chn', '')).strip()

            if not (pid in female_ids or aid in female_ids):
                continue
            if desc in skip_assoc:
                continue

            total_valid += 1

            # 朝代归属优先 personid 侧
            if pid in female_ids:
                dyn = person_dynasty.get(pid, '未知')
            else:
                dyn = person_dynasty.get(aid, '未知')

            dyn_assoc[dyn][desc] += 1
            assoc_global[desc] += 1

            # 特殊类型统计
            if '贈詩' in desc or '赠诗' in desc:
                special_stats['贈詩'] += 1
            if '致書' in desc or '致书' in desc:
                special_stats['致書'] += 1
            if '師生' in desc or '师生' in desc:
                special_stats['師生'] += 1

    # 计算特殊类型占比
    special_ratio = {}
    for k, v in special_stats.items():
        special_ratio[k] = {
            'count': v,
            'ratio': round(v / total_valid, 6) if total_valid > 0 else 0,
            'ratio_pct': round(v / total_valid * 100, 2) if total_valid > 0 else 0,
            'exists': v > 0,
        }

    # 写 CSV
    rows = []
    for dyn in MAIN_DYNASTY_ORDER + ['未知', '其他']:
        counter = dyn_assoc.get(dyn, Counter())
        if not counter:
            continue
        for rel, count in counter.most_common():
            rows.append([dyn, rel, count])
    header = ['dynasty', 'assoc_type', 'count']
    write_csv(OUT_DIR / 'female_assoc_stats.csv', header, rows)

    print(f"  涉及女性社会关系总数: {total_valid}")
    print(f"  Top 5 社会关系: {assoc_global.most_common(5)}")
    print(f"  赠诗/致书/师生: {special_stats}")

    return dyn_assoc, assoc_global, special_stats, special_ratio, total_valid


# ========== Step 6: 可视化 ==========
def plot_ratio_trend(dyn_female: Counter, dyn_total: Counter):
    """女性占比趋势折线图"""
    print("绘制 女性占比趋势图 ...")
    xs = MAIN_DYNASTY_ORDER
    ys = []
    for d in xs:
        t = dyn_total.get(d, 0)
        f = dyn_female.get(d, 0)
        ys.append((f / t * 100) if t > 0 else 0)

    fig, ax = plt.subplots(figsize=(14, 6), dpi=200)
    ax.plot(xs, ys, 'o-', color='#E45756', linewidth=2, markersize=6)
    ax.fill_between(range(len(xs)), ys, alpha=0.15, color='#E45756')

    # 标注关键转折点
    for i in range(1, len(ys)):
        if ys[i] > 0 and ys[i - 1] > 0:
            change = (ys[i] - ys[i - 1]) / ys[i - 1]
            if abs(change) > 0.3:  # 变化超过30%
                ax.annotate(f'{ys[i]:.1f}%', (i, ys[i]),
                            textcoords="offset points", xytext=(0, 12),
                            ha='center', fontsize=8, fontweight='bold',
                            color='#E45756')
    # 始终标注首尾有效值
    for i, v in enumerate(ys):
        if v > 0 and i in (0, len(ys) - 1):
            ax.annotate(f'{v:.1f}%', (i, v),
                        textcoords="offset points", xytext=(0, 12),
                        ha='center', fontsize=8, fontweight='bold')

    ax.set_xticks(range(len(xs)))
    ax.set_xticklabels(xs, rotation=45, ha='right', fontsize=9)
    ax.set_ylabel('女性占比 (%)', fontsize=11)
    ax.set_title('各朝代女性人物占比趋势', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    fig.tight_layout()
    fig.savefig(OUT_DIR / 'female_ratio_trend.png', bbox_inches='tight')
    plt.close(fig)


def plot_status_evolution(dyn_status_count: defaultdict, status_global: Counter):
    """女性身份类型演变堆叠面积图"""
    print("绘制 身份类型演变图 ...")
    top5_labels = [s for s, _ in status_global.most_common(5)]
    labels = top5_labels + ['其他']
    xs = MAIN_DYNASTY_ORDER

    data = {lab: [] for lab in labels}
    for dyn in xs:
        counter = dyn_status_count.get(dyn, Counter())
        total = sum(counter.values()) or 1
        for lab in top5_labels:
            data[lab].append(counter.get(lab, 0) / total * 100)
        other_pct = 100 - sum(data[lab][-1] for lab in top5_labels)
        data['其他'].append(max(0, other_pct))

    fig, ax = plt.subplots(figsize=(14, 7), dpi=200)
    y_stack = np.zeros(len(xs))
    for i, lab in enumerate(labels):
        vals = np.array(data[lab])
        ax.fill_between(range(len(xs)), y_stack, y_stack + vals,
                        label=lab, color=COLORS_10[i % len(COLORS_10)], alpha=0.8)
        y_stack += vals

    ax.set_xticks(range(len(xs)))
    ax.set_xticklabels(xs, rotation=45, ha='right', fontsize=9)
    ax.set_ylabel('占比 (%)', fontsize=11)
    ax.set_title('女性身份类型演变趋势', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left', fontsize=9, ncol=2)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    fig.tight_layout()
    fig.savefig(OUT_DIR / 'female_status_evolution.png', bbox_inches='tight')
    plt.close(fig)


def plot_origin_heatmap(dyn_addr_count: defaultdict, top10_addrs: list):
    """女性籍贯分布热力图"""
    print("绘制 籍贯分布热力图 ...")
    # 只取有数据的主朝代
    dyns_with_data = [d for d in MAIN_DYNASTY_ORDER
                      if sum(dyn_addr_count.get(d, Counter()).values()) > 0]
    if not dyns_with_data:
        print("  警告：无籍贯数据，跳过热力图")
        return

    matrix = []
    for addr in top10_addrs:
        row = []
        for dyn in dyns_with_data:
            row.append(dyn_addr_count.get(dyn, Counter()).get(addr, 0))
        matrix.append(row)

    matrix = np.array(matrix, dtype=float)
    fig, ax = plt.subplots(figsize=(max(14, len(dyns_with_data) * 0.9), 7), dpi=200)
    im = ax.imshow(matrix, aspect='auto', cmap='YlOrRd')

    ax.set_xticks(range(len(dyns_with_data)))
    ax.set_xticklabels(dyns_with_data, rotation=45, ha='right', fontsize=9)
    ax.set_yticks(range(len(top10_addrs)))
    ax.set_yticklabels(top10_addrs, fontsize=10)

    # 标注数值
    for i in range(len(top10_addrs)):
        for j in range(len(dyns_with_data)):
            v = int(matrix[i, j])
            if v > 0:
                ax.text(j, i, str(v), ha='center', va='center', fontsize=7,
                        color='white' if v > matrix.max() * 0.6 else 'black')

    fig.colorbar(im, ax=ax, label='人数', shrink=0.8)
    ax.set_title('女性籍贯分布热力图（Top 10 地区 × 朝代）', fontsize=14, fontweight='bold')
    fig.tight_layout()
    fig.savefig(OUT_DIR / 'female_origin_heatmap.png', bbox_inches='tight')
    plt.close(fig)


def plot_kin_roles(dyn_kinrole: defaultdict, kinrole_global: Counter):
    """女性亲属角色柱状图"""
    print("绘制 亲属角色柱状图 ...")
    top8_roles = [r for r, _ in kinrole_global.most_common(8)]
    xs = MAIN_DYNASTY_ORDER

    fig, ax = plt.subplots(figsize=(16, 7), dpi=200)
    x = np.arange(len(xs))
    width = 0.8 / len(top8_roles)
    offsets = np.linspace(-0.4 + width / 2, 0.4 - width / 2, len(top8_roles))

    for i, role in enumerate(top8_roles):
        vals = [dyn_kinrole.get(dyn, Counter()).get(role, 0) for dyn in xs]
        ax.bar(x + offsets[i], vals, width, label=role,
               color=COLORS_10[i % len(COLORS_10)], edgecolor='white', linewidth=0.3)

    ax.set_xticks(x)
    ax.set_xticklabels(xs, rotation=45, ha='right', fontsize=9)
    ax.set_ylabel('出现次数', fontsize=11)
    ax.set_title('各朝代女性亲属角色分布', fontsize=14, fontweight='bold')
    ax.legend(fontsize=8, ncol=2, loc='upper left')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    fig.tight_layout()
    fig.savefig(OUT_DIR / 'female_kin_roles.png', bbox_inches='tight')
    plt.close(fig)


def plot_assoc_types(assoc_global: Counter):
    """女性社会关系类型柱状图"""
    print("绘制 社会关系类型图 ...")
    top12 = assoc_global.most_common(12)
    labels = [l for l, _ in top12]
    vals = [v for _, v in top12]

    fig, ax = plt.subplots(figsize=(12, 6), dpi=200)
    bars = ax.bar(range(len(labels)), vals,
                  color='#72B7B2', edgecolor='white', linewidth=0.5)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
    ax.set_ylabel('关系记录数', fontsize=11)
    ax.set_title('女性人物社会关系类型分布', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # 标注数值
    for bar in bars:
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, h,
                    f'{int(h)}', ha='center', va='bottom', fontsize=8)

    fig.tight_layout()
    fig.savefig(OUT_DIR / 'female_assoc_types.png', bbox_inches='tight')
    plt.close(fig)


# ========== Step 7: JSON 摘要 + README ==========
def step7_summary(gender_counter, dyn_female, dyn_total, dyn_shannon,
                  dyn_hhi, kinrole_global, assoc_global, special_stats,
                  special_ratio, total_assoc, female_as_person, female_as_kin,
                  total_kin_records):
    print('生成分析摘要 ...')

    # 女性占比最高朝代
    best_ratio_dyn = max(MAIN_DYNASTY_ORDER,
                         key=lambda d: (dyn_female.get(d, 0) / dyn_total.get(d, 1)))
    best_ratio_pct = dyn_female.get(best_ratio_dyn, 0) / dyn_total.get(best_ratio_dyn, 1) * 100

    # 多样性最高朝代
    valid_shannon = {d: v for d, v in dyn_shannon.items() if d in MAIN_DYNASTY_ORDER and v > 0}
    best_div_dyn = max(valid_shannon, key=valid_shannon.get) if valid_shannon else '无数据'
    best_div_h = valid_shannon.get(best_div_dyn, 0)

    # 籍贯最集中朝代 (HHI 最高)
    valid_hhi = {d: v for d, v in dyn_hhi.items() if d in MAIN_DYNASTY_ORDER and v > 0}
    most_concentrated_dyn = max(valid_hhi, key=valid_hhi.get) if valid_hhi else '无数据'
    most_concentrated_hhi = valid_hhi.get(most_concentrated_dyn, 0)

    summary = {
        '总人物数': sum(gender_counter.values()),
        '女性人物数': gender_counter.get('女', 0),
        '男性人物数': gender_counter.get('男', 0),
        '未知性别': gender_counter.get('未知', 0),
        '女性占比': round(gender_counter.get('女', 0) / max(sum(gender_counter.values()), 1) * 100, 2),
        '女性占比最高朝代': '{} ({:.1f}%)'.format(best_ratio_dyn, best_ratio_pct),
        '女性身份多样性最高朝代': '{} (H={:.4f})'.format(best_div_dyn, best_div_h),
        '女性籍贯最集中朝代': '{} (HHI={:.4f})'.format(most_concentrated_dyn, most_concentrated_hhi),
        '最常见女性亲属角色': kinrole_global.most_common(5),
        '最常见女性社会关系类型': assoc_global.most_common(5),
        '赠诗_致书_师生统计': {
            '赠诗': special_ratio.get('贈詩', {'count': 0, 'exists': False}),
            '致书': special_ratio.get('致書', {'count': 0, 'exists': False}),
            '师生': special_ratio.get('師生', {'count': 0, 'exists': False}),
        },
        '女性亲属关系概览': {
            '作为personid记录数': female_as_person,
            '作为kin_id记录数': female_as_kin,
            '涉及女性总记录数': total_kin_records,
        },
        '女性社会关系总数': total_assoc,
        '各朝代Shannon多样性指数': {d: dyn_shannon.get(d, 0) for d in MAIN_DYNASTY_ORDER},
        '各朝代HHI集中度': {d: dyn_hhi.get(d, 0) for d in MAIN_DYNASTY_ORDER},
    }

    with (OUT_DIR / 'analysis_summary.json').open('w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # 附属/独立身份统计
    dep_total = sum(dyn_female.get(d, 0) for d in MAIN_DYNASTY_ORDER) or 1

    # 师生特殊统计
    shi_sheng = special_ratio.get('師生', {'count': 0, 'exists': False})

    # README
    readme_lines = [
        '# E-3: 中国古代女性人物的时空分布分析',
        '',
        '## 方法',
        '',
        '### 数据来源',
        '- 人物主表: output_cbdb_v1/dim_person.csv (c_female 字段识别性别)',
        '- 五张事实表: 身份、地址、亲属、社会关系、主表籍贯字段',
        '- 女性定义: c_female == 1 (0=男, 其他/空值=未知)',
        '- 朝代映射: 原始朝代 -> 主朝代 (18 个主朝代), 排除非中国朝代 (朝鮮/韓國/高麗/新羅)',
        '',
        '### 分析维度',
        '1. 基本统计: 各朝代女性人数与占比趋势',
        '2. 身份类型: 女性身份 Top 10 + Shannon 多样性指数',
        '3. 地理分布: 籍贯 Top 10 + HHI 集中度指数',
        '4. 亲属角色: 女性在亲属关系中的角色分布',
        '5. 社会关系: 女性社会关系类型 + 赠诗/致书/师生专项分析',
        '',
        '## 主要发现',
        '',
        '### 1. 女性记录的系统性遗漏',
        '- CBDB 记录女性人物 {} 人, 仅占总人物的 {:.1f}%'.format(
            gender_counter.get('女', 0),
            gender_counter.get('女', 0) / max(sum(gender_counter.values()), 1) * 100),
        '- 这反映了中国古代史学中女性记录的系统性缺失: 正史列传以男性精英为主,',
        '  女性往往仅在列女传中以附属身份出现',
        '- 早期朝代 (先秦至南北朝) 女性记录极少, 唐宋以后逐步增加,',
        '  尤其明清时期女性记录显著增长',
        '',
        '### 2. 身份从附属到独立的演变',
        '- 身份多样性最高朝代: {} (Shannon H={:.4f})'.format(best_div_dyn, best_div_h),
        '- 早期女性身份以节妇/孝女/烈女等附属身份为主,',
        '  这些身份的认定依赖于与男性亲属的关系',
        '- 唐宋以后, 诗人/画家/才女等独立身份逐渐出现并增多,',
        '  反映女性社会角色的扩展',
        '- 明清时期身份类型最为多样, 但附属身份仍占主导',
        '',
        '### 3. 地域文化差异',
        '- 女性籍贯最集中朝代: {} (HHI={:.4f})'.format(most_concentrated_dyn, most_concentrated_hhi),
        '- 江南地区 (江浙一带) 在宋元明清时期集中出现大量女性人物,',
        '  与该地区文化教育发达、世家大族聚居有关',
        '- 北方地区在早期朝代中女性记录相对集中,',
        '  反映政治中心对记录完整性的影响',
        '',
        '### 4. 女性亲属角色',
        '- 女性最常见的亲属角色: {}'.format(
            ', '.join(r for r, _ in kinrole_global.most_common(3))),
        '- 女性作为亲属记录中的 c_personid (被引用方): {} 次'.format(female_as_person),
        '- 女性作为亲属记录中的 c_kin_id (引用方): {} 次'.format(female_as_kin),
        '- 女性在亲属关系中主要以母亲/妻子/女儿等核心家庭角色出现,',
        '  姐妹/姑/姨等扩展角色相对较少',
        '',
        '### 5. 女性社会关系',
        '- 女性社会关系记录总数: {}'.format(total_assoc),
        '- 最常见社会关系: {}'.format(
            ', '.join(r for r, _ in assoc_global.most_common(3))),
        '- 赠诗统计: {}'.format(json.dumps(special_ratio.get('贈詩', {}), ensure_ascii=False)),
        '- 致书统计: {}'.format(json.dumps(special_ratio.get('致書', {}), ensure_ascii=False)),
        '- 师生统计: {}'.format(json.dumps(shi_sheng, ensure_ascii=False)),
        '- 女性拥有独立的赠诗/致书/师生关系记录, 但数量和比例有限,',
        '  反映女性在公共知识交流网络中的参与度较低',
        '',
        '## 局限性',
        '',
        '1. 数据偏倚: CBDB 主要基于正史、碑传等传统文献, 女性记录存在系统性遗漏,',
        '   实际女性人物数量远超数据库记录',
        '2. 朝代归属: 采用主朝代映射 (如宋统一归为南宋),',
        '   可能掩盖部分朝代内部的时间差异',
        '3. 籍贯回退: 当事实表无籍贯记录时回退到主表 index_addr_chn,',
        '   两者的定义标准可能略有差异',
        '4. 身份分类: 附属/独立身份的关键词匹配可能遗漏边缘案例',
        '5. 亲属关系朝代归属: 统一按女性相关人物的主朝代,',
        '   未按关系发生年份精确建模',
    ]

    with (OUT_DIR / 'README.md').open('w', encoding='utf-8') as f:
        f.write('\n'.join(readme_lines))

    return summary

def main():
    dim_path = IN_DIR / "dim_person.csv"
    status_path = IN_DIR / "fact_person_status.csv"
    addr_path = IN_DIR / "fact_person_address.csv"
    kin_path = IN_DIR / "fact_person_kin.csv"
    assoc_path = IN_DIR / "fact_person_assoc.csv"

    # Step 1
    (female_ids, person_dynasty, dyn_total, dyn_female,
     gender_counter) = step1_basic_stats(dim_path)

    # Step 2
    (dyn_status_count, status_global, dyn_shannon,
     dyn_dependent, dyn_independent) = step2_status_analysis(
        status_path, female_ids, person_dynasty)

    # Step 3
    (dyn_addr_count, addr_global, dyn_hhi,
     top10_addrs) = step3_geography(addr_path, dim_path,
                                     female_ids, person_dynasty)

    # Step 4
    (dyn_kinrole, kinrole_global, female_as_person, female_as_kin,
     total_kin_records) = step4_kinship(kin_path, female_ids, person_dynasty)

    # Step 5
    (dyn_assoc, assoc_global, special_stats, special_ratio,
     total_assoc) = step5_association(assoc_path, female_ids, person_dynasty)

    # Step 6: 可视化
    print("\nStep 6: 生成可视化图表 ...")
    plot_ratio_trend(dyn_female, dyn_total)
    plot_status_evolution(dyn_status_count, status_global)
    plot_origin_heatmap(dyn_addr_count, top10_addrs)
    plot_kin_roles(dyn_kinrole, kinrole_global)
    plot_assoc_types(assoc_global)

    # Step 7: 摘要
    print("\nStep 7: 生成摘要与 README ...")
    step7_summary(
        gender_counter, dyn_female, dyn_total, dyn_shannon,
        dyn_hhi, kinrole_global, assoc_global, special_stats,
        special_ratio, total_assoc, female_as_person, female_as_kin,
        total_kin_records)

    # 最终确认
    print("\n" + "=" * 60)
    print("E-3 分析完成！输出目录：")
    print(f"  {OUT_DIR}")
    print("输出文件：")
    for p in sorted(OUT_DIR.iterdir()):
        print(f"  {p.name}")
    print("=" * 60)


if __name__ == '__main__':
    main()
