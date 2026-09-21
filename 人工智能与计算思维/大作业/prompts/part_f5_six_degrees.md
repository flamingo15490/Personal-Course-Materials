# 任务 F-5：中国历史人物的"六度分隔"验证

你是一个 Python 数据分析工程师。请严格按照以下计划实现此专题分析。

## 背景
工作目录：`D:\虚拟C盘\study\人工智能与计算思维大作业`
数据来源：`output_cbdb_v1/` 目录下的已数据化 CSV 文件
输出目录：`任务f/专题5_六度分隔/`（自动创建）
脚本路径：`scripts/f5_six_degrees.py`

已有依赖：networkx、matplotlib、pandas（无需额外安装）

## 专题目标
在 CBDB 社会关系网络上验证"六度分隔"（小世界现象）。计算社交网络的平均路径长度、直径（最长最短路径）、度分布，并抽样计算任意两人之间的最短路径距离分布。同时与等规模随机网络对比，判断 CBDB 社交网络是否具有小世界特征。

## 输入数据
- `output_cbdb_v1/fact_person_assoc.csv`：社会关系边表
- `output_cbdb_v1/fact_person_kin.csv`：亲属关系边表（可选，用于对比）
- `output_cbdb_v1/dim_person.csv`：人物主维度

## 实现步骤

### Step 1 — 构建社会关系网络
1. 读取 `fact_person_assoc.csv`，剔除"未詳"
2. 按无向图处理，去重
3. 构建 NetworkX 图 G_assoc
4. 提取最大连通分量 G_main（小世界分析要求图连通）

### Step 2 — 全局网络指标
对 G_main 计算：
1. 节点数 N、边数 M
2. 密度 density
3. 平均聚类系数（average_clustering）
4. 平均最短路径长度（average_shortest_path_length）——可能很慢，使用近似：随机采样 5000 对节点计算
5. 直径（diameter，即最长最短路径）——使用近似：抽取 200 个随机节点计算 eccentricity 后取 max

### Step 3 — 最短路径距离分布
1. 用 `nx.approximate_current_flow_betweenness_centrality` 或用随机采样法：
   - 采样 5000 对随机节点
   - 计算每对的最短路径长度
2. 统计距离分布：距离 1 到 N 各有多少对
3. 绘制距离分布直方图

### Step 4 — 与随机网络对比（构建零模型）
1. 生成一个与 G_main 同规模（节点数、平均度）的 Erdős–Rényi 随机网络 G_random
2. 生成一个与 G_main 同度序列的配置模型（configuration model）G_config
3. 对比三个网络的：
   - 平均聚类系数
   - 平均最短路径长度
   - 直径

若 G_main 的聚类系数 >> G_random 且平均路径长度 ≈ G_random，则验证了小世界特征。

### Step 5 — 按朝代分组分析
1. 为唐/宋/明分别构建子网的最大连通分量
2. 计算每个朝代的网络指标
3. 输出朝代对比表

### Step 6 — "六度可达"比例
1. 对宋代最大连通分量，随机采样 1000 个起始节点
2. 对每个起始节点，计算"在 6 步内可达的节点比例"
3. 输出平均值和分布

### Step 7 — 具体案例路径
选取 10 对看似无关的历史名人，计算他们的最短路径：
- 蘇軾 → 李清照
- 李白 → 岳飛
- 杜甫 → 袁宏道
- 白居易 → 王維
- 欧阳修 → 王安石
- 及 5 对随机选的人物
- 输出每条路径的完整链路（人名链）到 `path_examples.csv`

### Step 8 — 可视化
1. **距离分布** `shortest_path_distribution.png`：
   - 直方图，X 轴=距离，Y 轴=对数频次
   - 标注均值和中位数

2. **小世界验证** `small_world_verification.png`：
   - 三组并列柱状图（G_main / G_random / G_config）
   - 展示：平均聚类系数、平均路径长度

3. **朝代对比** `dynasty_path_comparison.png`：
   - 柱状图：唐/宋/明的直径和平均路径长度对比

4. **六度可达比例** `six_degree_reach.png`：
   - 累积分布图：X 轴=距离，Y 轴=到该距离时可覆盖的节点比例

### Step 9 — 输出文件清单
| 文件 | 内容 |
|------|------|
| `global_network_metrics.csv` | 全局网络指标 |
| `dynasty_path_stats.csv` | 各朝代路径长度对比 |
| `path_examples.csv` | 名人最短路径案例（含完整链路） |
| `six_degree_reach_stats.csv` | 六度可达统计 |
| `shortest_path_distribution.png` | 距离分布直方图 |
| `small_world_verification.png` | 小世界验证对比图 |
| `dynasty_path_comparison.png` | 朝代路径对比 |
| `six_degree_reach.png` | 六度可达累积图 |
| `analysis_summary.json` | 分析摘要 |
| `README.md` | 说明文档（含方法论、研究假设、结论） |

## 注意事项
1. 路径用 `pathlib.Path`，根目录通过 `Path(__file__).resolve().parents[1]` 获取
2. 中文字体：`plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']`
3. CSV 编码：`utf-8-sig`
4. 全图最短路径计算在 14K 节点上可能很慢（O(N²logN)），务必使用采样近似
5. `nx.average_shortest_path_length(G_main)` 在大图上极慢，用 `nx.approximate_current_flow_betweenness_centrality` 或采样
6. 配置模型生成：`nx.configuration_model(degree_seq)`，注意可能产生自环和多边，用 `nx.Graph(G_config)` 清除
7. 名人路径案例中，如果某对人物在不同连通分量（不可达），标注"不可达"
8. 在 README 中清晰写明：采样方法、样本量、近似方法的误差说明