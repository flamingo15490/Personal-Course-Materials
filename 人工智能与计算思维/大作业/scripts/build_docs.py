# -*- coding: utf-8 -*-
"""
生成 CBDB 数据化说明文档（中文），含结构说明、字段含义、案例链路与校验摘要。
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output_cbdb_v1"


def iter_csv(path: Path):
    with path.open("r", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        for row in r:
            yield row


def load_validation():
    return json.loads((OUT / "validation_summary.json").read_text(encoding="utf-8"))


def load_verify():
    p = OUT / "verify_report.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return None


def sample_rows(rows, pids, coord_only=False, limit=10):
    out = []
    for row in rows:
        if row["c_personid"] not in pids:
            continue
        if coord_only:
            if row.get("x_coord") in ("", None) or row.get("y_coord") in ("", None):
                continue
        out.append(row)
        if len(out) >= limit:
            break
    return out


def main():
    val = load_validation()
    verify = load_verify()

    dim_person = []
    with (OUT / "dim_person.csv").open("r", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        for i, row in enumerate(r):
            if i < 6:
                dim_person.append(row)
            else:
                break

    status_rows = sample_rows(iter_csv(OUT / "fact_person_status.csv"), {"1", "4"}, coord_only=False, limit=20)
    posting_rows = sample_rows(iter_csv(OUT / "fact_person_posting.csv"), {"1", "4"}, coord_only=True, limit=40)

    def person_name(pid):
        for row in dim_person:
            if row["c_personid"] == str(pid):
                return row["c_name_chn"] or row["c_name"]
        return str(pid)

    md = []
    md.append("# CBDB 数据化首版说明\n")
    md.append("本文档配套 `output_cbdb_v1/` 下的 CSV 数据集，说明如何把 CBDB 原始关系型数据库整理成可用于历史人物分析的结构化数据。\n")
    md.append("## 1. 数据库整体结构说明（ER 思路）\n")
    md.append("- **人物主表**：`BIOG_MAIN` 以 `c_personid` 为核心，保存姓名、性别、索引年、生卒年、活动年与索引地。")
    md.append("- **身份维度**：`STATUS_DATA` + `STATUS_CODES`，描述人物在社会身份/职业上的多条记录。")
    md.append("- **地址经历**：`BIOG_ADDR_DATA` + `ADDR_CODES` + `BIOG_ADDR_CODES`，描述人物相关地点与类型。")
    md.append("- **任官驻地**：`POSTING_DATA` → `POSTED_TO_OFFICE_DATA` → `OFFICE_CODES`，再可选挂接 `POSTED_TO_ADDR_DATA` → `ADDR_CODES`。")
    md.append("- **亲属与社会关系**：`KIN_DATA` + `KINSHIP_CODES`、`ASSOC_DATA` + `ASSOC_CODES`。\n")
    md.append("```mermaid\nflowchart LR\n  BIOG_MAIN --> STATUS_DATA --> STATUS_CODES\n  BIOG_MAIN --> BIOG_ADDR_DATA --> ADDR_CODES\n  BIOG_MAIN --> POSTING_DATA --> POSTED_TO_OFFICE_DATA --> OFFICE_CODES\n  POSTED_TO_OFFICE_DATA --> POSTED_TO_ADDR_DATA --> ADDR_CODES\n  BIOG_MAIN --> KIN_DATA --> KINSHIP_CODES\n  BIOG_MAIN --> ASSOC_DATA --> ASSOC_CODES\n```")
    md.append("\n## 2. 关键字段含义表\n")
    md.append("| 表 | 字段 | 含义 | 来源/说明 |")
    md.append("|---|---|---|---|")
    md.append("| `BIOG_MAIN` | `c_personid` | 人物主键 | 可溯源唯一ID |")
    md.append("| `BIOG_MAIN` | `c_name_chn` | 中文姓名 | 自动拼接字段 |")
    md.append("| `BIOG_MAIN` | `c_dy` | 朝代编码 | 缺失保留NULL |")
    md.append("| `BIOG_MAIN` | `c_index_addr_id` | 索引地ID | 0视为未知地 |")
    md.append("| `STATUS_DATA` | `c_status_code` | 身份编码 | 原始编码 |")
    md.append("| `BIOG_ADDR_DATA` | `c_addr_type` | 地址类型编码 | 原始编码 |")
    md.append("| `POSTED_TO_OFFICE_DATA` | `c_appt_code` | 任官方式编码 | 原始编码 |")
    md.append("| `POSTED_TO_OFFICE_DATA` | `c_office_id` | 职官编码 | 原始编码 |")
    md.append("| `KIN_DATA` | `c_kin_code` | 亲属关系编码 | 原始编码 |")
    md.append("| `ASSOC_DATA` | `c_assoc_code` | 社会关系编码 | 原始编码 |\n")
    md.append("完整字段字典见 `data_dictionary.csv`。\n")

    md.append("## 3. 数据口径与处理规则\n")
    md.append("- 未知值（`0`、`未詳`、空值）保留为空串或 `NULL`，不默认推断。")
    md.append("- 时间字段不做插值，缺失保留 `NULL`。")
    md.append("- 地址与任官驻地仅在源表可定位坐标时才生成坐标字段，不影响主维度完整性。")
    md.append("- 为便于 Excel/Pandas 读取，所有 CSV 使用 `UTF-8 with BOM`。\n")

    md.append("## 4. 案例链路：人物如何“数据化”\n")
    md.append(f"### 案例 1：`c_personid=1`（{person_name(1)}）\n")
    md.append("原始数据链路：\n")
    md.append("- `BIOG_MAIN`：主维度 → `dim_person.csv`。")
    md.append("- `STATUS_DATA + STATUS_CODES`：身份记录 → `fact_person_status.csv`。")
    md.append("- `POSTING_DATA → POSTED_TO_OFFICE_DATA → OFFICE_CODES (+ ADDR_CODES)`：任官地点 → `fact_person_posting.csv`。")
    md.append("- `KIN_DATA + KINSHIP_CODES`：亲属关系 → `fact_person_kin.csv`。")
    md.append("- `ASSOC_DATA + ASSOC_CODES`：社会关系 → `fact_person_assoc.csv`。\n")
    md.append("结果样例（带坐标的可制图记录）：\n")
    md.append("**身份记录**\n")
    md.append("| c_personid | c_status_desc_chn | c_firstyear | c_lastyear |")
    md.append("|---|---|---|---|")
    for row in status_rows[:8]:
        if row["c_personid"] == "1":
            md.append(f"| {row['c_personid']} | {row['c_status_desc_chn']} | {row['c_firstyear']} | {row['c_lastyear']} |")
    md.append("\n**任官与驻地（含坐标）**\n")
    md.append("| c_personid | c_office_chn | posting_addr_chn | x_coord | y_coord |")
    md.append("|---|---|---|---|---|")
    cnt = 0
    for row in posting_rows:
        if row["c_personid"] == "1":
            md.append(f"| {row['c_personid']} | {row['c_office_chn']} | {row['posting_addr_chn']} | {row['x_coord']} | {row['y_coord']} |")
            cnt += 1
            if cnt >= 8:
                break

    md.append(f"\n### 案例 2：`c_personid=4`（{person_name(4)}）\n")
    md.append("**任官与驻地（含坐标）**\n")
    md.append("| c_personid | c_office_chn | posting_addr_chn | x_coord | y_coord |")
    md.append("|---|---|---|---|---|")
    cnt = 0
    for row in posting_rows:
        if row["c_personid"] == "4":
            md.append(f"| {row['c_personid']} | {row['c_office_chn']} | {row['posting_addr_chn']} | {row['x_coord']} | {row['y_coord']} |")
            cnt += 1
            if cnt >= 12:
                break

    md.append("\n## 5. 产出文件说明\n")
    md.append("- `dim_person.csv`：人物主维度。")
    md.append("- `dim_address.csv`：地址主维度（含坐标）。")
    md.append("- `fact_person_status.csv`：人物-身份维度。")
    md.append("- `fact_person_address.csv`：人物-地址维度。")
    md.append("- `fact_person_posting.csv`：人物-任官-驻地维度。")
    md.append("- `fact_person_kin.csv`：亲属关系边表。")
    md.append("- `fact_person_assoc.csv`：社会关系边表。")
    md.append("- `data_dictionary.csv`：字段字典。")
    md.append("- `validation_summary.json`：源表与输出计数。")
    md.append("- `verify_report.json`：唯一性与覆盖度校验。\n")

    md.append("## 6. 校验摘要\n")
    md.append("```json")
    md.append(json.dumps(val, ensure_ascii=False, indent=2))
    md.append("```\n")
    if verify:
        md.append("```json")
        md.append(json.dumps(verify, ensure_ascii=False, indent=2))
        md.append("```\n")

    (ROOT / "README_DATAIZATION.md").write_text("\n".join(md), encoding="utf-8-sig")
    print((ROOT / "README_DATAIZATION.md").resolve())


if __name__ == "__main__":
    main()
