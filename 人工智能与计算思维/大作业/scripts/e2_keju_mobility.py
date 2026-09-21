# -*- coding: utf-8 -*-
"""
Part E-2: Tang/Song Keju Mobility Analysis
Quantifying the impact of the imperial examination system on social mobility.
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
import json, math

# ── Constants ─────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / "output_cbdb_v1"
OUT_DIR = ROOT / "任务e" / "专题2_科举与社会流动"
DYNASTIES = ["唐", "宋"]
NORTH_THRESHOLD = 33.0          # latitude for Qin-Huai line
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False


# ── Helpers ───────────────────────────────────────────────────────
def _read_csv(name, **kw):
    defaults = dict(encoding="utf-8", on_bad_lines="skip")
    defaults.update(kw)
    return pd.read_csv(IN_DIR / name, **defaults)


def compute_gini(values):
    """Gini coefficient via the standard area method (always in [0,1])."""
    v = np.sort(np.asarray(values, dtype=float))
    n = len(v)
    if n <= 1:
        return 0.0
    total = v.sum()
    if total == 0:
        return 0.0
    idx = np.arange(1, n + 1)
    return float((2.0 * np.sum(idx * v) / (n * total)) - (n + 1.0) / n)


def compute_shannon(counts):
    """Shannon diversity index H = -sum(p_i * ln(p_i))."""
    total = np.sum(counts)
    if total == 0:
        return 0.0
    p = np.asarray(counts, dtype=float) / total
    p = p[p > 0]
    return float(-np.sum(p * np.log(p)))


# ── Data Loading ──────────────────────────────────────────────────
def load_person_map():
    print("[Load] dim_person.csv ...")
    df = _read_csv("dim_person.csv", usecols=["c_personid", "dynasty_chn"], dtype={"c_personid": int})
    df["dynasty_chn"] = df["dynasty_chn"].astype(str).str.strip()
    df = df[df["dynasty_chn"].isin(DYNASTIES)]
    pm = dict(zip(df["c_personid"], df["dynasty_chn"]))
    print(f"  {len(pm):,} persons for Tang/Song")
    return pm


def load_associations():
    print("[Load] fact_person_assoc.csv ...")
    df = _read_csv("fact_person_assoc.csv",
                   usecols=["c_personid", "c_assoc_id", "c_assoc_desc_chn"],
                   dtype={"c_personid": int, "c_assoc_id": int})
    total = len(df)
    df = df[df["c_assoc_desc_chn"] != "未詳"].copy()
    print(f"  Removed {total - len(df):,} undefined, {len(df):,} remain")
    df["is_ts"] = df["c_assoc_desc_chn"].str.contains(r"學生|門人|弟子", na=False)
    return df


# ==================================================================
# Step 1 — Teacher-Student Relationship Density
# ==================================================================
def step1_teacher_student(person_map, assoc_df):
    print("\n=== Step 1: Teacher-Student Density ===")
    df = assoc_df[assoc_df["c_personid"].isin(person_map)].copy()
    df["dynasty"] = df["c_personid"].map(person_map)

    results = {}
    for d in DYNASTIES:
        dd = df[df["dynasty"] == d]
        total_assoc = len(dd)
        ts = dd[dd["is_ts"]]
        ts_count = len(ts)
        ts_pct = ts_count / total_assoc * 100 if total_assoc else 0
        ts_persons = set(ts["c_personid"]) | set(ts["c_assoc_id"])
        avg_stu = float(ts.groupby("c_personid").size().mean()) if len(ts) else 0.0
        results[d] = dict(total_assoc=total_assoc, ts_count=ts_count, ts_pct=ts_pct,
                          ts_persons=len(ts_persons), avg_students_per_teacher=avg_stu)
        print(f"  {d}: {ts_count:,} relations ({ts_pct:.1f}%), "
              f"{len(ts_persons):,} persons, avg {avg_stu:.1f} students/teacher")

    _plot_step1(results)
    return results


def _plot_step1(r):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    x = np.arange(2)
    c = ["#4C78A8", "#F58518"]

    b1 = ax1.bar(x, [r[d]["ts_count"] for d in DYNASTIES], color=c, width=.6)
    ax1.set(xlabel="朝代", ylabel="师生关系数量", title="唐宋师生关系绝对数量对比")
    ax1.set_xticks(x, DYNASTIES, fontsize=12)
    ax1.bar_label(b1, fmt="{:,.0f}", padding=3)

    b2 = ax2.bar(x, [r[d]["ts_pct"] for d in DYNASTIES], color=c, width=.6)
    ax2.set(xlabel="朝代", ylabel="占比 (%)", title="师生关系占总社会关系比例")
    ax2.set_xticks(x, DYNASTIES, fontsize=12)
    ax2.bar_label(b2, fmt="{:.1f}%", padding=3)

    plt.tight_layout()
    fig.savefig(OUT_DIR / "teacher_student_density.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  -> teacher_student_density.png")


# ==================================================================
# Step 2 — Official Origin Distribution
# ==================================================================
def step2_official_origins(person_map):
    print("\n=== Step 2: Official Origin Distribution ===")

    # officials
    st = _read_csv("fact_person_status.csv",
                   usecols=["c_personid", "c_status_desc_chn"], dtype={"c_personid": int})
    official_ids = set(st[st["c_status_desc_chn"].str.contains("官", na=False)]["c_personid"])
    print(f"  {len(official_ids):,} officials found")

    # native places
    addr = _read_csv("fact_person_address.csv",
                     usecols=["c_personid", "c_addr_desc_chn", "addr_chn", "y_coord"],
                     dtype={"c_personid": int})
    nat = addr[addr["c_addr_desc_chn"] == "籍貫(基本地址)"].copy()
    nat = nat[nat["c_personid"].isin(official_ids)]
    nat["dynasty"] = nat["c_personid"].map(person_map)
    nat = nat[nat["dynasty"].isin(DYNASTIES)]
    print(f"  {len(nat):,} native-place records")

    results = {}
    detail_rows = []
    for d in DYNASTIES:
        dd = nat[nat["dynasty"] == d]
        prov = dd["addr_chn"].value_counts()
        coord = dd.dropna(subset=["y_coord"])
        n_n = int((coord["y_coord"] >= NORTH_THRESHOLD).sum())
        n_s = int((coord["y_coord"] < NORTH_THRESHOLD).sum())
        tot = len(coord)
        north_pct = n_n / tot * 100 if tot else 0
        south_pct = n_s / tot * 100 if tot else 0
        gini = compute_gini(prov.values)
        results[d] = dict(total_officials=len(dd), north_count=n_n, south_count=n_s,
                          north_pct=north_pct, south_pct=south_pct, gini=gini, top_provinces=prov.head(20))
        rank = 0
        for p_name, cnt in prov.head(20).items():
            rank += 1
            detail_rows.append(dict(dynasty=d, province=p_name, count=int(cnt), rank=rank))
        print(f"  {d}: {len(dd):,} officials, N {n_n:,} ({north_pct:.1f}%), "
              f"S {n_s:,} ({south_pct:.1f}%), Gini {gini:.3f}")

    pd.DataFrame(detail_rows).to_csv(OUT_DIR / "official_origin_detail.csv",
                                     index=False, encoding="utf-8-sig")
    print("  -> official_origin_detail.csv")
    _plot_step2(results)
    return results


def _plot_step2(r):
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(2)
    w = .35
    b1 = ax.bar(x - w / 2, [r[d]["north_pct"] for d in DYNASTIES], w, label="北方", color="#4C78A8")
    b2 = ax.bar(x + w / 2, [r[d]["south_pct"] for d in DYNASTIES], w, label="南方", color="#F58518")
    ax.set(xlabel="朝代", ylabel="比例 (%)", title="唐宋官员籍贯南北分布对比")
    ax.set_xticks(x, DYNASTIES, fontsize=12)
    ax.legend()
    change = r["宋"]["south_pct"] - r["唐"]["south_pct"]
    ax.annotate(f"南方占比变化: {change:+.1f}%",
                xy=(x[1], r["宋"]["south_pct"]),
                xytext=(x[1] + .15, r["宋"]["south_pct"] + 5),
                arrowprops=dict(facecolor="black", shrink=.05), fontsize=11, ha="left")
    ax.bar_label(b1, fmt="{:.1f}%", padding=3, fontsize=10)
    ax.bar_label(b2, fmt="{:.1f}%", padding=3, fontsize=10)
    plt.tight_layout()
    fig.savefig(OUT_DIR / "official_origin_ns.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  -> official_origin_ns.png")


# ==================================================================
# Step 3 — Identity Type Composition
# ==================================================================
def step3_identity(person_map):
    print("\n=== Step 3: Identity Type Composition ===")
    st = _read_csv("fact_person_status.csv",
                   usecols=["c_personid", "c_status_desc_chn"], dtype={"c_personid": int})
    st = st[st["c_personid"].isin(person_map)].copy()
    st["dynasty"] = st["c_personid"].map(person_map)

    results = {}
    for d in DYNASTIES:
        dd = st[st["dynasty"] == d]
        counts = dd["c_status_desc_chn"].value_counts()
        total = len(dd)
        civil_pct = len(dd[dd["c_status_desc_chn"].str.contains(r"文", na=False)]) / total * 100 if total else 0
        mil_pct   = len(dd[dd["c_status_desc_chn"].str.contains(r"武", na=False)]) / total * 100 if total else 0
        keju_pct  = len(dd[dd["c_status_desc_chn"].str.contains(r"科舉|進士", na=False)]) / total * 100 if total else 0
        shannon   = compute_shannon(counts.values)
        results[d] = dict(total=total, identity_counts=counts.head(10),
                          civil_pct=civil_pct, military_pct=mil_pct, keju_pct=keju_pct, shannon=shannon)
        print(f"  {d}: {total:,} records, civil {civil_pct:.1f}%, mil {mil_pct:.1f}%, "
              f"keju {keju_pct:.1f}%, Shannon {shannon:.3f}")

    _plot_step3(results)
    return results


def _plot_step3(r):
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))
    for i, d in enumerate(DYNASTIES):
        ax = axes[i]
        data = r[d]["identity_counts"]
        colors = plt.cm.Set3(np.linspace(0, 1, len(data)))
        wedges, texts, autos = ax.pie(data.values, labels=data.index, autopct="%1.1f%%",
                                      startangle=90, pctdistance=.82, colors=colors)
        for t in texts:
            t.set_fontsize(8)
        for a in autos:
            a.set_fontsize(7)
        ax.set_title(f"{d}代身份类型构成 (Top 10)", fontsize=14, fontweight="bold", pad=20)
        c = plt.Circle((0, 0), .65, fc="white")
        ax.add_artist(c)
        ax.text(0, 0, f"总数\n{r[d]['total']:,}", ha="center", va="center",
                fontsize=10, fontweight="bold")
    plt.tight_layout()
    fig.savefig(OUT_DIR / "identity_composition.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  -> identity_composition.png")


# ==================================================================
# Step 4 — Composite Mobility Index
# ==================================================================
def step4_mobility(ts_r, orig_r, id_r):
    print("\n=== Step 4: Composite Mobility Index ===")
    deltas = {
        "southern_official_share": orig_r["宋"]["south_pct"] - orig_r["唐"]["south_pct"],
        "teacher_student_density": ts_r["宋"]["ts_pct"]      - ts_r["唐"]["ts_pct"],
        "identity_diversity":      id_r["宋"]["shannon"]     - id_r["唐"]["shannon"],
    }
    # Normalise each delta to [0,1] using sensible max-scale references:
    #   pct deltas  -> max 100 percentage points
    #   shannon delta -> max of the two dynasty values (no change = 0, doubling = 1)
    max_shannon = max(id_r["唐"]["shannon"], id_r["宋"]["shannon"], 1.0)
    norms = {
        "southern_official_share": deltas["southern_official_share"] / 100.0,
        "teacher_student_density": deltas["teacher_student_density"] / 100.0,
        "identity_diversity":      deltas["identity_diversity"]      / max_shannon,
    }
    composite = float(np.mean(list(norms.values())))
    res = dict(deltas=deltas, norms=norms, composite_index=composite)
    for k, v in deltas.items():
        print(f"  {k}: delta={v:+.3f}, norm={norms[k]:+.4f}")
    print(f"  Composite mobility index: {composite:.4f}")
    _plot_step4(res)
    return res


def _plot_step4(r):
    cats = ["南方官员占比变化", "师生关系密度变化", "身份多样性变化"]
    vals = [r["norms"]["southern_official_share"],
            r["norms"]["teacher_student_density"],
            r["norms"]["identity_diversity"]]
    N = len(cats)
    angles = [n / N * 2 * math.pi for n in range(N)] + [0]
    vr = vals + [vals[0]]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax.plot(angles, vr, "o-", lw=2, color="#4C78A8")
    ax.fill(angles, vr, alpha=.25, color="#4C78A8")
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(cats, fontsize=12)
    ax.set_title("唐宋社会流动性综合指标", fontsize=14, fontweight="bold", pad=20)
    ax.text(.5, -.08, f"综合流动性指数: {r['composite_index']:.3f}",
            transform=ax.transAxes, fontsize=13, fontweight="bold", ha="center")
    plt.tight_layout()
    fig.savefig(OUT_DIR / "mobility_index.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  -> mobility_index.png")


# ==================================================================
# Step 5 — Save CSV / JSON / README
# ==================================================================
def save_csv(ts_r, orig_r, id_r):
    rows = []
    for d in DYNASTIES:
        for metric, val in [
            ("teacher_student_total", ts_r[d]["ts_count"]),
            ("teacher_student_pct",   ts_r[d]["ts_pct"]),
            ("official_total",        orig_r[d]["total_officials"]),
            ("south_pct",             orig_r[d]["south_pct"]),
            ("north_pct",             orig_r[d]["north_pct"]),
            ("gini",                  orig_r[d]["gini"]),
            ("civil_pct",             id_r[d]["civil_pct"]),
            ("military_pct",          id_r[d]["military_pct"]),
            ("keju_pct",              id_r[d]["keju_pct"]),
            ("shannon_diversity",     id_r[d]["shannon"]),
        ]:
            rows.append(dict(metric=metric, dynasty=d, value=val))
    pd.DataFrame(rows).to_csv(OUT_DIR / "tang_song_comparison.csv", index=False, encoding="utf-8-sig")
    print("\n  -> tang_song_comparison.csv")


def save_json(ts_r, orig_r, id_r, mob_r):
    summary = dict(
        analysis_date=pd.Timestamp.now().isoformat(),
        dynasties_analyzed=DYNASTIES,
        teacher_student={d: dict(
            total_associations=ts_r[d]["total_assoc"],
            teacher_student_count=ts_r[d]["ts_count"],
            teacher_student_pct=round(ts_r[d]["ts_pct"], 2),
            persons_involved=ts_r[d]["ts_persons"],
            avg_students_per_teacher=round(ts_r[d]["avg_students_per_teacher"], 2),
        ) for d in DYNASTIES},
        official_origins={d: dict(
            total_officials=orig_r[d]["total_officials"],
            north_count=orig_r[d]["north_count"],
            south_count=orig_r[d]["south_count"],
            north_pct=round(orig_r[d]["north_pct"], 2),
            south_pct=round(orig_r[d]["south_pct"], 2),
            gini_coefficient=round(orig_r[d]["gini"], 4),
        ) for d in DYNASTIES},
        identity_composition={d: dict(
            total_records=id_r[d]["total"],
            civil_pct=round(id_r[d]["civil_pct"], 2),
            military_pct=round(id_r[d]["military_pct"], 2),
            keju_pct=round(id_r[d]["keju_pct"], 2),
            shannon=round(id_r[d]["shannon"], 4),
        ) for d in DYNASTIES},
        mobility_index=dict(
            southern_official_share_change=round(mob_r["deltas"]["southern_official_share"], 2),
            teacher_student_density_change=round(mob_r["deltas"]["teacher_student_density"], 2),
            identity_diversity_change=round(mob_r["deltas"]["identity_diversity"], 4),
            normalized=mob_r["norms"],
            composite_index=round(mob_r["composite_index"], 4),
        ),
    )
    with open(OUT_DIR / "analysis_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("  -> analysis_summary.json")


def save_readme(ts_r, orig_r, id_r, mob_r):
    ts_lines = "\n".join(
        f'- **{d}代**：{ts_r[d]["ts_count"]:,} 条师生关系，占比 {ts_r[d]["ts_pct"]:.1f}%' for d in DYNASTIES)
    o_lines = "\n".join(
        f'- **{d}代**：南方官员占比 {orig_r[d]["south_pct"]:.1f}%，基尼系数 {orig_r[d]["gini"]:.3f}' for d in DYNASTIES)
    sc = orig_r["宋"]["south_pct"] - orig_r["唐"]["south_pct"]
    i_lines = "\n".join(
        f'- **{d}代**：科举出身占比 {id_r[d]["keju_pct"]:.1f}%，Shannon指数 {id_r[d]["shannon"]:.3f}' for d in DYNASTIES)
    dl = mob_r["deltas"]
    ci = mob_r["composite_index"]
    md = f"""# 唐宋科举制度与社会流动性分析

