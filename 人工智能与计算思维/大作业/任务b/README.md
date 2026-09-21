# 任务 B：历史人物维度与各朝代数量分布

## 任务目标
定义中国历史人物的多维属性，并统计每个维度在各朝代的数量分布情况。

## 维度设计

| 维度 | 字段来源 | 说明 |
|------|----------|------|
| 朝代（核心维度） | `dim_person.dynasty_chn` | 来源于 `BIOG_MAIN.c_dy`，映射到中文朝代名 |
| 性别 | `dim_person.c_female` | 0=男性，1=女性，其余归为"未知" |
| 身份类型 | `fact_person_status.c_status_desc_chn` | 如"文官""诗人""画家"等，保留原始标签不做二次合并 |
| 地址类型 | `fact_person_address.c_addr_desc_chn` | 如"籍贯""迁住地""葬地"等 |

## 统计口径
- **人物总量统计**：按 `dim_person.c_personid` 去重计数（一人一行）
- **身份/地址统计**：按事实表行数计数（一人可有多条记录），文案中已注明口径差异
- **朝代归并**：采用 `main_dynasty` 精简列表（16 个主要朝代 + "其他"/"非中国朝代"/"未知"），排除了朝鲜、高丽、新罗等非中国政权

## 文件清单

### 统计 CSV

| 文件 | 内容 | 行数说明 |
|------|------|----------|
| `person_dynasty_counts.csv` | 全量朝代人物分布（含原始 77 个朝代标签） | 按 `dynasty_chn` 分组，覆盖全部 658,941 人 |
| `person_main_dynasty_counts.csv` | 精简朝代人物分布（19 行） | 按 `main_dynasty` 归并，适合论文主表 |
| `status_by_dynasty_counts.csv` | 朝代 x 身份类型交叉表 | 按事实行计数，status_desc 保留原始标签 |
| `address_type_by_dynasty_counts.csv` | 朝代 x 地址类型交叉表 | 按事实行计数 |
| `gender_by_dynasty_counts.csv` | 朝代 x 性别交叉表 | 按人数计数 |

### 图表（`charts/` 目录）

| 文件 | 内容 |
|------|------|
| `dynasty_person_counts.png` | 各朝代人物总量柱状图（按数量排序） |
| `dynasty_detail_top30.png` | Top 30 朝代详细柱状图 |
| `status_by_dynasty_stacked.png` | 朝代 x 身份类型堆叠柱状图（Top N 身份） |
| `address_type_by_dynasty_stacked.png` | 朝代 x 地址类型堆叠柱状图（Top N 类型） |
| `gender_by_dynasty_grouped.png` | 朝代 x 性别分组柱状图 |
| `gender_by_dynasty_percent.png` | 朝代 x 性别百分比堆叠图 |

## 数据特征摘要

**朝代分布 Top 5：** 清 (236,022) > 明 (224,659) > 宋 (83,312) > 唐 (57,476) > 元 (25,309)

**身份类型 Top 5：** 文官、诗人、画家、孝子/孝女、财政官员

**地址类型 Top 5：** 籍贯、户籍地、八旗（清代）、死所、游历

## 已知限制
- `未詳` 朝代归入"未知"类目，不丢弃
- 身份标签保留原始括号格式（如 `[為官者：文]`），未做语义合并
- 非中国政权（朝鲜、高丽、新罗等）单独归为"非中国朝代"类

## 生成脚本
`scripts/b_analysis_and_viz.py`，一键运行可复现全部统计与图表。