# 中国历代人物传记数据库（CBDB）数据分析作业

> 仓库版本不包含 `latest/cbdb_20260606.sqlite3` 原始数据库（约 550 MB，超过 GitHub 单文件大小限制），也不包含 Python `__pycache__` 缓存。要重新运行数据构建脚本，请从 [CBDB 官网](https://projects.iq.harvard.edu/cbdb) 获取相应版本数据库并放入 `latest/`；仓库中保留了分析代码、已生成的维度表、图表和可视化页面。

## 项目概述
基于 Harvard University 中国历代人物传记数据库（CBDB）的数据，对中国历史人物进行多维度数据化分析。涵盖数据化处理、维度统计、地理迁徙、社会化网络、专题深入分析和创新应用六个层面，使用 Python（pandas / NetworkX / matplotlib / folium / pyvis）完成数据处理、统计分析与可视化。

## 数据来源
- 数据库版本：`cbdb_20260606.sqlite3`（约 550MB）
- 数据来源：[CBDB 官网](https://projects.iq.harvard.edu/cbdb)
- 核心规模：658,941 位历史人物，覆盖先秦至清代

## 作业结构与完成情况

### A. 数据化与数据存储方式说明

将 CBDB 的 SQLite 关系型数据库转化为 CSV 数据集，以蘇軾/安惇为案例说明数据化方法。

**产出：**
- `output_cbdb_v1/` — 7 张 CSV 维度表 + 数据字典
- `数据化和数据存储方式说明.md` — 数据化方法说明文档

**核心 CSV：**

| 文件 | 内容 | 行数 |
|------|------|------|
| `dim_person.csv` | 人物主维度（姓名/朝代/生卒年/籍贯/坐标） | 659,183 |
| `dim_address.csv` | 地址主维度（含坐标） | 30,100 |
| `fact_person_status.csv` | 身份维度（文官/诗人/画家等） | 71,745 |
| `fact_person_address.csv` | 地址经历（籍贯/迁住地/游历等） | 458,403 |
| `fact_person_posting.csv` | 任官与驻地 | 589,875 |
| `fact_person_kin.csv` | 亲属关系边表 | 557,907 |
| `fact_person_assoc.csv` | 社会关系边表 | 189,297 |

---

### B. 历史人物的维度与各朝代数量分布

以朝代为核心维度，统计人物属性（性别/身份/地址类型）在各朝代的分布。排除非中国政权（朝鲜、高丽等），保留"未知"类目。

**产出目录：** `任务b/`
- 5 张统计 CSV（朝代总量、身份×朝代、地址×朝代、性别×朝代）
- 6 张可贴论文的图表（柱状图、堆叠图、百分比图）
- `README.md` — 维度定义与口径说明

**核心发现：** 清 (236K) > 明 (225K) > 宋 (83K) > 唐 (57K) > 元 (25K)，宋清两代记录最丰富。

---

### C. 地图上呈现历史人物的迁移关系

选取 8 位跨唐/宋/明名人（李白、杜甫、白居易、王维、蘇軾、岳飛、李清照、袁宏道），从地址经历表和任官表提取 218 个轨迹点，在地图上可视化其一生迁移路径。

**产出目录：** `任务c/`
- `migration_trajectory_data.csv` — 轨迹明细（218 行）
- `migration_summary.csv` — 人物摘要
- `migration_map.html` — 交互式 Folium 地图（可缩放、点击查看详情）
- `migration_map_static.png` — 静态迁移总图
- `migration_by_dynasty.png` — 按朝代分组图
- `README.md` — 数据说明

---

### D. 社会化网络研究

构建社会关系网络（44,352 节点、74,365 边）和亲属关系网络（284,967 节点、555,863 边），进行全局分析、朝代对比、社区检测和名人自我中心网探索。

**产出目录：** `任务d/`
- `network_global_stats.json` — 全局指标（密度/聚类系数/连通分量）
- `dynasty_comparison.csv` — 唐/宋/明三代网络指标对比
- `top_central_persons.csv` — 宋代中心性 Top 50
- `network_song_full.html` — 宋代全量交互式网络图（pyvis，可缩放/拖拽/高亮邻居）
- `ego_pages/` — 50 个核心人物的独立交互式自我中心网页面（支持点击跳转）
- `ego_sushi_network.png` — 蘇軾社交圈静态图
- 度分布图、朝代对比图、亲属关系度分布图
- `README.md` — 分析说明

**核心发现：**
- 全局平均最短路径 5.76，宋代 4.07 — 具有小世界特征
- 宋代社交网络检测出 26 个社区，模块度 0.66
- 唐→宋→明社交网络密度逐步降低，但平均度上升

---

### E. 专题深入分析（6 个专题并行完成）

| 专题 | 目录 | 核心问题 |
|------|------|----------|
| E-1 宋代文人社交圈与政治命运 | `任务e/专题1_宋代文人社交圈/` | 新旧党争是否在社交网络中形成独立社区？ |
| E-2 唐宋科举制度与社会流动性 | `任务e/专题2_科举与社会流动/` | 科举如何改变了官员籍贯分布和身份构成？ |
| E-3 中国古代女性人物的时空分布 | `任务e/专题3_女性人物/` | 女性记录从"附属身份"到"独立记录"的演变 |
| E-4 明清人口大迁徙与文化重心南移 | `任务e/专题4_文化重心南移/` | 南方文化主导地位如何逐步确立？ |
| E-5 门阀政治的兴衰——魏晋 vs 隋唐 | `任务e/专题5_门阀政治/` | 科举制如何瓦解了世家大族的权力结构？ |
| E-6 文学群体的地理集聚 | `任务e/专题6_文学地理/` | 文学中心从长安到江南的迁移路径 |

每个专题均包含：统计 CSV、分析图表、分析摘要 JSON、README 说明文档。

---

### F. 创新应用（4 个方向并行完成）

| 应用 | 目录 | 内容 |
|------|------|------|
| F-1 综合仪表盘 | `任务f/专题1_综合仪表盘/` | 整合 B/C/D 分析结果的交互式 HTML 仪表盘，可切换朝代联动展示 |
| F-2 人物传记自动生成 | `任务f/专题2_人物传记/` | 基于结构化数据自动生成人物简介，含在线查询页面 |
| F-5 六度分隔验证 | `任务f/专题5_六度分隔/` | 验证历史人物社交网络的小世界特性，平均路径 5.76 步 |
| F-8 历史人物影响力指数 | `任务f/专题8_影响力指数/` | 综合 PageRank/关系多样性/地理范围/身份/被引用频次的加权指数，Top 1：朱熹 |

**影响力 Top 5：** 朱熹 > 李白 > 蘇軾 > 王安石 > 宋濂

---

## 目录结构

```
人工智能与计算思维大作业/
├── README.md                          ← 本文件
├── 作业要求.txt                        ← 原始作业要求
├── 数据化和数据存储方式说明.md            ← A 问说明文档
│
├── latest/
│   └── cbdb_20260606.sqlite3          ← CBDB 原始数据库
│
├── output_cbdb_v1/                    ← A 问：数据化 CSV
│   ├── dim_person.csv
│   ├── dim_address.csv
│   ├── fact_person_status.csv
│   ├── fact_person_address.csv
│   ├── fact_person_posting.csv
│   ├── fact_person_kin.csv
│   ├── fact_person_assoc.csv
│   └── data_dictionary.csv
│
├── 任务b/                             ← B 问：维度与分布
│   ├── README.md
│   ├── *.csv (5 files)
│   └── charts/*.png (6 files)
│
├── 任务c/                             ← C 问：迁移地图
│   ├── README.md
│   ├── migration_map.html             ← 交互式地图
│   ├── migration_map_static.png
│   ├── migration_by_dynasty.png
│   └── migration_*.csv (2 files)
│
├── 任务d/                             ← D 问：社会化网络
│   ├── README.md
│   ├── network_song_full.html         ← 宋代交互式网络
│   ├── ego_pages/*.html (50 files)    ← 可钻取的自我中心网
│   ├── network_global_stats.json
│   └── *.csv, *.png (multiple)
│
├── 任务e/                             ← E 问：6 个专题
│   ├── 专题1_宋代文人社交圈/
│   ├── 专题2_科举与社会流动/
│   ├── 专题3_女性人物/
│   ├── 专题4_文化重心南移/
│   ├── 专题5_门阀政治/
│   └── 专题6_文学地理/
│
├── 任务f/                             ← F 问：4 个创新应用
│   ├── 专题1_综合仪表盘/
│   ├── 专题2_人物传记/
│   ├── 专题5_六度分隔/
│   └── 专题8_影响力指数/
│
├── scripts/                           ← 所有生成脚本
│   ├── build_cbdb_dataset.py          ← A 问：数据化脚本
│   ├── b_analysis_and_viz.py          ← B 问
│   ├── c_migration_map.py             ← C 问
│   ├── d_social_network.py            ← D 问
│   ├── e1_song_politics.py            ← E-1
│   ├── e2_keju_mobility.py            ← E-2
│   ├── e3_female_analysis.py          ← E-3
│   ├── e4_cultural_south_shift.py     ← E-4
│   ├── e5_aristocracy.py              ← E-5
│   ├── e6_literary_geography.py       ← E-6
│   ├── f1_dashboard.py                ← F-1
│   ├── f2_bio_generator.py            ← F-2
│   ├── f5_six_degrees.py              ← F-5
│   └── f8_influence_index.py          ← F-8
│
├── prompts/                           ← 子进程 prompt 文件（已执行完毕）
│
└── lib/                               ← 前端依赖（vis.js / tom-select）
```

## 环境依赖

- Python 3.12+
- pandas, networkx, matplotlib, folium, pyvis, jinja2
- 操作系统：Windows（中文字体 Microsoft YaHei / SimHei）

## 使用说明

**一键复现单个任务：**
```bash
python scripts/build_cbdb_dataset.py      # A 问
python scripts/b_analysis_and_viz.py      # B 问
python scripts/c_migration_map.py         # C 问
python scripts/d_social_network.py        # D 问（较慢，约 5-10 分钟）
python scripts/e1_song_politics.py        # E-1
# ... 以此类推
```

**交互式页面直接打开：**
- `任务c/migration_map.html` — 需联网（加载 OpenStreetMap 底图）
- `任务d/network_song_full.html` — 完全离线可用
- `任务d/ego_pages/*.html` — 完全离线可用
- `任务f/专题1_综合仪表盘/dashboard.html` — 完全离线可用
- `任务f/专题2_人物传记/bio_query.html` — 完全离线可用

## 数据口径与已知限制

- 朝代 `未詳` 归入"未知"类目，不丢弃
- 坐标缺失（值为 0 或空）不影响主维度分析，仅影响地图子集
- 社会关系 99.99% 双向对称，按无向图处理
- 影响力指数为加权模型，权重设定有主观性，详见各专题 README
- 先秦/秦代数据稀少，相关统计仅供参考
- CBDB 数据以宋明清为主，唐代以前覆盖较薄