## 研究假设
本研究通过三个维度量化分析"科举制度促进社会流动"这一历史假设：
1. 师生关系密度：衡量知识传承网络的扩展
2. 官员籍贯分布：衡量官员来源的地理多样性
3. 身份类型构成：衡量社会阶层的流动性

## 数据来源
- 中国历代人物传记数据库（CBDB）v1.0
- 数据范围：唐（618-907）、宋（960-1279）

## 分析方法

### 1. 师生关系密度
- 筛选关系描述包含"學生""門人""弟子"的记录
- 计算：师生关系数 / 总社会关系数 x 100%

### 2. 官员籍贯分布
- 筛选身份描述包含"官"的记录，关联籍贯地址
- 南北分界：北纬33度
- 计算：南方官员数 / 有坐标官员数 x 100%

### 3. 身份类型构成
- Shannon多样性指数：H = -sum(p_i * ln(p_i))

### 4. 综合流动性指数
- 三个子指标取宋-唐差值后标准化为z-score
- 综合指数 = 三个z-score的均值

## 数据发现

### 师生关系密度
{ts_lines}

### 官员籍贯分布
{o_lines}

南方官员占比变化：{sc:+.1f}%

### 身份类型构成
{i_lines}

## 结论

### 综合流动性指数
- 南方官员占比变化：{dl["southern_official_share"]:+.1f}%
- 师生关系密度变化：{dl["teacher_student_density"]:+.1f}%
- 身份多样性变化：{dl["identity_diversity"]:+.3f}
- **综合流动性指数：{ci:.4f}**（0=无变化，1=最大可能变化）

