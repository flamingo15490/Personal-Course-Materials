# 任务 F-8：历史人物"影响力指数"

你是一个 Python 数据分析工程师。请严格按照以下计划实现此专题分析。

## 背景
工作目录：`D:\虚拟C盘\study\人工智能与计算思维大作业`
数据来源：`output_cbdb_v1/` 目录下的已数据化 CSV 文件
输出目录：`任务f/专题8_影响力指数/`（自动创建）
脚本路径：`scripts/f8_influence_index.py`

已有依赖：networkx、matplotlib、pandas（无需额外安装）

## 专题目标
综合社交网络中心性、关系类型丰富度、活动地广度、身份多样性、后世记载频次，设计一个加权的"历史人物影响力指数"，排名 Top 200，并与公众认知（如中小学课本出现频次）做定性对比。

## 输入数据
- `output_cbdb_v1/fact_person_assoc.csv`：社会关系边表
- `output_cbdb_v1/fact_person_status.csv`：身份维度表
- `output_cbdb_v1/fact_person_address.csv`：地址经历表
- `output_cbdb_v1/fact_person_kin.csv`：亲属关系表
- `output_cbdb_v1/dim_person.csv`：人物主维度

## 影响力指数设计

### 子指标（5 个维度）

**A. 社交网络中心性（权重 30%）**
- PageRank（在无向社会关系网络 G_assoc 上计算）
- 归一化到 [0, 1]

**B. 关系多样性（权重 20%）**
- 社会关系类型的 Shannon 多样性指数（= 1 减去基尼系数）
- 关系大类数（文学交往/墓志/师生/友人/其他，5 类中覆盖了几类）
- 归一化到 [0, 1]

**C. 空间活动广度（权重 20%）**
- 活动地点数量（从地址经历表统计）
- 活动地经纬度覆盖范围的面积（纬度跨度 × 经度跨度，度数乘积）
- 归一化到 [0, 1]

**D. 身份多重性（权重 15%）**
- 身份标签种类数（从身份维度表统计）
- 归一化到 [0, 1]

**E. 文献记载量（权重 15%）**
- 社会关系表中该人物的 source/pages 记录频次（作为"被文献引用量"的代理变量）
- 归一化到 [0, 1]

### 综合影响力指数
```
Influence = 0.30×A + 0.20×B + 0.20×C + 0.15×D + 0.15×E
```
取值范围 [0, 1]，保留 4 位小数。

## 实现步骤

### Step 1 — 数据加载与索引
1. 读取所有输入 CSV
2. 构建 G_assoc 无向图（剔除"未詳"）
3. 建立每个人的快速查询索引

### Step 2 — 子指标计算

**A. 社交网络中心性**
1. 在 G_assoc 上计算 PageRank (`nx.pagerank(G_assoc)`)
2. 归一化：`A = (pr_val - min) / (max - min)`
3. 只对在 G_assoc 中有至少一条边的人物计算，孤立人物 A=0

**B. 关系多样性**
1. 统计每人涉及的 `c_assoc_desc_chn` 种类数 n_types
2. 统计覆盖关系大类数（5 类中几类）
3. 多样性 = `count_unique_types / max_unique_types`（归一化）
4. 最终 B = (多样性 + 大类覆盖率) / 2

**C. 空间活动广度**
1. 从地址经历表统计每人的唯一地名数
2. 计算每人的经纬度跨度：`lat_span = max_lat - min_lat`（单位：度）
3. 面积代理：`lat_span × lon_span`（处理 0 的情况）
4. 归一化到 [0, 1]

**D. 身份多重性**
1. 统计每人身份标签种类数
2. 归一化：`D = count / max_count`

**E. 文献记载量**
1. 统计每人在社会关系和亲属关系中被引用的 source 记录数
2. 归一化：`E = count / max_count`

