# -*- coding: utf-8 -*-
"""F-2: 人物传记自动生成 (Biography Generator).

Template-based NLG that turns CBDB structured data into natural-language
biographies for historical figures.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

# Paths
ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / "output_cbdb_v1"
OUT_DIR = ROOT / "任务f" / "专题2_人物传记"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Celebrity definitions
CELEB_BY_ID = {
    "蘇軾": 3767, "李白": 32540, "杜甫": 3915,
    "白居易": 32227, "岳飛": 8175, "李清照": 19713,
    "王維": 32174,
}
CELEB_BY_NAME = ["王安石", "司馬光"]


# ======================================================================
# Step 1 — Data Loading & Indexing
# ======================================================================

def load_all():
    """Read all CSVs once, return DataFrames."""
    dim = pd.read_csv(
        IN_DIR / "dim_person.csv", encoding="utf-8",
        usecols=["c_personid", "c_name_chn", "c_female",
                 "c_birthyear", "c_deathyear", "dynasty_chn", "index_addr_chn"],
    )
    status = pd.read_csv(
        IN_DIR / "fact_person_status.csv", encoding="utf-8",
        usecols=["c_personid", "c_sequence", "c_status_desc_chn"],
    )
    addr = pd.read_csv(
        IN_DIR / "fact_person_address.csv", encoding="utf-8",
        usecols=["c_personid", "addr_chn"],
    )
    assoc = pd.read_csv(
        IN_DIR / "fact_person_assoc.csv", encoding="utf-8",
        usecols=["c_personid", "c_assoc_id"],
    )
    return dim, status, addr, assoc


def build_name_indexes(dim):
    """Vectorised name_to_id and dynasty_of lookups."""
    valid = dim["c_name_chn"].notna()
    name_to_id = dict(
        zip(dim.loc[valid, "c_name_chn"].str.strip(),
            dim.loc[valid, "c_personid"].astype(int))
    )
    dynasty_of = dict(
        zip(dim["c_personid"].astype(int),
            dim["dynasty_chn"].fillna("").str.strip())
    )
    return name_to_id, dynasty_of


def get_song_top_n(dynasty_of, status, addr, assoc, n=1000):
    """Song-dynasty top N by total fact-table row count."""
    sc = status["c_personid"].value_counts()
    ac = addr["c_personid"].value_counts()
    oc = assoc["c_personid"].value_counts()
    all_counts = sc.add(ac, fill_value=0).add(oc, fill_value=0)
    song_pids = {pid for pid, dy in dynasty_of.items() if dy == "宋"}
    song_counts = {int(pid): cnt for pid, cnt in all_counts.items()
                   if int(pid) in song_pids}
    ranked = sorted(song_counts.items(), key=lambda x: -x[1])
    return [pid for pid, _ in ranked[:n]]


def build_person_info(dim, target_pids):
    """Detailed person info for target set only."""
    sub = dim[dim["c_personid"].isin(target_pids)]
    info = {}
    for r in sub.itertuples(index=False):
        pid = int(r.c_personid)
        name = str(r.c_name_chn).strip() if pd.notna(r.c_name_chn) else ""
        origin = str(r.index_addr_chn).strip() if pd.notna(r.index_addr_chn) else ""
        info[pid] = {
            "name": name,
            "female": int(r.c_female) if pd.notna(r.c_female) else 0,
            "birth": float(r.c_birthyear) if pd.notna(r.c_birthyear) else None,
            "death": float(r.c_deathyear) if pd.notna(r.c_deathyear) else None,
            "dynasty": str(r.dynasty_chn).strip() if pd.notna(r.dynasty_chn) else "",
            "origin": origin,
        }
    return info


def _clean_label(label):
    """Strip brackets; collapse '為官者：X' sub-categories."""
    if not isinstance(label, str) or not label.strip():
        return ""
    s = label.strip().strip("[]")
    if s.startswith("為官者：") or s.startswith("為官者:"):
        return "為官者"
    return s


def build_status_top3(status, target_pids):
    """Top 3 cleaned status labels per target person."""
    sub = status[status["c_personid"].isin(target_pids)]
    result = {}
    for pid, grp in sub.groupby("c_personid"):
        grp = grp.sort_values("c_sequence")
        seen, labels = set(), []
        for raw in grp["c_status_desc_chn"].values:
            lbl = _clean_label(raw)
            if lbl and lbl not in seen:
                seen.add(lbl)
                labels.append(lbl)
            if len(labels) >= 3:
                break
        result[int(pid)] = labels
    return result


def build_addr_top5(addr, target_pids):
    """Top 5 places (by frequency) per target person."""
    sub = addr[addr["c_personid"].isin(target_pids)]
    result = {}
    for pid, grp in sub.groupby("c_personid"):
        vc = grp["addr_chn"].dropna().value_counts()
        places = [p for p in vc.index if isinstance(p, str) and p.strip()]
        result[int(pid)] = places[:5]
    return result


def build_assoc_top5(assoc, target_pids, name_to_id):
    """Top 5 associated-person names per target person."""
    id_to_name = {v: k for k, v in name_to_id.items()}
    sub = assoc[assoc["c_personid"].isin(target_pids)]
    result = {}
    for pid, grp in sub.groupby("c_personid"):
        vc = grp["c_assoc_id"].value_counts()
        names = []
        for aid in vc.index:
            nm = id_to_name.get(int(aid), "")
            if nm and nm not in names:
                names.append(nm)
            if len(names) >= 5:
                break
        result[int(pid)] = names
    return result


# ======================================================================
# Step 2 — Bio Generation
# ======================================================================

def generate_one_liner(pid, person_info, status_top3):
    """Generate a one-sentence biography."""
    info = person_info.get(pid)
    if not info:
        return ""
    name = info["name"]
    dynasty = info["dynasty"]
    origin = info["origin"]

    # Dynasty + gender label
    if info["female"] == 1:
        dgl = f"{dynasty}女" if dynasty else "女"
    else:
        dgl = f"{dynasty}人" if dynasty else ""

    # Year range
    b, d = info["birth"], info["death"]
    if b is not None and d is not None:
        yrs = f"（{int(b)}-{int(d)}）"
    elif b is not None:
        yrs = f"（{int(b)}-?）"
    elif d is not None:
        yrs = f"（?- {int(d)}）"
    else:
        yrs = ""

    # Origin segment
    orig_seg = f"，{origin}人" if origin else ""

    # Status segment
    st = status_top3.get(pid, [])
    st_seg = f"，{'、'.join(st)}" if st else ""

    # Compose
    if yrs:
        return f"{name}{yrs}，{dgl}{orig_seg}{st_seg}。"
    return f"{name}，{dgl}{orig_seg}{st_seg}。"


def generate_bio(pid, person_info, status_top3, addr_top5, assoc_top5):
    """Generate a paragraph-length biography."""
    info = person_info.get(pid)
    if not info:
        return ""
    name = info["name"]
    dynasty = info["dynasty"]
    origin = info["origin"]

    # Dynasty + gender label
    if info["female"] == 1:
        dgl = f"{dynasty}女" if dynasty else "女"
    else:
        dgl = f"{dynasty}人" if dynasty else ""

    # Opening sentence
    if origin:
        s = f"{name}，{dgl}，籍貫{origin}。"
    else:
        s = f"{name}，{dgl}。"

    # Born line
    b, d = info["birth"], info["death"]
    if b is not None and d is not None:
        s += f"生於{int(b)}年，卒於{int(d)}年。"
    elif b is not None:
        s += f"生於{int(b)}年。"
    elif d is not None:
        s += f"卒於{int(d)}年。"

    # Status line
    st = status_top3.get(pid, [])
    if st:
        st_text = "、".join(st)
        if st_text.startswith("為"):
            s += st_text + "。"
        else:
            s += f"為{st_text}。"

    # Places
    places = addr_top5.get(pid, [])
    if places:
        s += f"一生主要活動於{'、'.join(places)}。"

    # Associations
    assocs = assoc_top5.get(pid, [])
    if assocs:
        s += f"與{'、'.join(assocs)}等人交遊唱和。"

    return s


# ======================================================================
# Step 3 — Batch Generation
# ======================================================================

def batch_generate(pids, person_info, status_top3, addr_top5, assoc_top5):
    """Generate bios for a list of person IDs."""
    rows = []
    for pid in pids:
        info = person_info.get(pid, {})
        ol = generate_one_liner(pid, person_info, status_top3)
        bio = generate_bio(pid, person_info, status_top3, addr_top5, assoc_top5)
        rows.append({
            "personid": pid,
            "name": info.get("name", ""),
            "dynasty": info.get("dynasty", ""),
            "one_liner": ol,
            "bio_paragraph": bio,
            "word_count": len(bio),
        })
    return pd.DataFrame(rows)


# ======================================================================
# Step 4 — Quality Assessment
# ======================================================================

def quality_assessment(df, top_pids, person_info, status_top3, addr_top5, assoc_top5):
    """Compute quality metrics and sample 20 for review."""
    total = len(df)
    avg_ol = df["one_liner"].str.len().mean()
    avg_bio = df["word_count"].mean()

    birth_n = sum(1 for p in top_pids
                  if person_info.get(p, {}).get("birth") is not None)
    death_n = sum(1 for p in top_pids
                  if person_info.get(p, {}).get("death") is not None)
    place_n = sum(1 for p in top_pids if addr_top5.get(p))
    assoc_n = sum(1 for p in top_pids if assoc_top5.get(p))

    stats = {
        "total": total,
        "avg_one_liner_chars": round(avg_ol, 1),
        "avg_bio_chars": round(avg_bio, 1),
        "birth_coverage": round(birth_n / total, 4),
        "death_coverage": round(death_n / total, 4),
        "place_coverage": round(place_n / total, 4),
        "assoc_coverage": round(assoc_n / total, 4),
    }

    metric_rows = [
        {"指標": "總人數", "數值": str(total)},
        {"指標": "一句話簡介平均字數", "數值": str(stats["avg_one_liner_chars"])},
        {"指標": "一段話小傳平均字數", "數值": str(stats["avg_bio_chars"])},
        {"指標": "生年覆蓋率", "數值": f"{birth_n}/{total} ({birth_n/total:.1%})"},
        {"指標": "卒年覆蓋率", "數值": f"{death_n}/{total} ({death_n/total:.1%})"},
        {"指標": "地名覆蓋率", "數值": f"{place_n}/{total} ({place_n/total:.1%})"},
        {"指標": "交往對象覆蓋率", "數值": f"{assoc_n}/{total} ({assoc_n/total:.1%})"},
    ]

    # Random sample 20
    sample = df.sample(min(20, total), random_state=42)
    for i, (_, r) in enumerate(sample.iterrows()):
        metric_rows.append({"指標": f"抽樣_{i+1}_personid", "數值": str(r["personid"])})
        metric_rows.append({"指標": f"抽樣_{i+1}_name", "數值": r["name"]})
        metric_rows.append({"指標": f"抽樣_{i+1}_one_liner", "數值": r["one_liner"]})
        metric_rows.append({"指標": f"抽樣_{i+1}_bio", "數值": r["bio_paragraph"]})

    return pd.DataFrame(metric_rows), stats


# ======================================================================
# Step 5 — Celebrity Cases
# ======================================================================

def celebrity_bios(person_info, name_to_id, status_top3, addr_top5, assoc_top5):
    """Generate bios for named celebrities."""
    rows = []
    for name, pid in CELEB_BY_ID.items():
        ol = generate_one_liner(pid, person_info, status_top3)
        bio = generate_bio(pid, person_info, status_top3, addr_top5, assoc_top5)
        rows.append({"personid": pid, "name": name,
                     "one_liner": ol, "bio_paragraph": bio})
    for name in CELEB_BY_NAME:
        pid = name_to_id.get(name)
        if pid:
            ol = generate_one_liner(pid, person_info, status_top3)
            bio = generate_bio(pid, person_info, status_top3, addr_top5, assoc_top5)
            rows.append({"personid": pid, "name": name,
                         "one_liner": ol, "bio_paragraph": bio})
        else:
            rows.append({"personid": "", "name": name,
                         "one_liner": "未找到", "bio_paragraph": "未找到"})
    return pd.DataFrame(rows)


# ======================================================================
# Step 6 — HTML Query Page
# ======================================================================

def generate_html(df):
    """Build an interactive HTML page with embedded data + sidebar list."""
    records = df[["personid", "name", "dynasty",
                  "one_liner", "bio_paragraph"]].to_dict("records")
    data_json = json.dumps(records, ensure_ascii=False)

    css = """
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:"Noto Serif TC","Source Han Serif TC","SimSun",serif;background:#F5F0E8;color:#3C2415;min-height:100vh}
.layout{display:flex;max-width:1200px;margin:0 auto;min-height:100vh}

