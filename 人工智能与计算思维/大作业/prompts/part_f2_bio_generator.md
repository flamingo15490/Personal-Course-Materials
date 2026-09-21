# 任务 F-2：人物传记自动生成

你是一个 Python 数据分析工程师。请严格按照以下计划实现此专题分析。

## 背景
工作目录：`D:\虚拟C盘\study\人工智能与计算思维大作业`
数据来源：`output_cbdb_v1/` 目录下的已数据化 CSV 文件
输出目录：`任务f/专题2_人物传记/`（自动创建）
脚本路径：`scripts/f2_bio_generator.py`

已有依赖：pandas（无需额外安装）

## 专题目标
利用结构化数据自动生成历史人物的"一句话简介"和"一段话小传"。组合字段：姓名+朝代+籍贯+生卒年+身份标签+核心社交关系+主要活动地→自然语句。支持批量生成和单个查询。

## 输入数据
- `output_cbdb_v1/dim_person.csv`：人物主维度（c_personid, c_name_chn, c_name, c_index_year, c_birthyear, c_deathyear, c_female, dynasty_chn, index_addr_chn, x_coord, y_coord）
- `output_cbdb_v1/fact_person_status.csv`：身份维度表
- `output_cbdb_v1/fact_person_address.csv`：地址经历表
- `output_cbdb_v1/fact_person_assoc.csv`：社会关系表

## 传记模板设计

### 一句话简介模板
```
{name}（{birth}-{death}），{dynasty}{gender_label}{origin}人，{top_status}。
```
示例：`蘇軾（1037-1101），宋人，眉山人，文學家、政治家。`

### 一段话小传模板
```
{name}，{dynasty}人，籍貫{origin}。{born_line}。{status_line}。一生主要活動於{main_places}。{assoc_line}。
```
示例：
`蘇軾，宋人，籍貫眉山。生於1037年，卒於1101年。為文學家、政治家。一生主要活動於開封、杭州、黃州、惠州、儋州。與黃庭堅、秦觀、米芾等人交遊唱和。`

### 规则定义
- gender_label：c_female==1→"女"；c_female==0→""（默认男性不标注）；其他→""
- origin：取 index_addr_chn，若为空→"不詳"
- top_status：取身份表中该人物 Top 3 身份（按 sequence 排序或 by 频率），用"、"连接
- born_line：若生卒年都有→"生於{birth}年，卒於{death}年。"；若只有生年→"生於{birth}年。"；都没有→省略此句
- main_places：取地址经历表中出现频次 Top 5 的地名，用"、"连接
- assoc_line：取社会关系表中 Top 5 交往对象（去重，最多5人），"與{names}等人交遊唱和。"；若无人→省略

## 实现步骤

### Step 1 — 数据加载与索引
1. 读取 `dim_person.csv`，建立 {c_personid: row} 的快速查找字典
2. 读取 `fact_person_status.csv`，按 c_personid 分组，预计算每人 Top 3 身份
3. 读取 `fact_person_address.csv`，按 c_personid 分组，预计算每人 Top 5 地名
4. 读取 `fact_person_assoc.csv`，按 c_personid 分组，预计算每人 Top 5 交往对象（通过 dim_person 查出姓名）

### Step 2 — 传记生成核心函数
```python
def generate_one_liner(personid):
    # 返回一句话简介

def generate_bio(personid, max_places=5, max_assoc=5):
    # 返回一段话小传
```

### Step 3 — 批量生成
1. 为宋代 Top 1000 人物（按事实表出现频次）各生成一句话简介和一段话小传
2. 同时支持按 personid 或姓名查询生成
3. 输出 `bio_database.csv`：字段 personid, name, dynasty, one_liner, bio_paragraph, word_count

### Step 4 — 质量评估
1. 随机抽样 20 条传记，检查语句通顺性、信息完整性
2. 统计：一句话简介平均字数、一段话小传平均字数
3. 统计：各字段填充率（生卒年覆盖率、地名覆盖率、交往对象覆盖率）
4. 输出 `bio_quality_report.csv`

### Step 5 — 名人案例展示
选取以下名人生成完整传记并单独保存：
- 蘇軾（3767）
- 李白（32540）
- 杜甫（3915）
- 白居易（32227）
- 岳飛（8175）
- 李清照（19713）
- 王維（32174）
- 王安石、司馬光（按姓名从 dim_person 查找）

### Step 6 — 交互式查询页面（可选，不影响核心交付）
生成一个简单的 HTML 查询页面 `bio_query.html`：
- 输入框：输入姓名或 personid
- 点击查询后显示该人物的一句话简介 + 一段话小传
- 美观卡片式展示

### Step 7 — 输出文件清单
| 文件 | 内容 |
|------|------|
| `bio_database.csv` | Top 1000 人物传记（含一句话和一段话） |
| `bio_quality_report.csv` | 传记质量统计 |
| `celebrities_bio.csv` | 名人传记单独文件 |
| `bio_query.html` | 交互式传记查询页面 |
| `analysis_summary.json` | 分析摘要 |
| `README.md` | 说明文档（含模板规则、已知局限） |

## 注意事项
1. 路径用 `pathlib.Path`，根目录通过 `Path(__file__).resolve().parents[1]` 获取
2. 所有输出 CSV 编码：`utf-8-sig`
3. 生卒年字段可能为空字符串或 0，需要统一判断
4. 一句话简介中，如果多个身份标签太碎（如 5 种不同的"為官者"子类），用大类概括
5. 交往对象如果 c_assoc_id 在 dim_person 中找不到姓名，用"不詳"替代
6. 地名如果重复出现（如"開封"出现 10 次），只取一次
7. 传记文本中避免出现"不詳"过多的情况（比如全是不詳就留空该句）
8. 在 README 中写清楚模板变量来源和缺值处理规则