### Step 3 — 综合指数计算与排名
1. 计算所有 658,941 人的综合影响力指数
2. 按 influence 降序排列
3. 输出 Top 200 到 `influence_top200.csv`
4. 输出全量指数到 `influence_all.csv`（只包含有至少一个非零子指标的人物，约 50K 人）

### Step 4 — 朝代分布分析
1. 按朝代统计 Top 200 人物的分布
2. 与各朝代总人数占比对比（标准化后）：哪个朝代"超产"了 Top 200 名人？
3. 输出 `influence_by_dynasty.csv`

### Step 5 — 与公众认知对比
1. 准备一个课本高频人物列表（手动列出 50 位中小学语文/历史课本常见人物）
   包括：孔子、孟子、荀子、老子、庄子、孫子、屈原、秦始皇、項羽、劉邦、張良、韓信、司馬遷、諸葛亮、曹操、關羽、劉備、孫權、王羲之、陶淵明、李白、杜甫、白居易、王維、韓愈、柳宗元、蘇軾、歐陽修、王安石、司馬光、范仲淹、辛棄疾、陸游、李清照、岳飛、文天祥、鄭和、王陽明、曹雪芹、吳承恩等
2. 查找这些课本人物在 CBDB 中的影响力排名
3. 输出 `textbook_vs_cbdb.csv`（字段：name, cbdb_rank, cbdb_influence, in_textbook_top50）
4. 分析：CBDB 中排名高但课本中不常见的"被低估"人物、课本中高频但 CBDB 中排名低的"被高估"人物

### Step 6 — 可视化
1. **Top 50 影响力人物** `influence_top50_bar.png`：
   - 水平柱状图，Y 轴=姓名，X 轴=影响力指数
   - 分段着色（5 个子指标颜色叠加）

2. **子指标相关性** `sub_index_correlation.png`：
   - 5×5 子指标散点图矩阵（散点+回归线+相关系数）
   - 看哪些维度高度相关（如空间广度和关系多样性可能正相关）

3. **朝代影响力分布** `influence_by_dynasty.png`：
   - 分组柱状图：各朝代在 Top 200 中的占比 vs 总人数占比
   - 标注"超产"和"欠产"朝代

4. **课本 vs CBDB 对比** `textbook_vs_cbdb.png`：
   - 散点图：X 轴=CBDB 影响力排名，Y 轴=课本人物标记（二分类用不同颜色）
   - 标注"被低估"和"被高估"的极端人物

### Step 7 — 输出文件清单
| 文件 | 内容 |
|------|------|
| `influence_top200.csv` | Top 200 影响力人物（含 5 个子指标） |
| `influence_all.csv` | 全量影响力指数（约 50K 人） |
| `influence_by_dynasty.csv` | 朝代影响力分布 |
| `textbook_vs_cbdb.csv` | 课本人物 CBDB 排名对比 |
| `influence_top50_bar.png` | Top 50 影响力柱状图 |
| `sub_index_correlation.png` | 子指标相关性矩阵 |
| `influence_by_dynasty.png` | 朝代影响力分布 |
| `textbook_vs_cbdb.png` | 课本 vs CBDB 散点图 |
| `analysis_summary.json` | 分析摘要（含 Top 10、权重设定、关键发现） |
| `README.md` | 说明文档（含权重选择理由、方法论局限） |

## 注意事项
1. 路径用 `pathlib.Path`，根目录通过 `Path(__file__).resolve().parents[1]` 获取
2. 中文字体：`plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']`
3. CSV 编码：`utf-8-sig`
4. PageRank 在 14K 节点网络上很快，无需采样
5. 归一化的 min/max 使用所有非零值的最小/最大，避免孤立人物拉低分布
6. 子指标计算中，空值统一为 0
7. 课本人物列表如部分在 CBDB 中找不到（如古代传说人物），标注"不在 CBDB 中"
8. 在 README 中写清楚：权重的选择是主观的（基于专家判断），可调整为论文需要
9. 影响力指数的局限性：CBDB 数据偏文人/官员，武将、商人、工匠等系统性遗漏