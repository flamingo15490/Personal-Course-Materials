# 任务 E-1：宋代文人社交圈与政治命运

你是一个 Python 数据分析工程师。请严格按照以下计划实现此专题分析。

## 背景
工作目录：`D:\虚拟C盘\study\人工智能与计算思维大作业`
数据来源：`output_cbdb_v1/` 目录下的已数据化 CSV 文件
输出目录：`任务e/专题1_宋代文人社交圈/`（自动创建）
脚本路径：`scripts/e1_song_politics.py`

已有依赖：networkx、matplotlib、pandas（无需额外安装）

## 专题目标
聚焦北宋新旧党争时期（约 1050-1100 年），分析以王安石（新党）和司马光/蘇軾（旧党）为核心的社交圈是否在数据上呈现为两个独立社区，量化"政治派系"在社会关系网络中的结构特征。

## 输入数据
- `output_cbdb_v1/fact_person_assoc.csv`：社会关系边表（188,777 行）
- `output_cbdb_v1/fact_person_status.csv`：身份维度表
- `output_cbdb_v1/dim_person.csv`：人物主维度（含朝代、姓名）
- 核心人物 ID（从 dim_person 中按姓名查找）：
  - 王安石、司马光、蘇軾、蘇轍、黃庭堅、秦觀、歐陽修、曾鞏、程顥、程頤、呂惠卿、章惇

## 实现步骤

### Step 1 — 构建宋代社会关系网络
1. 读取 `fact_person_assoc.csv`，筛选 c_personid 在宋代人物集合中的记录
2. 剔除 `c_assoc_desc_chn == '未詳'`
3. 按无向图处理（合并双向边）
4. 读取 `dim_person.csv` 获取姓名映射

### Step 2 — 核心人物社交圈提取
1. 为每位核心人物提取其一度邻居（直接交往对象）和二度邻居（朋友的朋友）
2. 构建"党争核心圈"子图：包含所有核心人物 + 他们的一度邻居
3. 统计每位核心人物的：度数、关系类型分布、与对立阵营的跨阵营连接数

### Step 3 — 社区检测与党派对应分析
1. 在宋代最大连通分量上做 Louvain 社区检测
2. 找到王安石和蘇軾/司马光分别所在的社区
3. 分析：
   - 他们是否在不同社区？
   - 两个社区之间的边密度 vs 社区内部边密度（模块度）
   - 跨阵营连接人物是谁（同时与双方有交往的人）

### Step 4 — 关系类型与政治派系
1. 将关系类型归并为 5 大类（文學交往、墓誌傳記、師生、友人、其他）
2. 分析新党核心圈 vs 旧党核心圈在关系类型分布上的差异
   - 是否一方更多"师生"关系（学术传承型）vs 另一方更多"赠诗"关系（文学交往型）？
3. 跨阵营连接人物的关系类型以什么为主？

### Step 5 — 可视化
1. **党争核心圈网络图** `core_network.png`：
   - 新党人物用红色系，旧党人物用蓝色系
   - 跨阵营连接人物用紫色
   - 节点大小按度数，边粗细按关系类型数量
   - 标注核心人物姓名

2. **社区 vs 党派热力图** `community_party_heatmap.png`：
   - X 轴 = Louvain 社区 Top 10，Y 轴 = 新党/旧党/中立
   - 值 = 该阵营在该社区的人数

3. **关系类型分布对比** `relation_type_comparison.png`：
   - 新党核心圈 vs 旧党核心圈的关系类型分布柱状图

4. **跨阵营人物表** `cross_camp_persons.csv`：
   - 字段：personid, name, degree, new_camp_connections, old_camp_connections, main_relation_types

### Step 6 — 输出文件清单
| 文件 | 内容 |
|------|------|
| `core_network.png` | 党争核心圈网络图 |
| `community_party_heatmap.png` | 社区-党派热力图 |
| `relation_type_comparison.png` | 关系类型分布对比 |
| `cross_camp_persons.csv` | 跨阵营连接人物表 |
| `core_person_stats.csv` | 核心人物统计（度数、关系分布、所属社区） |
| `analysis_summary.json` | 分析摘要（社区数、模块度、核心发现） |
| `README.md` | 说明文档 |

## 注意事项
1. 路径用 `pathlib.Path`，根目录通过 `Path(__file__).resolve().parents[1]` 获取
2. 中文字体：`plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']`
3. CSV 编码：`utf-8-sig`
4. 如果某个核心人物在 dim_person 中找不到（姓名可能有异体字），打印警告并跳过
5. 社区检测使用 `community.louvain_communities(G, seed=42)` 保证可复现
6. 分析结论写入 README.md，不要只输出数据