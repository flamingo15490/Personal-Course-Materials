# 任务 E-4：明清人口大迁徙与文化重心南移

你是一个 Python 数据分析工程师。请严格按照以下计划实现此专题分析。

## 背景
工作目录：`D:\虚拟C盘\study\人工智能与计算思维大作业`
数据来源：`output_cbdb_v1/` 目录下的已数据化 CSV 文件
输出目录：`任务e/专题4_文化重心南移/`（自动创建）
脚本路径：`scripts/e4_cultural_south_shift.py`

已有依赖：matplotlib、pandas（无需额外安装）

## 专题目标
利用 CBDB 地址经历数据，追踪宋→元→明→清四代历史人物的出生地与活动地分布变化，量化"经济文化重心从北到南"这一历史进程。特别关注：北方人物南迁的轨迹、南方文化中心的形成（江南/岭南）、以及明清时期南方文化主导地位的确立。

## 输入数据
- `output_cbdb_v1/dim_person.csv`：人物主维度（含 dynasty_chn, index_addr_chn, x_coord, y_coord）
- `output_cbdb_v1/fact_person_address.csv`：地址经历表（含 c_addr_desc_chn, addr_chn, x_coord, y_coord, c_firstyear）
- `output_cbdb_v1/fact_person_posting.csv`：任官驻地表

## 实现步骤

### Step 1 — 籍贯地理分布（静态基线）
1. 从 `fact_person_address.csv` 筛选 `c_addr_desc_chn == '籍貫(基本地址)'` 的记录
2. 关联 `dim_person.csv` 获取朝代
3. 按朝代（宋/元/明/清）分组，统计：
   - 籍贯坐标的省份分布（用坐标粗略匹配省份，或直接用 addr_chn 中的地名）
   - 北方（纬度 > 33°N）vs 南方（纬度 <= 33°N）的占比
   - Top 10 籍贯地名
4. 输出 `birthplace_by_dynasty.csv`

### Step 2 — 活动地分布（动态迁徙）
1. 从 `fact_person_address.csv` 筛选非籍贯类地址（前住地、迁住地、游历、任官驻地等）
2. 关联 `dim_person.csv` 获取朝代
3. 按朝代分组，统计活动地的南北分布：
   - 各朝代活动地纬度分布的均值和中位数
   - 北方活动地占比的变化
4. 输出 `activity_place_by_dynasty.csv`

### Step 3 — 南迁轨迹分析
1. 对每位有"籍贯在北方 + 活动地在南方"记录的人物，标记为"南迁者"
2. 按朝代统计南迁者数量和占比
3. 分析南迁目的地 Top 10 地区（是否集中在江南/临安/广州等）
4. 输出 `migration_south_stats.csv`

### Step 4 — 文化中心演变
1. 用"赠诗/致书/师生"等文学/学术交往关系，找到各朝代文化交往最密集的地区
2. 方法：将社会关系中涉及的地址按朝代聚合，统计各地区出现的文化交往频次
3. 标注各朝代的文化中心（Top 3 地区）
4. 输出 `cultural_centers_by_dynasty.csv`

### Step 5 — 可视化
1. **南北占比变化** `north_south_ratio.png`：
   - 双 Y 轴折线图：X 轴=朝代，左 Y 轴=南方籍贯占比（%），右 Y 轴=南方活动地占比（%）
   - 标注关键历史事件（如靖康之变、南宋建立）

2. **籍贯分布热力图** `birthplace_heatmap.png`：
   - 4 个子图（宋/元/明/清），每个子图为散点图
   - X=经度，Y=纬度，点大小=该地区人数，颜色深浅=密度

3. **南迁趋势** `south_migration_trend.png`：
   - 柱状图：X 轴=朝代，Y 轴=南迁者占比（%）
   - 叠加折线：南迁者绝对数量

4. **文化中心迁移** `cultural_center_shift.png`：
   - 在地图上标注各朝代的文化中心（Top 3），用箭头连接表示迁移方向
   - 如果坐标不好获取，可用条形图展示各朝代 Top 5 地区的文化交往频次

### Step 6 — 输出文件清单
| 文件 | 内容 |
|------|------|
| `birthplace_by_dynasty.csv` | 各朝代籍贯分布 |
| `activity_place_by_dynasty.csv` | 各朝代活动地分布 |
| `migration_south_stats.csv` | 南迁统计 |
| `cultural_centers_by_dynasty.csv` | 文化中心变迁 |
| `north_south_ratio.png` | 南北占比变化 |
| `birthplace_heatmap.png` | 籍贯分布热力图 |
| `south_migration_trend.png` | 南迁趋势 |
| `cultural_center_shift.png` | 文化中心迁移 |
| `analysis_summary.json` | 分析摘要 |
| `README.md` | 说明文档 |

## 注意事项
1. 路径用 `pathlib.Path`，根目录通过 `Path(__file__).resolve().parents[1]` 获取
2. 中文字体：`plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']`
3. CSV 编码：`utf-8-sig`
4. 坐标缺失的记录按原样保留地名统计，不丢弃
5. 南北分界以纬度 33°N 为近似标准
6. 朝代排序按时间顺序：宋→元→明→清
7. 分析结论写入 README.md，重点讨论：靖康之变的影响、江南文化核心区的形成、明清科举南强北弱