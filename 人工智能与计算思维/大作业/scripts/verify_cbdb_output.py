# -*- coding: utf-8 -*-
"""
校验 CBDB 数据化首版输出，必要时自动修复 dim_person 去重。
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output_cbdb_v1"


def read_header(path: Path):
    with path.open("r", encoding="utf-8-sig") as f:
        return next(csv.reader(f))


def count_rows(path: Path):
    with path.open("r", encoding="utf-8-sig") as f:
        return sum(1 for _ in f) - 1


def check_unique(path: Path, cols: list[str]):
    header = read_header(path)
    idxs = [header.index(c) for c in cols]
    seen = set()
    dup = 0
    with path.open("r", encoding="utf-8-sig") as f:
        r = csv.reader(f)
        next(r)
        for row in r:
            key = tuple(row[i] for i in idxs)
            if key in seen:
                dup += 1
            else:
                seen.add(key)
    return dup


def fix_dim_person_if_needed():
    p = OUT / "dim_person.csv"
    dup = check_unique(p, ["c_personid"])
    if dup == 0:
        return {"fixed": False, "duplicate_rows": 0}

    # 仅保留每个 c_personid 的第一行
    tmp = OUT / "dim_person.csv.tmp"
    seen = set()
    removed = 0
    with p.open("r", encoding="utf-8-sig") as fin, tmp.open("w", encoding="utf-8-sig", newline="") as fout:
        r = csv.reader(fin)
        w = csv.writer(fout)
        header = next(r)
        w.writerow(header)
        pid_idx = header.index("c_personid")
        for row in r:
            pid = row[pid_idx]
            if pid in seen:
                removed += 1
                continue
            seen.add(pid)
            w.writerow(row)
    tmp.replace(p)
    return {"fixed": True, "duplicate_rows": removed}


def main():
    dim_person = OUT / "dim_person.csv"
    dim_addr = OUT / "dim_address.csv"
    fact_status = OUT / "fact_person_status.csv"
    fact_addr = OUT / "fact_person_address.csv"
    fact_posting = OUT / "fact_person_posting.csv"
    fact_kin = OUT / "fact_person_kin.csv"
    fact_assoc = OUT / "fact_person_assoc.csv"

    result = {
        "row_counts": {
            "dim_person": count_rows(dim_person),
            "dim_address": count_rows(dim_addr),
            "fact_person_status": count_rows(fact_status),
            "fact_person_address": count_rows(fact_addr),
            "fact_person_posting": count_rows(fact_posting),
            "fact_person_kin": count_rows(fact_kin),
            "fact_person_assoc": count_rows(fact_assoc),
        },
        "primary_key_duplicates": {
            "dim_person(c_personid)": check_unique(dim_person, ["c_personid"]),
            "fact_person_status(c_personid,c_sequence,c_status_code)": check_unique(
                fact_status, ["c_personid", "c_sequence", "c_status_code"]
            ),
            "fact_person_address(c_personid,c_addr_id,c_addr_type,c_sequence)": check_unique(
                fact_addr, ["c_personid", "c_addr_id", "c_addr_type", "c_sequence"]
            ),
            "fact_person_kin(c_personid,c_kin_id,c_kin_code)": check_unique(
                fact_kin, ["c_personid", "c_kin_id", "c_kin_code"]
            ),
        },
        "person_coverage": {
            "status_persons": len(set(read_col(fact_status, "c_personid"))),
            "address_persons": len(set(read_col(fact_addr, "c_personid"))),
            "posting_persons": len(set(read_col(fact_posting, "c_personid"))),
            "kin_persons": len(set(read_col(fact_kin, "c_personid"))),
            "assoc_persons": len(set(read_col(fact_assoc, "c_personid"))),
        },
    }

    fix = fix_dim_person_if_needed()
    result["dim_person_fix"] = fix

    (OUT / "verify_report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


def read_col(path: Path, col: str):
    vals = []
    with path.open("r", encoding="utf-8-sig") as f:
        r = csv.reader(f)
        header = next(r)
        idx = header.index(col)
        for row in r:
            vals.append(row[idx])
    return vals


if __name__ == "__main__":
    main()