/* ---- Sidebar ---- */
.sidebar{width:260px;min-width:260px;background:#EDE6D6;border-right:1px solid #D4C5A0;
  display:flex;flex-direction:column;height:100vh;position:sticky;top:0}
.sidebar h2{font-size:1rem;color:#8B1A1A;padding:18px 16px 10px;letter-spacing:2px;
  border-bottom:1px solid #D4C5A0;text-align:center}
.sidebar .badge{display:inline-block;background:#8B1A1A;color:#FFFDF5;font-size:.72rem;
  padding:2px 8px;border-radius:10px;margin-left:4px;vertical-align:middle}
.sidebar .count{font-size:.78rem;color:#8B6914;text-align:center;padding:6px 0 8px;
  border-bottom:1px solid #D4C5A0}
.sidebar .list-wrap{flex:1;overflow-y:auto;padding:6px 0}
.sidebar .list-wrap::-webkit-scrollbar{width:6px}
.sidebar .list-wrap::-webkit-scrollbar-thumb{background:#C4A35A;border-radius:3px}
.s-item{display:flex;align-items:center;padding:7px 16px;cursor:pointer;
  transition:background .15s;border-left:3px solid transparent;font-size:.9rem}
.s-item:hover{background:#E0D8C4}
.s-item.active{background:#FFFDF5;border-left-color:#8B1A1A;color:#8B1A1A;font-weight:600}
.s-item .pid{font-size:.72rem;color:#8B6914;margin-left:auto;min-width:40px;text-align:right}

/* ---- Main ---- */
.main{flex:1;display:flex;flex-direction:column;padding:32px 36px 40px;min-width:0}
h1{text-align:center;font-size:2rem;color:#8B1A1A;letter-spacing:6px;margin-bottom:4px}
.sub{text-align:center;color:#8B6914;font-size:.88rem;margin-bottom:4px}
.scope{text-align:center;margin-bottom:22px}
.scope .tag{display:inline-block;background:#8B1A1A;color:#FFFDF5;font-size:.82rem;
  padding:4px 14px;border-radius:14px;letter-spacing:1px}
.search{display:flex;gap:12px;justify-content:center;margin-bottom:24px}
.search input{width:340px;padding:12px 16px;font-size:1rem;border:2px solid #C4A35A;
  border-radius:8px;background:#FFFDF5;color:#3C2415;font-family:inherit;outline:none}
.search input:focus{border-color:#8B1A1A}
.search button{padding:12px 28px;background:#8B1A1A;color:#FFFDF5;border:none;
  border-radius:8px;font-size:1rem;cursor:pointer;font-family:inherit;transition:background .2s}
.search button:hover{background:#6B0F0F}
.card{background:#FFFDF5;border:1px solid #D4C5A0;border-radius:12px;padding:28px;
  margin-bottom:18px;box-shadow:0 2px 8px rgba(60,36,21,.08)}
.card h3{color:#8B1A1A;font-size:1.3rem;margin-bottom:10px;padding-bottom:8px;
  border-bottom:1px solid #D4C5A0}
.meta{color:#8B6914;font-size:.84rem;margin-bottom:14px}
.ol{font-size:1.08rem;line-height:1.7;color:#5A3E1B;margin-bottom:14px;padding:12px 16px;
  background:#F9F3E3;border-left:3px solid #8B1A1A;border-radius:0 8px 8px 0}
.bio{font-size:.98rem;line-height:1.85;color:#3C2415}
.nr{text-align:center;color:#8B6914;font-size:1.05rem;padding:40px}
.hint{text-align:center;color:#A89470;font-size:.82rem;margin-top:8px}

@media(max-width:800px){
  .layout{flex-direction:column}
  .sidebar{width:100%;min-width:0;height:auto;position:static;max-height:280px}
  .main{padding:20px 16px}
  .search input{width:100%}
}
"""

    js = """
var D=__DATA__;
var bN={},bI={};
D.forEach(function(d){bN[d.name]=d;bI[String(d.personid)]=d});

// Build sidebar list
var sb=document.getElementById('slist');
var html='';
D.forEach(function(d,i){
  html+='<div class="s-item" data-idx="'+i+'" onclick="pick('+i+')">'
    +'<span>'+d.name+'</span>'
    +'<span class="pid">#'+d.personid+'</span></div>';
});
sb.innerHTML=html;

function pick(idx){
  var d=D[idx];
  showCard(d);
  // highlight sidebar
  var items=sb.querySelectorAll('.s-item');
  items.forEach(function(el){el.classList.remove('active')});
  if(items[idx])items[idx].classList.add('active');
}

function showCard(d){
  var o=document.getElementById('r');
  o.innerHTML='<div class="card"><h3>'+d.name+'</h3>'
    +'<div class="meta">\u4eba\u7269ID: '+d.personid
    +' &middot; '+d.dynasty+'</div>'
    +'<div class="ol">'+d.one_liner+'</div>'
    +'<div class="bio">'+d.bio_paragraph+'</div></div>';
}

function doSearch(){
  var q=document.getElementById('q').value.trim(),o=document.getElementById('r'),R=[];
  if(!q){o.innerHTML='<div class="nr">\u8acb\u8f38\u5165\u59d3\u540d\u6216\u4eba\u7269ID</div>';return}
  if(bN[q])R.push(bN[q]);
  if(bI[q]&&R.indexOf(bI[q])<0)R.push(bI[q]);
  if(!R.length)R=D.filter(function(d){return d.name.indexOf(q)>=0});
  if(!R.length){o.innerHTML='<div class="nr">\u672a\u627e\u5230\u5339\u914d\u7684\u4eba\u7269</div>';return}
  if(R.length===1){showCard(R[0]);return}
  o.innerHTML=R.map(function(d){
    return '<div class="card" style="cursor:pointer" onclick="showCard(bN[\\''+d.name+'\\'])">'
      +'<h3>'+d.name+'</h3>'
      +'<div class="meta">\u4eba\u7269ID: '+d.personid+' &middot; '+d.dynasty+'</div>'
      +'<div class="ol">'+d.one_liner+'</div></div>';
  }).join('');
}
""".replace("__DATA__", data_json)

    return (
        '<!DOCTYPE html>\n<html lang="zh-Hant">\n<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '<title>\u6b77\u53f2\u4eba\u7269\u50b3\u8a18\u67e5\u8a62</title>\n'
        '<style>\n' + css + '\n</style>\n</head>\n<body>\n'
        '<div class="layout">\n'
        '  <aside class="sidebar">\n'
        '    <h2>\u4eba\u7269\u6e05\u55ae <span class="badge">\u5b8b\u4ee3</span></h2>\n'
        '    <div class="count">\u5171 ' + str(len(records)) + ' \u4eba</div>\n'
        '    <div class="list-wrap" id="slist"></div>\n'
        '  </aside>\n'
        '  <div class="main">\n'
        '    <h1>\u6b77\u53f2\u4eba\u7269\u50b3\u8a18\u67e5\u8a62</h1>\n'
        '    <p class="sub">\u57fa\u65bc CBDB \u4e2d\u570b\u6b77\u4ee3\u4eba\u7269\u50b3\u8a18\u8cc7\u6599\u5eab \u00b7 \u81ea\u52d5\u751f\u6210</p>\n'
        '    <div class="scope"><span class="tag">\u7576\u524d\u6578\u64da\uff1a\u5b8b\u4ee3 Top 1000 \u4eba\u7269</span></div>\n'
        '    <div class="search">\n'
        '      <input id="q" placeholder="\u8f38\u5165\u59d3\u540d\u6216\u4eba\u7269ID...">\n'
        '      <button onclick="doSearch()">\u67e5 \u8a62</button>\n'
        '    </div>\n'
        '    <div id="r" class="nr">\u9ede\u64ca\u5de6\u5074\u4eba\u7269\u540d\u55ae\uff0c\u6216\u8f38\u5165\u59d3\u540d\u641c\u5c0b</div>\n'
        '  </div>\n'
        '</div>\n'
        '<script>\n' + js + '</script>\n</body>\n</html>'
    )



# ======================================================================
# Step 7 — README & Summary
# ======================================================================

def write_readme(stats, celeb_df):
    lines = [
        "# F-2: 人物傳記自動生成", "",
        "將 CBDB 結構化數據自動轉換為歷史人物的自然語言傳記。", "",
        "## 數據來源", "",
        "- `dim_person.csv` — 人物主維度（姓名、性別、生卒年、朝代、籍貫）",
        "- `fact_person_status.csv` — 身份維度表",
        "- `fact_person_address.csv` — 地址經歷表",
        "- `fact_person_assoc.csv` — 社會關係表", "",
        "## 傳記模板", "",
        "### 一句話簡介", "",
        "```",
        "{name}（{birth}-{death}），{dynasty}人，{origin}人，{top_status}。",
        "```", "",
        "### 一段話小傳", "",
        "```",
        "{name}，{dynasty}人，籍貫{origin}。{born_line}{status_line}一生主要活動於{places}。{assoc_line}",
        "```", "",
        "## 變量來源與缺值處理", "",
        "| 變量 | 來源 | 缺值處理 |",
        "|------|------|----------|",
        "| origin | dim_person.index_addr_chn | 空則省略籍貫句 |",
        "| birth/death | dim_person.c_birthyear/deathyear | 皆缺則省略生卒年句 |",
        "| top_status | fact_person_status Top 3 by c_sequence | 空則省略身份句 |",
        "| places | fact_person_address Top 5 by 頻次 | 空則省略活動地句 |",
        "| assoc | fact_person_assoc Top 5 by 頻次 | 空則省略交往句 |", "",
        "## 身份標籤清洗規則", "",
        "- 去除 [] 方括號",
        "- 為官者：文 / 為官者：武 等子類統一合併為「為官者」",
        "- 按 c_sequence 升序取前 3 個去重標籤", "",
        "## 統計摘要", "",
        f"- 宋代 Top {stats['total']} 人物傳記已生成",
        f"- 一句話簡介平均: {stats['avg_one_liner_chars']} 字",
        f"- 一段話小傳平均: {stats['avg_bio_chars']} 字",
        f"- 生年覆蓋率: {stats['birth_coverage']:.1%}",
        f"- 卒年覆蓋率: {stats['death_coverage']:.1%}",
        f"- 地名覆蓋率: {stats['place_coverage']:.1%}",
        f"- 交往對象覆蓋率: {stats['assoc_coverage']:.1%}", "",
        "## 名人案例", "",
    ]
    for _, r in celeb_df.iterrows():
        lines.append(f"- **{r['name']}** (ID {r['personid']}): {r['one_liner']}")
    lines += [
        "", "## 已知局限", "",
        "- 傳記為模板拼接，不具備語義理解能力",
        "- 部分人物生卒年、籍貫、身份信息缺失，傳記較短",
        "- 交往對象僅基於 fact_person_assoc，不含親屬關係",
        "- 身份標籤可能存在重疊或類別不平衡的問題",
    ]
    (OUT_DIR / "README.md").write_text("\n".join(lines), encoding="utf-8")


def write_summary(stats):
    summary = {
        "task": "F-2 人物傳記自動生成",
        "data_source": "output_cbdb_v1/",
        "output_dir": str(OUT_DIR.relative_to(ROOT)),
        "scope": "宋代 Top 1000 人物",
        "statistics": stats,
        "output_files": [
            "bio_database.csv", "bio_quality_report.csv",
            "celebrities_bio.csv", "bio_query.html",
            "analysis_summary.json", "README.md",
        ],
    }
    (OUT_DIR / "analysis_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


# ======================================================================
# Main
# ======================================================================

def main():
    print("=== F-2: 人物傳記自動生成 ===\n")

    # --- Load ---
    print("[1/7] 載入資料 ...")
    dim, status, addr, assoc = load_all()
    print(f"  dim_person: {len(dim):,}  status: {len(status):,}"
          f"  addr: {len(addr):,}  assoc: {len(assoc):,}")

    name_to_id, dynasty_of = build_name_indexes(dim)
    print(f"  name_to_id: {len(name_to_id):,}")

    # --- Top 1000 ---
    print("\n[2/7] 計算宋代 Top 1000 ...")
    top1000 = get_song_top_n(dynasty_of, status, addr, assoc, 1000)
    print(f"  -> {len(top1000)} persons")

    # --- Build detailed indexes for targets ---
    celeb_pids = set(CELEB_BY_ID.values())
    for nm in CELEB_BY_NAME:
        if nm in name_to_id:
            celeb_pids.add(name_to_id[nm])
    target_pids = set(top1000) | celeb_pids

    print(f"\n[3/7] Building detailed indexes ({len(target_pids):,} persons) ...")
    person_info = build_person_info(dim, target_pids)
    status_top3 = build_status_top3(status, target_pids)
    addr_top5 = build_addr_top5(addr, target_pids)
    assoc_top5 = build_assoc_top5(assoc, target_pids, name_to_id)
    print(f"  person_info: {len(person_info):,}  status: {len(status_top3):,}"
          f"  addr: {len(addr_top5):,}  assoc: {len(assoc_top5):,}")

    # --- Batch generate ---
    print("\n[4/7] 批量生成傳記 ...")
    df = batch_generate(top1000, person_info, status_top3, addr_top5, assoc_top5)
    df.to_csv(OUT_DIR / "bio_database.csv", index=False, encoding="utf-8-sig")
    print(f"  -> bio_database.csv: {len(df)} entries")

    # --- Quality ---
    print("\n[5/7] 質量評估 ...")
    report_df, stats = quality_assessment(
        df, top1000, person_info, status_top3, addr_top5, assoc_top5)
    report_df.to_csv(OUT_DIR / "bio_quality_report.csv",
                     index=False, encoding="utf-8-sig")
    print(f"  avg one-liner: {stats['avg_one_liner_chars']} chars")
    print(f"  avg bio:       {stats['avg_bio_chars']} chars")
    print(f"  birth cover:   {stats['birth_coverage']:.1%}")
    print(f"  place cover:   {stats['place_coverage']:.1%}")
    print(f"  assoc cover:   {stats['assoc_coverage']:.1%}")

    # --- Celebrities ---
    print("\n[6/7] 名人傳記 ...")
    celeb_df = celebrity_bios(person_info, name_to_id,
                              status_top3, addr_top5, assoc_top5)
    celeb_df.to_csv(OUT_DIR / "celebrities_bio.csv",
                    index=False, encoding="utf-8-sig")
    for _, r in celeb_df.iterrows():
        print(f"  {r['name']}: {r['one_liner']}")

    # --- HTML & docs ---
    print("\n[7/7] 生成文件 ...")
    html = generate_html(df)
    (OUT_DIR / "bio_query.html").write_text(html, encoding="utf-8")
    write_readme(stats, celeb_df)
    write_summary(stats)
    print("  -> bio_query.html, README.md, analysis_summary.json")
    print(f"\n=== DONE ===  output: {OUT_DIR}")


if __name__ == "__main__":
    main()