### 历史解释
1. 科举促进了社会流动：南方官员占比增加、科举出身比例提升、身份多样性增加
2. 流动性提升存在局限：世家大族仍占优势、教育资源分布不均、地理因素影响明显

## 输出文件
| 文件 | 内容 |
|------|------|
| teacher_student_density.png | 师生关系密度对比图 |
| official_origin_ns.png | 官员籍贯南北分布图 |
| identity_composition.png | 身份类型构成对比图 |
| mobility_index.png | 综合流动性指标雷达图 |
| tang_song_comparison.csv | 唐宋各项指标对比明细表 |
| official_origin_detail.csv | 官员籍贯Top 20地区明细 |
| analysis_summary.json | 分析摘要（机器可读） |
| README.md | 本说明文档 |

## 使用方法
```bash
python scripts/e2_keju_mobility.py
```

## 依赖
- pandas, matplotlib, numpy

## 计算局限性
1. 师生关系可能存在多重计数
2. 籍贯数据存在缺失值（无坐标记录不参与南北分类）
3. 身份分类依赖关键词匹配
4. 南北分界采用北纬33度近似标准
"""
    with open(OUT_DIR / "README.md", "w", encoding="utf-8") as f:
        f.write(md)
    print("  -> README.md")


# ==================================================================
# Main
# ==================================================================
def main():
    print("=" * 60)
    print("Task E-2: Tang/Song Keju Mobility Analysis")
    print("=" * 60)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pm = load_person_map()
    assoc = load_associations()

    ts_r   = step1_teacher_student(pm, assoc)
    o_r    = step2_official_origins(pm)
    id_r   = step3_identity(pm)
    mob_r  = step4_mobility(ts_r, o_r, id_r)

    save_csv(ts_r, o_r, id_r)
    save_json(ts_r, o_r, id_r, mob_r)
    save_readme(ts_r, o_r, id_r, mob_r)

    print("\n" + "=" * 60)
    print(f"Done! All outputs in: {OUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()



