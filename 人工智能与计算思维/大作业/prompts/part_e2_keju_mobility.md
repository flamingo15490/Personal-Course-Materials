# 任务 E-2：唐宋科举制度与社会流动性

你是一个 Python 数据分析工程师。请严格按照以下计划实现此专题分析。

## 背景
工作目录：`D:\虚拟C盘\study\人工智能与计算思维大作业`
数据来源：`output_cbdb_v1/` 目录下的已数据化 CSV 文件
输出目录：`任务e/专题2_科举与社会流动/`（自动创建）
脚本路径：`scripts/e2_keju_mobility.py`

已有依赖：networkx、matplotlib、pandas（无需额外安装）

## 专题目标
通过"师生"关系密度、官员籍贯分布、身份类型构成三个维度，量化对比唐/宋两代科举制度对社会结构的影响，验证"科举促进社会流动"这一历史假设。

## 输入数据
- `output_cbdb_v1/fact_person_assoc.csv`：社会关系边表
- `output_cbdb_v1/fact_person_status.csv`：身份维度表（含 c_status_desc_chn）
- `output_cbdb_v1/fact_person_address.csv`：地址经历表（含籍贯信息）
- `output_cbdb_v1/dim_person.csv`：人物主维度

## 实现步骤

### Step 1 — 师生关系密度分析
1. 从 `fact_person_assoc.csv` 筛选关系类型包含"學生"或"門人"或"弟子"的记录
2. 按朝代分组（唐 vs 宋），计算：
   - 师生关系总边数
   - 师生关系占该朝代总社会关系的百分比
   - 有师生关系的人数占该朝代总人数的百分比
   - 平均每位老师的门生数
3. 绘制唐/宋师生关系密度对比图

### Step 2 — 官员籍贯分布分析
1. 从 `fact_person_status.csv` 筛选包含"為官"的身份记录
2. 关联 `fact_person_address.csv` 中 `c_addr_desc_chn == '籍貫(基本地址)'` 获取籍贯
3. 按朝代分组（唐/宋），统计：
   - 官员 Top 20 省份/地区分布
   - 北方 vs 南方官员比例（以秦岭-淮河为界，大约纬度 33°N）
   - 是否存在"某地集中出官员"的现象（基尼系数或 HHI 指数）
4. 绘制唐/宋官员籍贯分布对比图（南方比例变化是核心指标）

### Step 3 — 身份类型构成分析
1. 从 `fact_person_status.csv` 获取身份标签
2. 按朝代分组（唐/宋），统计身份类型分布：
   - 文官 vs 武官比例
   - "科举出身"相关标签的出现频率
   - 身份类型多样性（Shannon 指数）
3. 绘制唐/宋身份类型构成对比堆叠图

### Step 4 — 社会流动性综合指标
1. 定义一个简单的"流动性指数"：
   - 南方官员占比变化（宋 - 唐）
   - 师生关系密度变化
   - 身份多样性变化
2. 将三个指标标准化后取均值
3. 输出综合对比表

### Step 5 — 可视化
1. **师生关系密度对比** `teacher_student_density.png`：
   - 左：唐/宋师生关系绝对数量柱状图
   - 右：师生关系占比（占总社会关系）柱状图

2. **官员籍贯南北分布** `official_origin_ns.png`：
   - 唐/宋两组柱状图，每组分"北方"/"南方"
   - 标注南方占比变化百分比

3. **身份类型构成** `identity_composition.png`：
   - 唐/宋两个饼图或堆叠柱状图，展示 Top 10 身份类型

4. **综合流动性指标** `mobility_index.png`：
   - 雷达图或柱状图，展示三个子指标 + 综合指数

### Step 6 — 输出文件清单
| 文件 | 内容 |
|------|------|
| `teacher_student_density.png` | 师生关系密度对比 |
| `official_origin_ns.png` | 官员籍贯南北分布 |
| `identity_composition.png` | 身份类型构成对比 |
| `mobility_index.png` | 综合流动性指标 |
| `tang_song_comparison.csv` | 唐/宋各项指标对比明细表 |
| `official_origin_detail.csv` | 官员籍贯 Top 20 地区明细 |
| `analysis_summary.json` | 分析摘要 |
| `README.md` | 说明文档（含研究假设、数据发现、结论） |

## 注意事项
1. 路径用 `pathlib.Path`，根目录通过 `Path(__file__).resolve().parents[1]` 获取
2. 中文字体：`plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']`
3. CSV 编码：`utf-8-sig`
4. 籍贯坐标缺失的记录不影响分析（只需省份/地区名称）
5. 南北分界：以纬度 33°N 为近似分界线
6. 写清楚每个指标的计算方法和局限性