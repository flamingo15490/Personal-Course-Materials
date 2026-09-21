# 任务 E-6：文学群体的地理集聚——从长安到江南

你是一个 Python 数据分析工程师。请严格按照以下计划实现此专题分析。

## 背景
工作目录：`D:\虚拟C盘\study\人工智能与计算思维大作业`
数据来源：`output_cbdb_v1/` 目录下的已数据化 CSV 文件
输出目录：`任务e/专题6_文学地理/`（自动创建）
脚本路径：`scripts/e6_literary_geography.py`

已有依赖：matplotlib、pandas（无需额外安装）

## 专题目标
追踪中国古代"文学交往"（赠诗/致书/唱和/同游/书序/墓志铭等）的地理重心在各朝代的迁移路径，量化文学中心从唐代长安→宋代汴京/临安→元明江南的演变过程，并分析文学群体的地理集聚特征。

## 输入数据
- `output_cbdb_v1/fact_person_assoc.csv`：社会关系边表（含 c_assoc_desc_chn）
- `output_cbdb_v1/fact_person_address.csv`：地址经历表（含坐标和地名）
- `output_cbdb_v1/dim_person.csv`：人物主维度

## 文学交往关系类型定义
从 `c_assoc_desc_chn` 中匹配以下关键词的关系：
- 贈詩、收到贈詩
- 致書、被致書、答書、收到答書
- 為Y所著書作序、書序由Y所作
- 為Y所著書作跋、書跋由Y所作
- 唱和、同遊
- 為Y作墓誌銘（虽是丧葬，但墓志铭撰写是重要文学活动）

## 实现步骤

### Step 1 — 文学交往关系提取
1. 读取 `fact_person_assoc.csv`，筛选上述文学交往类型的关系
2. 关联 `dim_person.csv` 获取朝代
3. 统计各朝代文学交往关系的总量

### Step 2 — 文学人物地理定位
1. 从 `fact_person_address.csv` 获取每位文学交往参与者的活动地坐标
2. 对每位人物，取其最频繁活动地（或籍贯+任官地的加权中心）作为代表坐标
3. 按朝代聚合，计算该朝代所有文学人物的"地理重心"（加权平均经纬度）
4. 输出 `literary_centroid_by_dynasty.csv`

### Step 3 — 文学交往地理密度分析
1. 将中国地图粗略划分为 5°×5° 的网格
2. 按朝代统计每个网格内的文学交往频次
3. 找出各朝代 Top 10 高密度网格
4. 计算文学交往的地理集中度（HHI 指数）和重心迁移距离
5. 输出 `literary_density_grid.csv`

### Step 4 — 文学群体聚类分析
1. 对每个主要朝代（唐/宋/明），用文学交往关系构建子网
2. 做社区检测，找到文学群体
3. 分析每个文学群体的地理特征：
   - 群体成员的籍贯/活动地是否集中在同一地区？
   - 是否存在"跨地域文学群体"（如韩愈的古文运动群体）？
4. 输出 `literary_community_geo.csv`

### Step 5 — 文学重心迁移轨迹
1. 计算各朝代文学交往地理重心的经纬度
2. 计算相邻朝代重心之间的迁移距离（公里，Haversine 公式）
3. 标注迁移方向（南/北/东/西）
4. 输出 `literary_centroid_movement.csv`

### Step 6 — 可视化
1. **文学重心迁移** `literary_centroid_movement.png`：
   - 在中国轮廓（或坐标系）上标注各朝代的文学重心
   - 用箭头连接相邻朝代重心，标注朝代名称
   - 如果画不了中国轮廓，用散点+箭头的坐标图即可

2. **文学交往密度** `literary_density_heatmap.png`：
   - 4 个子图（唐/宋/元/明），每个为网格热力图
   - X=经度，Y=纬度，颜色=文学交往频次

3. **朝代文学活跃度** `literary_activity_trend.png`：
   - 折线图：X 轴=朝代，Y 轴=文学交往总频次（绝对数量）
   - 叠加折线：参与文学交往的人数

4. **文学群体地理分布** `literary_community_map.png`：
   - 按朝代分组的散点图，不同社区用不同颜色
   - 展示文学群体是否与地理区域对应

### Step 7 — 输出文件清单
| 文件 | 内容 |
|------|------|
| `literary_centroid_by_dynasty.csv` | 各朝代文学重心坐标 |
| `literary_density_grid.csv` | 网格化文学交往密度 |
| `literary_community_geo.csv` | 文学群体地理特征 |
| `literary_centroid_movement.csv` | 重心迁移轨迹 |
| `literary_activity_by_dynasty.csv` | 各朝代文学活跃度统计 |
| `literary_centroid_movement.png` | 文学重心迁移图 |
| `literary_density_heatmap.png` | 文学交往密度热力图 |
| `literary_activity_trend.png` | 文学活跃度趋势 |
| `literary_community_map.png` | 文学群体地理分布 |
| `analysis_summary.json` | 分析摘要 |
| `README.md` | 说明文档 |

## 注意事项
1. 路径用 `pathlib.Path`，根目录通过 `Path(__file__).resolve().parents[1]` 获取
2. 中文字体：`plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']`
3. CSV 编码：`utf-8-sig`
4. 坐标缺失的记录：保留地名统计，不参与坐标计算
5. Haversine 公式：`a = sin²(Δlat/2) + cos(lat1)·cos(lat2)·sin²(Δlon/2); c = 2·atan2(√a, √(1-a)); d = R·c`（R=6371km）
6. 朝代排序按时间：唐→五代十國→北宋→南宋→元→明
7. 网格化分析中，只统计有坐标的记录，缺坐标的用"地名频次"补充说明
8. 分析结论写入 README.md，重点讨论：文学中心迁移与政治中心变迁的关系、地方文学传统的形成