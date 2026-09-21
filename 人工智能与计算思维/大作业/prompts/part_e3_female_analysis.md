# 任务 E-3：中国古代女性人物的时空分布

你是一个 Python 数据分析工程师。请严格按照以下计划实现此专题分析。

## 背景
工作目录：`D:\虚拟C盘\study\人工智能与计算思维大作业`
数据来源：`output_cbdb_v1/` 目录下的已数据化 CSV 文件
输出目录：`任务e/专题3_女性人物/`（自动创建）
脚本路径：`scripts/e3_female_analysis.py`

已有依赖：matplotlib、pandas（无需额外安装）

## 专题目标
从性别维度切入，分析中国古代女性人物在各朝代的数量变化、地理分布、身份类型（节妇/孝女/才女/女官等）演变，以及女性在亲属关系和社会关系网络中的角色特征。

## 输入数据
- `output_cbdb_v1/dim_person.csv`：人物主维度（含 c_female, dynasty_chn, index_addr_chn 等）
- `output_cbdb_v1/fact_person_status.csv`：身份维度表
- `output_cbdb_v1/fact_person_address.csv`：地址经历表
- `output_cbdb_v1/fact_person_kin.csv`：亲属关系表
- `output_cbdb_v1/fact_person_assoc.csv`：社会关系表

## 实现步骤

### Step 1 — 女性人物基本统计
1. 从 `dim_person.csv` 筛选 `c_female == 1` 的记录
2. 按朝代统计女性人数，计算：
   - 各朝代女性总人数
   - 女性占该朝代总人数的百分比
   - 女性占比的变化趋势
3. 输出 `female_dynasty_stats.csv`

### Step 2 — 女性身份类型分析
1. 将女性人物与 `fact_person_status.csv` 关联
2. 按朝代分组，统计女性身份类型 Top 10：
   - 是否从早期的"节妇/孝女/烈女"（附属身份）逐渐出现"诗人/画家/学者"（独立身份）？
   - 各朝代女性身份类型的 Shannon 多样性指数
3. 输出 `female_status_by_dynasty.csv`

### Step 3 — 女性地理分布
1. 关联 `fact_person_address.csv` 中的籍贯信息
2. 按朝代统计女性籍贯 Top 10 地区
3. 计算各朝代女性地理分布的集中度（HHI 指数）
4. 分析是否有特定地区（如江南）更集中地出现女性人物

### Step 4 — 女性在亲属关系中的角色
1. 从 `fact_person_kin.csv` 提取涉及女性的记录（作为 c_personid 或 c_kin_id 出现）
2. 统计女性最常见的亲属关系类型：
   - 作为"母亲""妻子""女儿"出现的频率
   - 是否有"姐妹""姑""姨"等更广泛的角色
3. 按朝代看女性亲属角色的变化

### Step 5 — 女性社会关系
1. 从 `fact_person_assoc.csv` 筛选涉及女性人物（c_personid 或 c_assoc_id 为女性）的记录
2. 统计女性的社会关系类型分布
3. 女性是否有独立的"赠诗/致书/师生"关系记录？数量和比例如何？

### Step 6 — 可视化
1. **女性占比趋势** `female_ratio_trend.png`：
   - 折线图：X 轴=朝代（按时间顺序），Y 轴=女性占比（%）
   - 标注关键转折点

2. **女性身份类型演变** `female_status_evolution.png`：
   - 堆叠面积图：X 轴=朝代，Y 轴=各身份类型占比
   - 只取 Top 5 身份类型 + 其他

3. **女性籍贯分布** `female_origin_heatmap.png`：
   - 按朝代分组的 Top 10 地区热力图（行=地区，列=朝代，值=人数）

4. **女性亲属角色** `female_kin_roles.png`：
   - 柱状图：各朝代女性在不同亲属关系类型中的出现次数

5. **女性社会关系** `female_assoc_types.png`：
   - 柱状图：女性人物的社会关系类型分布

### Step 7 — 输出文件清单
| 文件 | 内容 |
|------|------|
| `female_dynasty_stats.csv` | 各朝代女性人数与占比 |
| `female_status_by_dynasty.csv` | 女性身份类型按朝代分布 |
| `female_origin_top10.csv` | 女性籍贯 Top 10 按朝代 |
| `female_kin_role_stats.csv` | 女性亲属角色统计 |
| `female_assoc_stats.csv` | 女性社会关系统计 |
| `female_ratio_trend.png` | 女性占比趋势图 |
| `female_status_evolution.png` | 身份类型演变图 |
| `female_origin_heatmap.png` | 籍贯分布热力图 |
| `female_kin_roles.png` | 亲属角色柱状图 |
| `female_assoc_types.png` | 社会关系类型图 |
| `analysis_summary.json` | 分析摘要 |
| `README.md` | 说明文档 |

## 注意事项
1. 路径用 `pathlib.Path`，根目录通过 `Path(__file__).resolve().parents[1]` 获取
2. 中文字体：`plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']`
3. CSV 编码：`utf-8-sig`
4. 朝代排序按历史时间顺序：先秦→西漢→東漢→三國→西晉→東晉→南北朝→隋→唐→五代十國→北宋→南宋→遼→金→元→明→清
5. 非中国朝代（朝鮮、高麗等）排除
6. c_female 以外的值（0=男，其他=未知）需要明确标注
7. 分析结论写入 README.md，重点讨论：女性记录的系统性遗漏、身份从附属到独立的演变、地域文化差异