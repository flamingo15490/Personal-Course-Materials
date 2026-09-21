# 任务 F-1：交互式综合仪表盘

你是一个 Python 数据分析工程师。请严格按照以下计划实现此专题分析。

## 背景
工作目录：`D:\虚拟C盘\study\人工智能与计算思维大作业`
已有产出：`任务b/`、`任务c/`、`任务d/` 下的统计 CSV 和图表
输出目录：`任务f/专题1_综合仪表盘/`（自动创建）
脚本路径：`scripts/f1_dashboard.py`

已有依赖：无需额外安装（用纯 HTML+JS 即可，数据以 JSON 内嵌）

## 专题目标
将 Part B（朝代维度统计）、Part C（迁移地图）、Part D（社交网络）的核心数据整合为一个交互式 HTML 仪表盘。支持：
- 左侧：朝代选择器（下拉框），选择后右侧三个面板同时更新
- 面板 1：该朝代的维度统计（人数、性别比例、Top 5 身份/地址类型）
- 面板 2：该朝代代表性人物的迁移轨迹（复用 Part C 的轨迹数据，但按朝代过滤展示）
- 面板 3：该朝代的社交网络基本指标（节点数、边数、密度、平均度）
- 所有数据预计算为 JSON，内嵌在 HTML 中，无需后端

## 输入数据
- `任务b/person_dynasty_counts.csv`
- `任务b/gender_by_dynasty_counts.csv`
- `任务b/status_by_dynasty_counts.csv`
- `任务b/address_type_by_dynasty_counts.csv`
- `任务c/migration_trajectory_data.csv`
- `任务d/network_global_stats.json`
- `任务d/dynasty_comparison.csv`

## 实现步骤

### Step 1 — 数据预处理与 JSON 生成
1. 读取上述所有输入文件
2. 按朝代（使用 main_dynasty 归并后的名称）聚合统计：
   - 人数、性别分布（男/女/未知占比）
   - Top 5 身份类型及占比
   - Top 5 地址类型及占比
   - 迁移人物数、轨迹点数
   - 社交网络指标（节点数、边数、密度、平均度，从 dynasty_comparison.csv 获取，缺失的标为"无数据"）
3. 将全部数据组织为一个 `dashboard_data` 嵌套字典
4. 生成 `dashboard_data.json`（UTF-8，中文保留）

### Step 2 — 迁移轨迹按朝代筛选
1. 读取 `migration_trajectory_data.csv`
2. 按 `dynasty_chn` 分组，将每个朝代的所有轨迹点导出为独立的 JSON 数组
3. 每个点包含：person_name, event_type, year, place_name, lon, lat

### Step 3 — HTML 仪表盘生成
构建一个单页 HTML，布局如下：

```
┌─────────────────────────────────────────┐
│  CBDB 中国历史人物分析仪表盘              │
│  ┌─ 朝代选择 ──── 当前朝代：唐 ▼ ────┐  │
│  └──────────────────────────────────┘  │
├────────────────┬────────────────┬───────┤
│ ▲ 维度统计     │ ▲ 迁移地图     │▲ 网络  │
│ 人数: XX       │ (Leaflet/     │ 节点: XX│
│ 男/女: XX/XX   │  Plotly地图)  │ 边: XX  │
│ Top 5 身份:    │ 展示唐人物    │ 密度: XX│
│ 1. XXX        │ 迁徙轨迹      │ 平均度:X│
│ 2. XXX        │               │         │
│ ...           │               │         │
├────────────────┴────────────────┴───────┤
│  ▲ 朝代对比总览（唐/宋/元/明/清柱状图）   │
└─────────────────────────────────────────┘
```

技术要求：
- 使用 Leaflet.js（CDN 引用）做地图，复用 Part C 风格（颜色/标记）
- 使用 Chart.js（CDN 引用）做柱状图
- 纯前端 JS，所有数据以 JSON 内嵌或从 JSON 文件加载
- 朝代选择器使用 `<select>` 元素，切换时 JS 更新三个面板
- 底部总览图始终显示所有朝代对比

### Step 4 — Leaflet 地图集成
1. 内嵌 Leaflet CSS/JS CDN
2. 为每个朝代预计算地图中心（该朝代轨迹点的加权中心）
3. 切换朝代时：
   - 清除旧 markers/polylines
   - 添加该朝代所有人物的轨迹线（按人物分色）
   - 添加初始点和终点的特殊标记（★起点，■终点）
   - 自动缩放到合适视野

### Step 5 — Chart.js 图表集成
1. 维度统计面板：显示当前朝代的数值卡片（大字号）+ 2 个饼图（性别、身份 Top 5）
2. 网络面板：显示当前朝代的网络指标卡片 + 与全部朝代的对比条
3. 底部总览：朝代对比柱状图（人数、网络节点数、网络密度）

### Step 6 — 样式设计
- 配色方案：使用柔和的历史感配色（米色/棕色系背景，深色文字）
- 卡片圆角、阴影，现代扁平化设计
- 响应式：三栏在宽屏并排，窄屏堆叠
- 中文字体：Microsoft YaHei / 思源黑体

### Step 7 — 输出文件清单
| 文件 | 内容 |
|------|------|
| `dashboard.html` | 独立可打开的交互式仪表盘 |
| `dashboard_data.json` | 预计算的统计数据（仪表盘数据源） |
| `README.md` | 说明文档（使用方式、数据口径） |

## 注意事项
1. 路径用 `pathlib.Path`，根目录通过 `Path(__file__).resolve().parents[1]` 获取
2. HTML 文件必须自包含（除 CDN 引用外），双击即可打开
3. Leaflet CDN：`https://unpkg.com/leaflet@1.9/dist/leaflet.js`
4. Chart.js CDN：`https://cdn.jsdelivr.net/npm/chart.js`
5. 迁移数据中如果没有坐标的朝代，地图面板显示"该朝代暂无迁移数据"
6. 社交网络数据中如果没有覆盖的朝代，网络面板显示"该朝代暂无网络数据"
7. 确保 JSON 数据量可接受（不嵌入超大数组，用 fetch 加载外部 JSON）