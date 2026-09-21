# -*- coding: utf-8 -*-
"""
F-1: 交互式综合仪表盘
读取 Part B/C/D 的统计 CSV 和 JSON，生成自包含的交互式 HTML 仪表盘。
输出：任务f/专题1_综合仪表盘/ (dashboard.html, dashboard_data.json, README.md)
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IN_B = ROOT / "任务b"
IN_C = ROOT / "任务c"
IN_D = ROOT / "任务d"
OUT_DIR = ROOT / "任务f" / "专题1_综合仪表盘"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── 16 个中国主朝代（时间序） ──
CHINA_DYNASTIES = [
    '先秦', '西漢', '東漢', '三國', '西晉', '東晉',
    '南北朝', '隋', '唐', '五代十國', '南宋', '遼', '金', '元', '明', '清'
]

# ── 朝代映射（复用 Part B 的 DYNASTY_TO_MAIN） ──
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


def map_dynasty(raw: str) -> str:
    """将原始朝代名映射到 main_dynasty"""
    if raw == '未知':
        return '未知'
    return DYNASTY_TO_MAIN.get(raw, '其他')


# ═══════════════════════════════════════════
# Step 1 — 读取输入数据
# ═══════════════════════════════════════════

def read_csv_rows(path: Path) -> list[dict]:
    with path.open('r', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def load_person_counts() -> dict[str, int]:
    """读取 person_main_dynasty_counts.csv → {main_dynasty: count}"""
    rows = read_csv_rows(IN_B / "person_main_dynasty_counts.csv")
    return {r['main_dynasty']: int(r['person_count']) for r in rows}


def load_gender_stats() -> dict[str, dict[str, int]]:
    """读取 gender_by_dynasty_counts.csv → {main_dynasty: {男: n, 女: n, 未知: n}}"""
    result: dict[str, dict[str, int]] = defaultdict(lambda: {'男': 0, '女': 0, '未知': 0})
    for r in read_csv_rows(IN_B / "gender_by_dynasty_counts.csv"):
        d = r['main_dynasty']
        result[d][r['gender']] = int(r['person_count'])
    return dict(result)


def load_status_stats() -> dict[str, list[dict]]:
    """读取 status_by_dynasty_counts.csv → {main_dynasty: [{name, count}, ...]} sorted desc, top 5"""
    bucket: dict[str, list[dict]] = defaultdict(list)
    for r in read_csv_rows(IN_B / "status_by_dynasty_counts.csv"):
        bucket[r['main_dynasty']].append({
            'name': r['status_desc'],
            'count': int(r['fact_count'])
        })
    result = {}
    for dyn, items in bucket.items():
        items.sort(key=lambda x: -x['count'])
        result[dyn] = items[:5]
    return result


def load_address_type_stats() -> dict[str, list[dict]]:
    """读取 address_type_by_dynasty_counts.csv → {main_dynasty: [{name, count}, ...]} top 5"""
    bucket: dict[str, list[dict]] = defaultdict(list)
    for r in read_csv_rows(IN_B / "address_type_by_dynasty_counts.csv"):
        bucket[r['main_dynasty']].append({
            'name': r['address_type_desc'],
            'count': int(r['fact_count'])
        })
    result = {}
    for dyn, items in bucket.items():
        items.sort(key=lambda x: -x['count'])
        result[dyn] = items[:5]
    return result


def load_migration_data() -> dict[str, list[dict]]:
    """
    读取 migration_trajectory_data.csv
    → {main_dynasty: [{person_name, person_id, points: [{event_type, year, place, lon, lat}]}]}
    """
    rows = read_csv_rows(IN_C / "migration_trajectory_data.csv")
    # 按 main_dynasty → person_id → points
    dyn_person: dict[str, dict[str, dict]] = defaultdict(lambda: defaultdict(lambda: {
        'person_name': '', 'person_id': '', 'points': []
    }))
    for r in rows:
        raw_dyn = r.get('dynasty_chn', '').strip()
        main_dyn = map_dynasty(raw_dyn)
        pid = r.get('c_personid', '').strip()
        name = r.get('c_name_chn', '').strip()
        rec = dyn_person[main_dyn][pid]
        rec['person_name'] = name
        rec['person_id'] = pid
        year_raw = r.get('year', '')
        try:
            year_val = float(year_raw) if year_raw else None
        except (ValueError, TypeError):
            year_val = None
        lon_raw = r.get('lon', '')
        lat_raw = r.get('lat', '')
        try:
            lon_val = float(lon_raw) if lon_raw else None
        except (ValueError, TypeError):
            lon_val = None
        try:
            lat_val = float(lat_raw) if lat_raw else None
        except (ValueError, TypeError):
            lat_val = None
        rec['points'].append({
            'event_type': r.get('event_type', ''),
            'year': year_val,
            'place': r.get('place_name', ''),
            'lon': lon_val,
            'lat': lat_val,
        })
    # 转为输出格式
    result: dict[str, list[dict]] = {}
    for dyn, persons in dyn_person.items():
        person_list = []
        for pid, rec in persons.items():
            # 按年份排序
            rec['points'].sort(key=lambda p: (p['year'] if p['year'] is not None else 9999))
            person_list.append({
                'person_name': rec['person_name'],
                'person_id': pid,
                'points': rec['points']
            })
        # 按人名排序保持稳定
        person_list.sort(key=lambda p: p['person_name'])
        result[dyn] = person_list
    return result


def load_network_stats() -> dict[str, dict]:
    """
    读取 dynasty_comparison.csv
    → {main_dynasty: {nodes, edges, density, avg_degree, avg_clustering, components}}
    """
    rows = read_csv_rows(IN_D / "dynasty_comparison.csv")
    result = {}
    for r in rows:
        raw_dyn = r.get('dynasty', '').strip()
        main_dyn = map_dynasty(raw_dyn)
        result[main_dyn] = {
            'nodes': int(r['nodes']),
            'edges': int(r['edges']),
            'density': float(r['density']),
            'avg_degree': float(r['avg_degree']),
            'avg_clustering': float(r['avg_clustering']),
            'components': int(r['components']),
        }
    return result


# ═══════════════════════════════════════════
# Step 2 — 组装 dashboard_data
# ═══════════════════════════════════════════

def build_dashboard_data() -> dict:
    person_counts = load_person_counts()
    gender_stats = load_gender_stats()
    status_stats = load_status_stats()
    addr_stats = load_address_type_stats()
    migration = load_migration_data()
    network = load_network_stats()

    stats = {}
    for dyn in CHINA_DYNASTIES:
        gender = gender_stats.get(dyn, {'男': 0, '女': 0, '未知': 0})
        total = sum(gender.values()) if any(gender.values()) else person_counts.get(dyn, 0)
        stats[dyn] = {
            'person_count': person_counts.get(dyn, total),
            'gender': gender,
            'top5_status': status_stats.get(dyn, []),
            'top5_address_type': addr_stats.get(dyn, []),
        }

    return {
        'dynasties': CHINA_DYNASTIES,
        'stats': stats,
        'migration': migration,
        'network': network,
    }


# ═══════════════════════════════════════════
# Step 3 — 生成 HTML
# ═══════════════════════════════════════════

def generate_html(data: dict) -> str:
    data_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CBDB 中国历史人物分析仪表盘</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9/dist/leaflet.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
:root {{
  --bg: #F5F0E8;
  --card: #FFFFFF;
  --accent: #8B4513;
  --accent-light: #A0522D;
  --text: #2C2C2C;
  --text-light: #666;
  --border: #E0D8CC;
  --shadow: 0 2px 8px rgba(0,0,0,0.10);
  --radius: 8px;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: 'Microsoft YaHei', '思源黑体', 'Noto Sans SC', sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
}}
header {{
  background: linear-gradient(135deg, #5C3317 0%, #8B4513 60%, #A0522D 100%);
  color: #FFF;
  padding: 20px 32px;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 2px;
  text-shadow: 0 1px 3px rgba(0,0,0,0.3);
  display: flex;
  align-items: center;
  gap: 16px;
}}
header .subtitle {{
  font-size: 13px;
  font-weight: 400;
  opacity: 0.85;
  letter-spacing: 0;
}}
#selector-bar {{
  background: var(--card);
  border-bottom: 1px solid var(--border);
  padding: 12px 32px;
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}}
#selector-bar label {{
  font-weight: 600;
  color: var(--accent);
}}
#dynasty-select {{
  padding: 8px 16px;
  border: 2px solid var(--border);
  border-radius: 6px;
  font-size: 15px;
  font-family: inherit;
  background: #FFF;
  cursor: pointer;
  transition: border-color 0.2s;
}}
#dynasty-select:focus {{
  outline: none;
  border-color: var(--accent);
}}
#current-dynasty {{
  font-size: 15px;
  color: var(--text-light);
}}
#current-dynasty strong {{
  color: var(--accent);
  font-size: 17px;
}}
.three-col {{
  display: grid;
  grid-template-columns: 1fr 1.4fr 1fr;
  gap: 16px;
  padding: 16px 32px;
}}
@media (max-width: 960px) {{
  .three-col {{ grid-template-columns: 1fr; }}
}}
.card {{
  background: var(--card);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 20px;
  min-height: 300px;
}}
.card-title {{
  font-size: 16px;
  font-weight: 700;
  color: var(--accent);
  border-bottom: 2px solid var(--border);
  padding-bottom: 8px;
  margin-bottom: 14px;
}}
.big-number {{
  font-size: 32px;
  font-weight: 800;
  color: var(--accent);
  line-height: 1;
}}
.big-number-label {{
  font-size: 12px;
  color: var(--text-light);
  margin-top: 2px;
}}
.stat-cards {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 14px;
}}
.stat-card {{
  background: #FAF7F2;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 10px;
  text-align: center;
}}
.chart-wrap {{
  margin-bottom: 14px;
}}
.chart-wrap canvas {{
  max-height: 180px;
}}
#map-container {{
  height: 420px;
  border-radius: 6px;
  border: 1px solid var(--border);
  position: relative;
}}
.map-overlay {{
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(245,240,232,0.92);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  font-size: 16px;
  color: var(--text-light);
  font-weight: 600;
  border-radius: 6px;
}}
.net-cards {{
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 14px;
}}
.net-card {{
  background: #FAF7F2;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 12px;
  text-align: center;
}}
.net-card .val {{
  font-size: 22px;
  font-weight: 800;
  color: var(--accent);
}}
.net-card .lbl {{
  font-size: 11px;
  color: var(--text-light);
  margin-top: 2px;
}}
.no-data-msg {{
  text-align: center;
  padding: 40px 20px;
  color: var(--text-light);
  font-size: 15px;
}}
.overview-section {{
  padding: 0 32px 24px;
}}
.overview-section .card {{
  min-height: auto;
}}
.overview-section canvas {{
  max-height: 320px;
}}
.leaflet-popup-content {{ font-family: inherit; font-size: 13px; line-height: 1.5; }}
.legend {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; font-size:12px; }}
.legend-item {{ display:flex; align-items:center; gap:4px; }}
.legend-swatch {{ width:14px; height:14px; border-radius:3px; border:1px solid rgba(0,0,0,0.15); }}
</style>
</head>
<body>
<header>
  <span>CBDB 中国历史人物分析仪表盘</span>
  <span class="subtitle">基于中国历代人物传记资料库 Part B/C/D 数据</span>
</header>
<div id="selector-bar">
  <label for="dynasty-select">选择朝代：</label>
  <select id="dynasty-select"></select>
  <span id="current-dynasty">当前朝代：<strong id="dyn-display"></strong></span>
</div>

<div class="three-col">
  <!-- 左：维度统计 -->
  <div class="card" id="stats-panel">
    <div class="card-title">维度统计</div>
    <div id="stats-content"></div>
  </div>
  <!-- 中：迁移地图 -->
  <div class="card" id="map-panel">
    <div class="card-title">迁移轨迹</div>
    <div id="map-container"></div>
    <div id="map-legend" class="legend"></div>
  </div>
  <!-- 右：网络指标 -->
  <div class="card" id="network-panel">
    <div class="card-title">社交网络指标</div>
    <div id="network-content"></div>
  </div>
</div>

<div class="overview-section">
  <div class="card">
    <div class="card-title">朝代对比总览</div>
    <canvas id="overview-chart"></canvas>
  </div>
</div>

<script>
const DATA = {data_json};

// ── 初始化 ──
const select = document.getElementById('dynasty-select');
const dynDisplay = document.getElementById('dyn-display');
DATA.dynasties.forEach(d => {{
  const opt = document.createElement('option');
  opt.value = d; opt.textContent = d;
  select.appendChild(opt);
}});
select.value = DATA.dynasties.indexOf('唐') >= 0 ? '唐' : DATA.dynasties[0];

select.addEventListener('change', () => updateDashboard(select.value));

// ── 地图 ──
const map = L.map('map-container').setView([35, 108], 4);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
  attribution: '&copy; OpenStreetMap',
  maxZoom: 18
}}).addTo(map);
let mapLayers = [];
let mapOverlay = null;

// ── Chart.js 实例（需要销毁重建） ──
let genderChart = null;
let statusChart = null;
let addrChart = null;
let overviewChart = null;

const PERSON_COLORS = [
  '#4C78A8','#F58518','#E45756','#72B7B2','#54A24B',
  '#EECA3B','#B279A2','#FF9DA6','#9D755D','#BAB0AC'
];

// ── 格式化数字 ──
function fmtNum(n) {{
  if (n == null) return '-';
  if (n >= 10000) return (n / 10000).toFixed(1) + '万';
  return n.toLocaleString('zh-CN');
}}

function fmtDensity(n) {{
  if (n == null) return '-';
  return n.toExponential(2);
}}

// ── 更新仪表盘 ──
function updateDashboard(dynasty) {{
  dynDisplay.textContent = dynasty;
  updateStats(dynasty);
  updateMap(dynasty);
  updateNetwork(dynasty);
}}

// ── 维度统计面板 ──
function updateStats(dynasty) {{
  const s = DATA.stats[dynasty];
  if (!s) {{
    document.getElementById('stats-content').innerHTML = '<div class="no-data-msg">该朝代暂无统计数据</div>';
    return;
  }}
  const g = s.gender;
  const total = s.person_count || (g['男'] + g['女'] + g['未知']);

  let html = '<div class="stat-cards">';
  html += '<div class="stat-card"><div class="big-number">' + fmtNum(total) + '</div><div class="big-number-label">总人数</div></div>';
  html += '<div class="stat-card"><div class="big-number">' + fmtNum(g['男']) + '</div><div class="big-number-label">男性</div></div>';
  html += '<div class="stat-card"><div class="big-number">' + fmtNum(g['女']) + '</div><div class="big-number-label">女性</div></div>';
  html += '</div>';
  html += '<div class="chart-wrap"><canvas id="gender-chart"></canvas></div>';
  html += '<div class="chart-wrap"><canvas id="status-chart"></canvas></div>';
  html += '<div class="chart-wrap"><canvas id="addr-chart"></canvas></div>';
  document.getElementById('stats-content').innerHTML = html;

  // 性别饼图
  if (genderChart) genderChart.destroy();
  genderChart = new Chart(document.getElementById('gender-chart'), {{
    type: 'doughnut',
    data: {{
      labels: ['男', '女', '未知'],
      datasets: [{{ data: [g['男'], g['女'], g['未知']],
        backgroundColor: ['#4C78A8','#E45756','#BAB0AC'],
        borderWidth: 1 }}]
    }},
    options: {{
      responsive: true,
      plugins: {{
        legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }},
        title: {{ display: true, text: '性别比例', font: {{ size: 13 }} }}
      }}
    }}
  }});

  // Top 5 身份
  if (statusChart) statusChart.destroy();
  const st = s.top5_status || [];
  statusChart = new Chart(document.getElementById('status-chart'), {{
    type: 'bar',
    data: {{
      labels: st.map(x => x.name),
      datasets: [{{ data: st.map(x => x.count),
        backgroundColor: '#F58518', borderRadius: 3 }}]
    }},
    options: {{
      indexAxis: 'y', responsive: true,
      plugins: {{
        legend: {{ display: false }},
        title: {{ display: true, text: 'Top 5 身份类型', font: {{ size: 13 }} }}
      }},
      scales: {{ x: {{ ticks: {{ font: {{ size: 10 }} }} }}, y: {{ ticks: {{ font: {{ size: 10 }} }} }} }}
    }}
  }});

  // Top 5 地址类型
  if (addrChart) addrChart.destroy();
  const at = s.top5_address_type || [];
  addrChart = new Chart(document.getElementById('addr-chart'), {{
    type: 'bar',
    data: {{
      labels: at.map(x => x.name),
      datasets: [{{ data: at.map(x => x.count),
        backgroundColor: '#72B7B2', borderRadius: 3 }}]
    }},
    options: {{
      indexAxis: 'y', responsive: true,
      plugins: {{
        legend: {{ display: false }},
        title: {{ display: true, text: 'Top 5 地址类型', font: {{ size: 13 }} }}
      }},
      scales: {{ x: {{ ticks: {{ font: {{ size: 10 }} }} }}, y: {{ ticks: {{ font: {{ size: 10 }} }} }} }}
    }}
  }});
}}

// ── 迁移地图 ──
function updateMap(dynasty) {{
  // 清除旧图层
  mapLayers.forEach(l => map.removeLayer(l));
  mapLayers = [];
  if (mapOverlay) {{ mapOverlay.remove(); mapOverlay = null; }}
  document.getElementById('map-legend').innerHTML = '';

  const mig = DATA.migration[dynasty];
  if (!mig || mig.length === 0) {{
    mapOverlay = document.createElement('div');
    mapOverlay.className = 'map-overlay';
    mapOverlay.textContent = '该朝代暂无迁移数据';
    document.getElementById('map-container').appendChild(mapOverlay);
    return;
  }}

  const allBounds = [];
  let legendHtml = '';

  mig.forEach((person, i) => {{
    const color = PERSON_COLORS[i % PERSON_COLORS.length];
    const pts = person.points.filter(p => p.lon != null && p.lat != null);
    if (pts.length === 0) return;

    // 轨迹线
    const latlngs = pts.map(p => [p.lat, p.lon]);
    const polyline = L.polyline(latlngs, {{ color: color, weight: 2.5, opacity: 0.8 }});
    polyline.addTo(map);
    mapLayers.push(polyline);

    // 起点 ★
    const start = pts[0];
    const startMarker = L.circleMarker([start.lat, start.lon], {{
      radius: 8, fillColor: color, color: '#FFF', weight: 2,
      fillOpacity: 1
    }}).addTo(map);
    startMarker.bindPopup(
      '<b>' + person.person_name + '</b> — 起点<br>' +
      start.event_type + ' · ' + (start.year ? Math.round(start.year) : '?') + '年<br>' + start.place
    );
    mapLayers.push(startMarker);

    // 终点 ■（用方形 marker）
    if (pts.length > 1) {{
      const end = pts[pts.length - 1];
      const endMarker = L.circleMarker([end.lat, end.lon], {{
        radius: 6, fillColor: color, color: '#333', weight: 2,
        fillOpacity: 0.9
      }}).addTo(map);
      endMarker.bindPopup(
        '<b>' + person.person_name + '</b> — 终点<br>' +
        end.event_type + ' · ' + (end.year ? Math.round(end.year) : '?') + '年<br>' + end.place
      );
      mapLayers.push(endMarker);
    }}

    // 途经点
    for (let j = 1; j < pts.length - 1; j++) {{
      const p = pts[j];
      const m = L.circleMarker([p.lat, p.lon], {{
        radius: 3, fillColor: color, color: '#FFF', weight: 1, fillOpacity: 0.7
      }}).addTo(map);
      m.bindPopup(
        '<b>' + person.person_name + '</b><br>' +
        p.event_type + ' · ' + (p.year ? Math.round(p.year) : '?') + '年<br>' + p.place
      );
      mapLayers.push(m);
    }}

    latlngs.forEach(ll => allBounds.push(ll));
    legendHtml += '<div class="legend-item"><div class="legend-swatch" style="background:' + color + '"></div>' + person.person_name + '</div>';
  }});

  document.getElementById('map-legend').innerHTML = legendHtml;
  if (allBounds.length > 0) {{
    map.fitBounds(allBounds, {{ padding: [30, 30] }});
  }}
}}

// ── 网络指标面板 ──
function updateNetwork(dynasty) {{
  const nw = DATA.network[dynasty];
  const container = document.getElementById('network-content');
  if (!nw) {{
    container.innerHTML = '<div class="no-data-msg">该朝代暂无网络数据</div>';
    return;
  }}
  let html = '<div class="net-cards">';
  html += '<div class="net-card"><div class="val">' + fmtNum(nw.nodes) + '</div><div class="lbl">节点数</div></div>';
  html += '<div class="net-card"><div class="val">' + fmtNum(nw.edges) + '</div><div class="lbl">边数</div></div>';
  html += '<div class="net-card"><div class="val">' + fmtDensity(nw.density) + '</div><div class="lbl">密度</div></div>';
  html += '<div class="net-card"><div class="val">' + nw.avg_degree.toFixed(2) + '</div><div class="lbl">平均度</div></div>';
  html += '</div>';
  html += '<div class="chart-wrap"><canvas id="net-compare-chart"></canvas></div>';
  container.innerHTML = html;

  // 与全部朝代的对比
  const netDynasties = Object.keys(DATA.network);
  const netNodes = netDynasties.map(d => DATA.network[d].nodes);
  const highlightColors = netDynasties.map(d => d === dynasty ? '#8B4513' : '#D7C4A5');
  new Chart(document.getElementById('net-compare-chart'), {{
    type: 'bar',
    data: {{
      labels: netDynasties,
      datasets: [{{
        label: '网络节点数',
        data: netNodes,
        backgroundColor: highlightColors,
        borderRadius: 3
      }}]
    }},
    options: {{
      responsive: true,
      plugins: {{
        legend: {{ display: false }},
        title: {{ display: true, text: '已有网络数据朝代对比', font: {{ size: 12 }} }}
      }},
      scales: {{ y: {{ ticks: {{ font: {{ size: 10 }} }} }}, x: {{ ticks: {{ font: {{ size: 10 }} }} }} }}
    }}
  }});
}}

// ── 底部总览图 ──
function buildOverviewChart() {{
  const dyns = DATA.dynasties;
  const personCounts = dyns.map(d => DATA.stats[d].person_count || 0);
  const netNodes = dyns.map(d => DATA.network[d] ? DATA.network[d].nodes : 0);

  overviewChart = new Chart(document.getElementById('overview-chart'), {{
    type: 'bar',
    data: {{
      labels: dyns,
      datasets: [
        {{
          label: '人物数量',
          data: personCounts,
          backgroundColor: '#4C78A8',
          borderRadius: 3,
          yAxisID: 'y'
        }},
        {{
          label: '网络节点数',
          data: netNodes,
          backgroundColor: '#F58518',
          borderRadius: 3,
          yAxisID: 'y1'
        }}
      ]
    }},
    options: {{
      responsive: true,
      interaction: {{ mode: 'index', intersect: false }},
      plugins: {{
        legend: {{ position: 'top' }},
        title: {{ display: true, text: '各朝代人物数量与网络节点数对比', font: {{ size: 14 }} }}
      }},
      scales: {{
        y: {{
          type: 'linear', position: 'left',
          title: {{ display: true, text: '人物数量' }},
          ticks: {{ font: {{ size: 10 }} }}
        }},
        y1: {{
          type: 'linear', position: 'right',
          title: {{ display: true, text: '网络节点数' }},
          grid: {{ drawOnChartArea: false }},
          ticks: {{ font: {{ size: 10 }} }}
        }},
        x: {{ ticks: {{ font: {{ size: 10 }}, maxRotation: 45 }} }}
      }}
    }}
  }});
}}

// ── 启动 ──
updateDashboard(select.value);
buildOverviewChart();
</script>
</body>
</html>'''


# ═══════════════════════════════════════════
# Step 4 — 生成 README
# ═══════════════════════════════════════════

def generate_readme() -> str:
    return '''# 专题1：交互式综合仪表盘

## 使用方式
1. 直接双击 `dashboard.html` 即可在浏览器中打开仪表盘
2. 使用顶部下拉框选择朝代，三个面板会同步更新
3. 地图支持缩放和拖拽，点击轨迹点可查看详情

## 文件说明
| 文件 | 说明 |
|------|------|
| `dashboard.html` | 自包含交互式仪表盘（需联网加载 Leaflet/Chart.js CDN） |
| `dashboard_data.json` | 预计算的 JSON 数据源（供参考或复用） |
| `README.md` | 本文档 |

## 数据来源
- **维度统计**：Part B (`任务b/`) — 朝代人数、性别、身份、地址类型
- **迁移轨迹**：Part C (`任务c/`) — 8 位代表性人物的迁徙路线
- **社交网络**：Part D (`任务d/`) — 唐/宋/明三朝的社会网络指标

## 数据口径
- 朝代使用 `main_dynasty` 归并后名称（如"宋"→"南宋"），映射规则复用 Part B 的 `DYNASTY_TO_MAIN`
- 16 个中国主朝代（时间序）：先秦→西漢→東漢→三國→西晉→東晉→南北朝→隋→唐→五代十國→南宋→遼→金→元→明→清
- 无迁移数据的朝代：地图面板显示"暂无迁移数据"
- 无网络数据的朝代：网络面板显示"暂无网络数据"
- 迁移数据仅覆盖唐、南宋、明三个朝代（8 位人物）
- 网络数据仅覆盖唐、南宋、明三个朝代

## 技术栈
- [Leaflet.js v1.9](https://leafletjs.com/) — 交互式地图
- [Chart.js](https://www.chartjs.org/) — 图表渲染
- 纯前端实现，无需后端服务
'''


# ═══════════════════════════════════════════
# Main
# ═══════════════════════════════════════════

def main():
    print("[F1] 读取输入数据...")
    data = build_dashboard_data()

    print(f"[F1] 生成 dashboard_data.json ({len(data['dynasties'])} 个朝代)...")
    json_path = OUT_DIR / "dashboard_data.json"
    with json_path.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  → {json_path} ({json_path.stat().st_size / 1024:.1f} KB)")

    print("[F1] 生成 dashboard.html...")
    html = generate_html(data)
    html_path = OUT_DIR / "dashboard.html"
    with html_path.open('w', encoding='utf-8') as f:
        f.write(html)
    print(f"  → {html_path} ({html_path.stat().st_size / 1024:.1f} KB)")

    print("[F1] 生成 README.md...")
    readme_path = OUT_DIR / "README.md"
    with readme_path.open('w', encoding='utf-8') as f:
        f.write(generate_readme())
    print(f"  → {readme_path}")

    # 验证
    print("\n[F1] 数据验证:")
    print(f"  朝代数量: {len(data['dynasties'])}")
    print(f"  有迁移数据的朝代: {list(data['migration'].keys())}")
    print(f"  有网络数据的朝代: {list(data['network'].keys())}")
    for dyn in ['唐', '南宋', '明']:
        s = data['stats'][dyn]
        print(f"  [{dyn}] 人数={s['person_count']}, 性别={s['gender']}")
        if dyn in data['migration']:
            persons = [p['person_name'] for p in data['migration'][dyn]]
            print(f"  [{dyn}] 迁移人物: {persons}")
        if dyn in data['network']:
            nw = data['network'][dyn]
            print(f"  [{dyn}] 网络: 节点={nw['nodes']}, 边={nw['edges']}")

    print("\n[F1] 完成！")


if __name__ == '__main__':
    main()

