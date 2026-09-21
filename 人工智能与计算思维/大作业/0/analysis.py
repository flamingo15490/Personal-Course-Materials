# -*- coding: utf-8 -*-
"""
北京大学讣告数据分析与可视化
"""
import json
import os
import sys
import re
from collections import Counter, defaultdict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

# Configure Chinese font
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'KaiTi', 'FangSong']
plt.rcParams['axes.unicode_minus'] = False

INPUT_FILE = r'D:\虚拟C盘\study\0\obituaries_structured.json'
CHARTS_DIR = r'D:\虚拟C盘\study\0\charts'

def load_data():
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def filter_valid(records, field):
    return [r for r in records if r.get(field)]

def chart_age_distribution(records):
    """享年岁数分布"""
    ages = [r['age'] for r in records if r.get('age') and 20 <= r['age'] <= 120]
    if not ages:
        return None

    fig, ax = plt.subplots(figsize=(10, 6))
    bins = range(min(ages), max(ages) + 5, 5)
    ax.hist(ages, bins=bins, color='#c0392b', edgecolor='white', alpha=0.85)
    ax.set_xlabel('享年（岁）', fontsize=13)
    ax.set_ylabel('人数', fontsize=13)
    ax.set_title('北京大学讣告 — 享年岁数分布', fontsize=16, fontweight='bold')

    mean_age = np.mean(ages)
    median_age = np.median(ages)
    ax.axvline(mean_age, color='#2c3e50', linestyle='--', linewidth=1.5, label=f'均值: {mean_age:.1f}')
    ax.axvline(median_age, color='#e67e22', linestyle='--', linewidth=1.5, label=f'中位数: {median_age:.1f}')
    ax.legend(fontsize=11)
    ax.text(0.02, 0.95, f'样本量: {len(ages)}\n均值: {mean_age:.1f}岁\n中位数: {median_age:.1f}岁\n最小: {min(ages)}岁\n最大: {max(ages)}岁',
            transform=ax.transAxes, fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, 'age_distribution.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path

def chart_role_distribution(records):
    """职称分布"""
    roles = [r['role'] for r in records if r.get('role')]
    # Consolidate roles
    role_map = {
        '教授': '教授', '资深教授': '教授', '研究员': '教授',
        '副教授': '副教授', '副研究员': '副教授',
        '讲师': '讲师', '助理研究员': '讲师', '实验师': '讲师', '工程师': '讲师',
        '高级工程师': '教授', '高级实验师': '教授',
        '院士': '院士',
        '先生': '先生', '同志': '同志', '老师': '老师',
    }
    consolidated = []
    for r in roles:
        consolidated.append(role_map.get(r, r))
    counter = Counter(consolidated)

    # Order by count
    labels = ['教授', '副教授', '讲师', '老师', '同志', '先生', '院士']
    sizes = [counter.get(l, 0) for l in labels]
    # Add any others
    for k, v in counter.items():
        if k not in labels and v > 0:
            labels.append(k)
            sizes.append(v)

    colors = ['#c0392b', '#e74c3c', '#f39c12', '#3498db', '#2ecc71', '#9b59b6', '#1abc9c', '#95a5a6', '#34495e']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Bar chart
    bars = ax1.barh(labels[::-1], sizes[::-1], color=colors[:len(labels)][::-1], edgecolor='white')
    ax1.set_xlabel('人数', fontsize=12)
    ax1.set_title('职称/身份分布', fontsize=14, fontweight='bold')
    for bar, val in zip(bars, sizes[::-1]):
        ax1.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2, str(val),
                va='center', fontsize=10)

    # Pie chart (top 6 + others)
    top_n = 6
    pie_labels = labels[:top_n]
    pie_sizes = sizes[:top_n]
    if len(labels) > top_n:
        pie_labels.append('其他')
        pie_sizes.append(sum(sizes[top_n:]))

    # Filter out zero values
    filtered = [(l, s) for l, s in zip(pie_labels, pie_sizes) if s > 0]
    if filtered:
        pie_labels, pie_sizes = zip(*filtered)
        ax2.pie(pie_sizes, labels=pie_labels, autopct='%1.1f%%', colors=colors[:len(pie_labels)],
                startangle=90, textprops={'fontsize': 10})
        ax2.set_title('职称/身份占比', fontsize=14, fontweight='bold')

    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, 'role_distribution.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path

