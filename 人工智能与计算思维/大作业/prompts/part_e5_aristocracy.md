# 任务 E-5：门阀政治的兴衰——魏晋 vs 隋唐

你是一个 Python 数据分析工程师。请严格按照以下计划实现此专题分析。

## 背景
工作目录：`D:\虚拟C盘\study\人工智能与计算思维大作业`
数据来源：`output_cbdb_v1/` 目录下的已数据化 CSV 文件
输出目录：`任务e/专题5_门阀政治/`（自动创建）
脚本路径：`scripts/e5_aristocracy.py`

已有依赖：networkx、matplotlib、pandas（无需额外安装）

## 专题目标
通过亲属关系网络密度、世家大族连通分量、官职集中度等指标，对比魏晋时期（三國/西晉/東晉/南北朝）与隋唐时期的门阀政治结构差异，量化"九品中正制→科举制"转型对权力集中的影响。

## 输入数据
- `output_cbdb_v1/dim_person.csv`：人物主维度（含 dynasty_chn, c_name_chn）
- `output_cbdb_v1/fact_person_kin.csv`：亲属关系表（557,601 行）
- `output_cbdb_v1/fact_person_status.csv`：身份维度表
- `output_cbdb_v1/fact_person_posting.csv`：任官记录表

## 实现步骤

### Step 1 — 朝代分组定义
```python
WEI_JIN_DYNASTIES = ['三國', '西晉', '東晉', '南北朝']
SUI_TANG_DYNASTIES = ['隋', '唐']
```
分别称为"魏晋组"和"隋唐组"。

### Step 2 — 亲属关系网络构建
1. 从 `fact_person_kin.csv` 读取数据，剔除"非可用"和"未詳"
2. 分别筛选两组朝代的人物，构建两个有向亲属网络
3. 转为无向图（亲属关系在结构分析中不考虑方向）进行连通分量分析

### Step 3 — 世家大族结构分析
1. 对两组分别计算：
   - 连通分量数量和大小分布
   - Top 10 大连通分量的大小（即"家族"规模）
   - 最大连通分量的节点数占该朝代总人数的比例（"大家族集中度"）
   - 平均连通分量大小
2. 输出 `family_structure_comparison.csv`

### Step 4 — 官职集中度分析
1. 从 `fact_person_status.csv` 筛选含"為官"的身份记录
2. 按两组朝代分别统计：
   - 有官职记录的人数占总人数比例
   - 在亲属关系最大连通分量中，有官职记录者的比例 vs 整体比例（大家族做官率）
   - 官职类型的多样性（Shannon 指数）
3. 输出 `official_concentration.csv`

### Step 5 — 姓氏集中度
1. 从 `dim_person.csv` 提取姓氏（c_name_chn 的第一个字）
2. 按两组朝代分别统计：
   - Top 20 姓氏的人数占比
   - 姓氏的 HHI（赫芬达尔指数）——衡量"多少姓氏主导了该时期"
   - Top 5 姓氏在最大亲属连通分量中的出现率
3. 输出 `surname_concentration.csv`

### Step 6 — 可视化
1. **家族规模分布** `family_size_distribution.png`：
   - 两个子图（魏晋/隋唐），每个子图为连通分量大小的对数直方图
   - 标注最大连通分量大小

2. **官职集中度对比** `official_concentration.png`：
   - 分组柱状图：大家族做官率 vs 整体做官率，两组朝代各一组

3. **姓氏集中度** `surname_hhi.png`：
   - 柱状图：魏晋/隋唐的 Top 10 姓氏占比
   - 标注 HHI 值

4. **门阀结构总结图** `aristocracy_summary.png`：
   - 雷达图或并排柱状图，展示 4 个指标：最大族规模、大家族做官率、姓氏 HHI、亲属网络密度

### Step 7 — 输出文件清单
| 文件 | 内容 |
|------|------|
| `family_structure_comparison.csv` | 家族结构对比 |
| `official_concentration.csv` | 官职集中度 |
| `surname_concentration.csv` | 姓氏集中度 |
| `family_size_distribution.png` | 家族规模分布 |
| `official_concentration.png` | 官职集中度对比 |
| `surname_hhi.png` | 姓氏集中度 |
| `aristocracy_summary.png` | 门阀结构总结 |
| `analysis_summary.json` | 分析摘要 |
| `README.md` | 说明文档 |

## 注意事项
1. 路径用 `pathlib.Path`，根目录通过 `Path(__file__).resolve().parents[1]` 获取
2. 中文字体：`plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']`
3. CSV 编码：`utf-8-sig`
4. 姓氏提取：取 `c_name_chn` 第一个字符。复姓（如司馬、歐陽）只取第一个字，这会引入少量误差，在 README 中说明
5. 魏晋组包含四个朝代标签，需要合并处理
6. 如果某组数据量太少（如三国可能人少），可适当放宽，但需在 README 中说明数据局限
7. 分析结论写入 README.md，重点讨论：魏晋门阀的家族网络结构 vs 隋唐科举带来的分散化