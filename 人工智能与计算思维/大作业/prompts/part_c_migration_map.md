# Part C 执行 Prompt：地图呈现历史人物迁移关系

## 任务概述

基于 output_cbdb_v1/ 已有的 CSV 数据集，选取 8 位轨迹丰富的历史名人，将其地址经历与任官驻地合并，按时间排序形成人生迁移轨迹，生成交互式 Folium HTML 地图和 Matplotlib 静态 PNG 地图。

## 工作目录

D:\虚拟C盘\study\人工智能与计算思维大作业

## 输入文件

- output_cbdb_v1/fact_person_address.csv — 地址经历表，关键列：c_personid, c_addr_type, c_addr_desc_chn, c_firstyear, c_lastyear, x_coord, y_coord, addr_chn
- output_cbdb_v1/fact_person_posting.csv — 任官驻地表，关键列：c_personid, c_firstyear, c_lastyear, x_coord, y_coord, posting_addr_chn, c_office_chn
- output_cbdb_v1/dim_person.csv — 人物主表，关键列：c_personid, c_name_chn, dynasty_chn, c_index_year

所有 CSV 编码为 UTF-8 BOM（utf-8-sig）。坐标列为 x_coord（经度 lon）和 y_coord（纬度 lat）。

## 目标人物（8 位，硬编码）

| c_personid | 姓名   | 朝代 |
|------------|--------|------|
| 3767       | 蘇軾   | 宋   |
| 32540      | 李白   | 唐   |
| 3915       | 杜甫   | 唐   |
| 8175       | 岳飛   | 宋   |
| 35222      | 袁宏道 | 明   |
| 32227      | 白居易 | 唐   |
| 32174      | 王維   | 唐   |
| 19713      | 李清照 | 宋   |

## 数据合并策略

### 第一步：从地址表提取轨迹

从 act_person_address.csv 筛选上述 8 人的记录，提取：
- c_personid → personid
- c_firstyear → year（整数，0 视为缺失）
- y_coord → lat（纬度）
- x_coord → lon（经度）
- ddr_chn → place_name
- c_addr_desc_chn → event_type（如"籍貫(基本地址)"、"遷住地"、"遊歷或曾經到過"等）

过滤条件：lat 和 lon 都不为 NaN 且都不为 0。

### 第二步：从任官表提取轨迹

从 act_person_posting.csv 筛选上述 8 人的记录，提取：
- c_personid → personid
- c_firstyear → year
- y_coord → lat
- x_coord → lon
- posting_addr_chn → place_name
- event_type 固定为 "任官駐地"

同样过滤无效坐标。

### 第三步：纵向合并

将两部分 concat 为一张长表 	rajectory_df，列：personid, year, lat, lon, place_name, event_type

### 第四步：补充人物信息

从 dim_person.csv 读取 c_personid → c_name_chn, dynasty_chn，合并到轨迹表中。

### 第五步：排序与去重

1. 将 year=0 的记录标记 year = NaN
2. 按 (personid, year) 排序，NaN year 排在每个人物的末尾
3. 对同一人物中欧氏距离 < 0.01 度的相邻重复地点去重，保留最早年份的记录

## 可视化方案

### Folium 交互式 HTML

输出路径：nalysis_c/migration_map.html

实现要求：
- 底图：OpenStreetMap 瓦片（	iles="OpenStreetMap"）
- 地图中心和缩放级别自动计算（所有轨迹点的 bounding box 中心，zoom_start 通过 bounds 自适应）
- 每位人物一个 olium.FeatureGroup（图层名 = 人物姓名），添加到地图后通过 LayerControl 可开关
- 8 色配色方案：使用固定色表 ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#42d4f4', '#f032e6']，按人物列表顺序分配
- 每条轨迹用 olium.PolyLine 绘制，线宽 2.5，透明度 0.7
- 轨迹点用 olium.CircleMarker 绘制，半径 5，颜色与轨迹线一致
- 每个 CircleMarker 的 popup 内容为 HTML 表格：人物: {name}<br>年份: {year}<br>地点: {place}<br>类型: {event_type}
- 起点（该人物 year 最小的点）标记为较大半径（8）+ 加粗边框
- 终点（该人物 year 最大的点）标记为不同图标或颜色加深
- 在地图右上角添加自定义 HTML 图例（olium.Element + MacroElement），列出 8 位人物及对应颜色
- 保存为独立 HTML 文件，可在浏览器直接打开

### Matplotlib 静态 PNG

输出路径：
- nalysis_c/migration_map_static.png — 所有 8 人在同一张图上
- nalysis_c/migration_by_dynasty.png — 按朝代分子图（唐/宋/明各一个 subplot）