def chart_department_distribution(records):
    """院系分布 Top 15"""
    depts = [r['department'].replace('北京大学', '') for r in records if r.get('department')]
    counter = Counter(depts)
    top15 = counter.most_common(15)

    fig, ax = plt.subplots(figsize=(12, 7))
    labels = [d[0] for d in top15][::-1]
    values = [d[1] for d in top15][::-1]
    colors = plt.cm.Reds(np.linspace(0.3, 0.9, len(labels)))
    ax.barh(labels, values, color=colors, edgecolor='white')
    ax.set_xlabel('讣告数量', fontsize=12)
    ax.set_title('北京大学讣告 — 院系分布 Top 15', fontsize=16, fontweight='bold')
    for i, v in enumerate(values):
        ax.text(v + 1, i, str(v), va='center', fontsize=10)
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, 'department_distribution.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path

def chart_province_distribution(records):
    """籍贯省份分布"""
    provinces = [r['province'] for r in records if r.get('province')]
    counter = Counter(provinces)
    top15 = counter.most_common(15)

    fig, ax = plt.subplots(figsize=(12, 7))
    labels = [d[0] for d in top15][::-1]
    values = [d[1] for d in top15][::-1]
    colors = plt.cm.Blues(np.linspace(0.3, 0.9, len(labels)))
    ax.barh(labels, values, color=colors, edgecolor='white')
    ax.set_xlabel('人数', fontsize=12)
    ax.set_title('北京大学讣告 — 籍贯省份分布 Top 15', fontsize=16, fontweight='bold')
    for i, v in enumerate(values):
        ax.text(v + 0.5, i, str(v), va='center', fontsize=10)
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, 'province_distribution.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path

def chart_school_distribution(records):
    """本科院校分布 Top 15"""
    schools = [r['undergraduate_school'] for r in records if r.get('undergraduate_school')]
    # Normalize
    normalized = []
    for s in schools:
        s = s.strip()
        if '北京' in s and '大学' in s:
            s = '北京大学'
        elif '清华' in s:
            s = '清华大学'
        elif '复旦' in s:
            s = '复旦大学'
        elif '南开' in s:
            s = '南开大学'
        elif '武汉' in s and '大学' in s:
            s = '武汉大学'
        elif '南京' in s and '大学' in s:
            s = '南京大学'
        elif '中山' in s:
            s = '中山大学'
        elif '人民大学' in s or '人大' in s:
            s = '中国人民大学'
        normalized.append(s)
    counter = Counter(normalized)
    top15 = counter.most_common(15)

    fig, ax = plt.subplots(figsize=(12, 7))
    labels = [d[0] for d in top15][::-1]
    values = [d[1] for d in top15][::-1]
    colors = plt.cm.Greens(np.linspace(0.3, 0.9, len(labels)))
    ax.barh(labels, values, color=colors, edgecolor='white')
    ax.set_xlabel('人数', fontsize=12)
    ax.set_title('北京大学讣告 — 本科就读院校分布 Top 15', fontsize=16, fontweight='bold')
    for i, v in enumerate(values):
        ax.text(v + 0.3, i, str(v), va='center', fontsize=10)
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, 'school_distribution.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path

def chart_timeline(records):
    """按年份统计讣告数量"""
    years = []
    for r in records:
        dd = r.get('death_date', '')
        if dd and len(dd) >= 4:
            try:
                y = int(dd[:4])
                if 2010 <= y <= 2026:
                    years.append(y)
            except:
                pass

    if not years:
        return None

    counter = Counter(years)
    all_years = range(min(counter.keys()), max(counter.keys()) + 1)
    values = [counter.get(y, 0) for y in all_years]

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(list(all_years), values, 'o-', color='#c0392b', linewidth=2, markersize=6)
    ax.fill_between(list(all_years), values, alpha=0.15, color='#c0392b')
    ax.set_xlabel('年份', fontsize=12)
    ax.set_ylabel('讣告数量', fontsize=12)
    ax.set_title('北京大学讣告 — 年度趋势', fontsize=16, fontweight='bold')
    ax.set_xticks(list(all_years))
    ax.set_xticklabels([str(y) for y in all_years], rotation=45)
    for x, y in zip(all_years, values):
        if y > 0:
            ax.annotate(str(y), (x, y), textcoords="offset points", xytext=(0, 8), ha='center', fontsize=9)
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, 'timeline.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path