实现要求（migration_map_static.png）：
- 图尺寸 igsize=(14, 10)
- 背景色设为浅灰 #f5f5f5，模拟底图效果
- 绘制中国大致轮廓：用所有轨迹点的边界范围（bounding box）设定 xlim/ylim，加 5% padding
- 每位人物一条折线（plt.plot，linewidth=1.5，alpha=0.7）+ 散点（plt.scatter，s=20）
- 起点用五角星标记（marker='*', s=100），终点用方形标记（marker='s', s=80）
- 图例放在图外右侧（box_to_anchor=(1.15, 1)），显示人物姓名和朝代
- 坐标轴标题："经度"、"纬度"
- 图标题："中国历代名人迁移轨迹"
- 中文字体使用 Microsoft YaHei，若不可用则用 SimHei
- plt.tight_layout()，dpi=200，box_inches='tight'
- 保存前调用 plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei'] 和 plt.rcParams['axes.unicode_minus'] = False

实现要求（migration_by_dynasty.png）：
- 图尺寸 igsize=(18, 6)，1 行 3 列子图（唐、宋、明）
- 每个子图只显示对应朝代的人物
- 样式与总图一致
- 每个子图标题为朝代名

## 输出文件清单

`
analysis_c/
  migration_map.html              # Folium 交互式地图
  migration_map_static.png        # Matplotlib 静态地图（8人合图）
  migration_by_dynasty.png        # 按朝代分子图（唐/宋/明）
  migration_trajectory_data.csv   # 合并后轨迹数据（可溯源）
  migration_summary.csv           # 每人轨迹统计摘要
`

## 脚本结构

脚本路径：scripts/c_migration_map.py

结构（单文件，一键可跑）：

`python
# -*- coding: utf-8 -*-
"""
Part C: 地图呈现历史人物迁移关系
"""
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import folium
from folium import FeatureGroup, LayerControl, PolyLine, CircleMarker
import os

# === 配置 ===
BASE_DIR = r'D:\虚拟C盘\study\人工智能与计算思维大作业'
INPUT_DIR = os.path.join(BASE_DIR, 'output_cbdb_v1')
OUTPUT_DIR = os.path.join(BASE_DIR, 'analysis_c')
os.makedirs(OUTPUT_DIR, exist_ok=True)

TARGET_PERSONS = {
    3767: '蘇軾', 32540: '李白', 3915: '杜甫', 8175: '岳飛',
    35222: '袁宏道', 32227: '白居易', 32174: '王維', 19713: '李清照'
}
COLORS = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8',
          '#f58231', '#911eb4', '#42d4f4', '#f032e6']

# === Step 1-3: 数据加载与合并 ===
# ... 读取 address + posting，合并为 trajectory_df

# === Step 4: 补充人物信息 ===
# ... join dim_person

# === Step 5: 排序去重 ===
# ...

# === Step 6: 保存轨迹数据 CSV ===
# trajectory_df.to_csv(...)

# === Step 7: 生成统计摘要 ===
# summary = trajectory_df.groupby('personid').agg(...)

# === Step 8: Folium 交互式地图 ===
# ...

# === Step 9: Matplotlib 静态地图 ===
# ...

# === Step 10: 校验打印 ===
# 打印每人轨迹点数、时间范围、坐标范围
`

注意：不要用 -string 内嵌反斜杠或复杂引号，避免 PowerShell 编码问题。

## 清洗与边界策略

- 坐标 (0, 0) 或 NaN → 丢弃该条记录
- c_firstyear = 0 且不是唯一记录 → 视为缺失年份，year 设为 NaN
- 同一人物同一地点去重：欧氏距离 sqrt((lat1-lat2)^2 + (lon1-lon2)^2) < 0.01 度
- 李白和李清照无任官记录，轨迹仅来自地址表，属正常情况
- 中文字体设置：plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']

## 依赖

- olium（已安装 v0.20.0）
- matplotlib（已安装 v3.10.8）
- pandas（已确认可用）
- 无需安装额外包，无需外部 shapefile 或 GeoJSON

## 验收标准

1. python scripts/c_migration_map.py 一次性运行成功，无报错
2. nalysis_c/migration_map.html 可在浏览器打开，能缩放、点击标记查看人物信息、通过图层控制按人物开关
3. nalysis_c/migration_map_static.png 可清晰辨认各人物轨迹走向，图例完整，中文正常显示
4. nalysis_c/migration_by_dynasty.png 按朝代分 3 个子图，每个子图只含对应朝代人物
5. nalysis_c/migration_trajectory_data.csv 可回溯到原始数据源（保留 personid + event_type）
6. 脚本最后打印校验摘要：每人轨迹点数、最早/最晚年份、坐标范围
7. 蘇軾的轨迹应可辨认出从四川（眉山/廣安軍）出发，经各地任职，最终到达海南/常州的大致路径
8. 李白的轨迹应可辨认出从西域/蜀地出发，游历长江中下游的路径