def chart_age_by_year(records):
    """各年份平均享年岁数变化趋势"""
    year_ages = defaultdict(list)
    for r in records:
        dd = r.get('death_date', '')
        age = r.get('age')
        if dd and age and 20 <= age <= 120:
            try:
                y = int(dd[:4])
                if 2010 <= y <= 2026:
                    year_ages[y].append(age)
            except:
                pass

    if not year_ages:
        return None

    all_years = sorted(year_ages.keys())
    avg_ages = [np.mean(year_ages[y]) for y in all_years]

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(all_years, avg_ages, 's-', color='#2980b9', linewidth=2, markersize=6)
    ax.fill_between(all_years, avg_ages, alpha=0.15, color='#2980b9')
    ax.set_xlabel('年份', fontsize=12)
    ax.set_ylabel('平均享年（岁）', fontsize=12)
    ax.set_title('北京大学讣告 — 各年份平均享年岁数趋势', fontsize=16, fontweight='bold')
    ax.set_xticks(all_years)
    ax.set_xticklabels([str(y) for y in all_years], rotation=45)
    for x, y in zip(all_years, avg_ages):
        ax.annotate(f'{y:.1f}', (x, y), textcoords="offset points", xytext=(0, 8), ha='center', fontsize=9)
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, 'age_by_year.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path

def chart_pku_work_years(records):
    """北大工作年限分布"""
    years = [r['pku_work_years'] for r in records if r.get('pku_work_years') and 0 < r['pku_work_years'] <= 80]
    if not years:
        return None

    fig, ax = plt.subplots(figsize=(10, 6))
    bins = range(0, max(years) + 5, 5)
    ax.hist(years, bins=bins, color='#27ae60', edgecolor='white', alpha=0.85)
    ax.set_xlabel('北大工作年限（年）', fontsize=13)
    ax.set_ylabel('人数', fontsize=13)
    ax.set_title('北京大学讣告 — 北大工作年限分布', fontsize=16, fontweight='bold')
    mean_y = np.mean(years)
    ax.axvline(mean_y, color='#c0392b', linestyle='--', linewidth=1.5, label=f'均值: {mean_y:.1f}年')
    ax.legend(fontsize=11)
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, 'pku_work_years.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path

def chart_gender_distribution(records):
    """性别分布"""
    genders = [r['gender'] for r in records if r.get('gender')]
    counter = Counter(genders)

    fig, ax = plt.subplots(figsize=(6, 6))
    labels = list(counter.keys())
    sizes = list(counter.values())
    colors = ['#3498db', '#e74c3c', '#95a5a6']
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors[:len(labels)],
           startangle=90, textprops={'fontsize': 13})
    ax.set_title('北京大学讣告 — 性别分布', fontsize=16, fontweight='bold')
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, 'gender_distribution.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path

def chart_publishing_org(records):
    """发布单位分布"""
    orgs = [r['publishing_org'] for r in records if r.get('publishing_org')]
    # Simplify
    simplified = []
    for o in orgs:
        o = o.replace('北京大学', '').replace('治丧办公室', '').replace('治丧委员会', '').replace('治丧小组', '')
        if o:
            simplified.append(o)
        else:
            simplified.append('未分类')
    counter = Counter(simplified)
    top10 = counter.most_common(10)

    fig, ax = plt.subplots(figsize=(10, 6))
    labels = [d[0] for d in top10][::-1]
    values = [d[1] for d in top10][::-1]
    colors = plt.cm.Purples(np.linspace(0.3, 0.9, len(labels)))
    ax.barh(labels, values, color=colors, edgecolor='white')
    ax.set_xlabel('讣告数量', fontsize=12)
    ax.set_title('北京大学讣告 — 治丧单位分布 Top 10', fontsize=14, fontweight='bold')
    for i, v in enumerate(values):
        ax.text(v + 0.3, i, str(v), va='center', fontsize=10)
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, 'publishing_org.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path

def chart_monthly_distribution(records):
    """按月份分布"""
    months = []
    for r in records:
        dd = r.get('death_date', '')
        if dd and len(dd) >= 7:
            try:
                m = int(dd[5:7])
                if 1 <= m <= 12:
                    months.append(m)
            except:
                pass
    if not months:
        return None

    counter = Counter(months)
    month_labels = [f'{m}月' for m in range(1, 13)]
    values = [counter.get(m, 0) for m in range(1, 13)]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(month_labels, values, color='#e74c3c', edgecolor='white', alpha=0.85)
    ax.set_xlabel('月份', fontsize=12)
    ax.set_ylabel('讣告数量', fontsize=12)
    ax.set_title('北京大学讣告 — 月份分布', fontsize=16, fontweight='bold')
    for i, v in enumerate(values):
        if v > 0:
            ax.text(i, v + 1, str(v), ha='center', fontsize=9)
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, 'monthly_distribution.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path

def generate_summary_stats(records):
    """生成统计摘要"""
    stats = {'total': len(records)}

    # Ages
    ages = [r['age'] for r in records if r.get('age') and 20 <= r['age'] <= 120]
    if ages:
        stats['age_mean'] = round(np.mean(ages), 1)
        stats['age_median'] = round(np.median(ages), 1)
        stats['age_min'] = min(ages)
        stats['age_max'] = max(ages)
        stats['age_std'] = round(np.std(ages), 1)

    # Gender
    genders = Counter(r['gender'] for r in records if r.get('gender'))
    stats['gender'] = dict(genders)

    # Roles
    roles = Counter(r['role'] for r in records if r.get('role'))
    stats['roles'] = dict(roles.most_common(10))

    # Departments
    depts = Counter(r['department'].replace('北京大学', '') for r in records if r.get('department'))
    stats['top_departments'] = dict(depts.most_common(10))

    # Provinces
    provs = Counter(r['province'] for r in records if r.get('province'))
    stats['top_provinces'] = dict(provs.most_common(10))

    # Schools
    schools = Counter(r['undergraduate_school'] for r in records if r.get('undergraduate_school'))
    stats['top_schools'] = dict(schools.most_common(10))

    # Coverage
    fields = ['name', 'birth_date', 'death_date', 'age', 'native_place', 'role',
              'education', 'undergraduate_school', 'department', 'publishing_org', 'gender']
    stats['coverage'] = {}
    for f in fields:
        count = sum(1 for r in records if r.get(f))
        stats['coverage'][f] = f'{count}/{len(records)} ({100*count/len(records):.1f}%)'

    return stats

def main():
    records = load_data()
    print(f'Loaded {len(records)} records')

    # Generate all charts
    charts = {}
    chart_funcs = {
        'age_distribution': lambda: chart_age_distribution(records),
        'role_distribution': lambda: chart_role_distribution(records),
        'department_distribution': lambda: chart_department_distribution(records),
        'province_distribution': lambda: chart_province_distribution(records),
        'school_distribution': lambda: chart_school_distribution(records),
        'timeline': lambda: chart_timeline(records),
        'age_by_year': lambda: chart_age_by_year(records),
        'pku_work_years': lambda: chart_pku_work_years(records),
        'gender_distribution': lambda: chart_gender_distribution(records),
        'publishing_org': lambda: chart_publishing_org(records),
        'monthly_distribution': lambda: chart_monthly_distribution(records),
    }

    for name, func in chart_funcs.items():
        try:
            path = func()
            if path:
                charts[name] = path
                print(f'  Generated: {name}')
            else:
                print(f'  Skipped: {name} (no data)')
        except Exception as e:
            print(f'  Error generating {name}: {e}')

    # Save summary stats
    stats = generate_summary_stats(records)
    with open(r'D:\虚拟C盘\study\0\summary_stats.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f'\nSummary stats saved')

    # Print summary
    print(f'\n=== 数据概览 ===')
    print(f'讣告总数: {stats["total"]}')
    print(f'平均享年: {stats.get("age_mean", "N/A")}岁 (中位数: {stats.get("age_median", "N/A")}岁)')
    print(f'年龄范围: {stats.get("age_min", "N/A")} - {stats.get("age_max", "N/A")}岁')
    print(f'性别分布: {stats.get("gender", {})}')
    print(f'\n字段覆盖率:')
    for k, v in stats.get('coverage', {}).items():
        print(f'  {k}: {v}')
    print(f'\n生成图表: {len(charts)}个')

if __name__ == '__main__':
    main()
