# -*- coding: utf-8 -*-
"""
CBDB 数据化首版提取脚本
输入: latest/cbdb_20260606.sqlite3
输出: output_cbdb_v1/*.csv + data_dictionary.csv + validation_summary.json
"""
from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "latest" / "cbdb_20260606.sqlite3"
OUT_DIR = ROOT / "output_cbdb_v1"
OUT_DIR.mkdir(exist_ok=True)


def write_csv(path: Path, rows, header):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for row in rows:
            w.writerow(row)


def dump_dict(path: Path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["table", "column", "meaning", "source_join", "notes"])
        for row in rows:
            w.writerow(row)


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    dim_person = cur.execute(
        """
        SELECT
            b.c_personid,
            b.c_name,
            b.c_name_chn,
            b.c_female,
            b.c_index_year,
            b.c_index_year_type_code,
            b.c_birthyear,
            b.c_deathyear,
            b.c_death_age,
            b.c_fl_earliest_year,
            b.c_fl_latest_year,
            b.c_dy,
            COALESCE(NULLIF(TRIM(d.c_dynasty_chn), ''), '') AS dynasty_chn,
            COALESCE(NULLIF(TRIM(d.c_dynasty), ''), '') AS dynasty,
            b.c_index_addr_id,
            COALESCE(NULLIF(TRIM(addr.c_name_chn), ''), '') AS index_addr_chn,
            COALESCE(NULLIF(TRIM(addr.c_name), ''), '') AS index_addr_pinyin,
            addr.x_coord AS index_addr_x,
            addr.y_coord AS index_addr_y,
            b.c_ethnicity_code,
            b.c_choronym_code,
            b.c_notes
        FROM BIOG_MAIN b
        LEFT JOIN DYNASTIES d ON d.c_dy = b.c_dy
        LEFT JOIN ADDR_CODES addr ON addr.c_addr_id = b.c_index_addr_id
        """
    ).fetchall()

    fact_status = cur.execute(
        """
        SELECT
            sd.c_personid,
            sd.c_sequence,
            sd.c_status_code,
            sc.c_status_desc,
            sc.c_status_desc_chn,
            sd.c_firstyear,
            sd.c_lastyear,
            sd.c_source,
            sd.c_pages,
            sd.c_notes
        FROM STATUS_DATA sd
        LEFT JOIN STATUS_CODES sc ON sc.c_status_code = sd.c_status_code
        """
    ).fetchall()

    fact_addr = cur.execute(
        """
        SELECT
            ba.c_personid,
            ba.c_addr_id,
            ba.c_addr_type,
            bac.c_addr_desc,
            bac.c_addr_desc_chn,
            ba.c_sequence,
            ba.c_firstyear,
            ba.c_lastyear,
            COALESCE(NULLIF(TRIM(addr.c_name_chn), ''), '') AS addr_chn,
            COALESCE(NULLIF(TRIM(addr.c_name), ''), '') AS addr_pinyin,
            addr.x_coord,
            addr.y_coord,
            ba.c_source,
            ba.c_pages,
            ba.c_notes
        FROM BIOG_ADDR_DATA ba
        LEFT JOIN ADDR_CODES addr ON addr.c_addr_id = ba.c_addr_id
        LEFT JOIN BIOG_ADDR_CODES bac ON bac.c_addr_type = ba.c_addr_type
        """
    ).fetchall()

    fact_posting = cur.execute(
        """
        SELECT
            o.c_personid,
            o.c_posting_id,
            o.c_office_id,
            oc.c_office_chn,
            oc.c_office_trans,
            o.c_dy,
            o.c_firstyear,
            o.c_lastyear,
            o.c_appt_code,
            ac.c_appt_desc_chn,
            ac.c_appt_desc,
            o.c_assume_office_code,
            aoc.c_assume_office_desc_chn,
            aoc.c_assume_office_desc,
            COALESCE(NULLIF(TRIM(addr.c_name_chn), ''), '') AS posting_addr_chn,
            COALESCE(NULLIF(TRIM(addr.c_name), ''), '') AS posting_addr_pinyin,
            addr.x_coord,
            addr.y_coord,
            o.c_source,
            o.c_pages,
            o.c_notes
        FROM POSTED_TO_OFFICE_DATA o
        LEFT JOIN OFFICE_CODES oc ON oc.c_office_id = o.c_office_id
        LEFT JOIN APPOINTMENT_CODES ac ON ac.c_appt_code = o.c_appt_code
        LEFT JOIN ASSUME_OFFICE_CODES aoc ON aoc.c_assume_office_code = o.c_assume_office_code
        LEFT JOIN POSTED_TO_ADDR_DATA pa
            ON pa.c_posting_id = o.c_posting_id AND pa.c_office_id = o.c_office_id
        LEFT JOIN ADDR_CODES addr ON addr.c_addr_id = pa.c_addr_id
        """
    ).fetchall()

    fact_kin = cur.execute(
        """
        SELECT
            k.c_personid,
            k.c_kin_id,
            k.c_kin_code,
            kc.c_kinrel,
            kc.c_kinrel_chn,
            k.c_source,
            k.c_pages,
            k.c_notes
        FROM KIN_DATA k
        LEFT JOIN KINSHIP_CODES kc ON kc.c_kincode = k.c_kin_code
        """
    ).fetchall()

    fact_assoc = cur.execute(
        """
        SELECT
            a.c_personid,
            a.c_assoc_id,
            a.c_assoc_code,
            ac.c_assoc_desc,
            ac.c_assoc_desc_chn,
            a.c_assoc_first_year,
            a.c_assoc_last_year,
            a.c_addr_id,
            a.c_source,
            a.c_pages,
            a.c_notes
        FROM ASSOC_DATA a
        LEFT JOIN ASSOC_CODES ac ON ac.c_assoc_code = a.c_assoc_code
        """
    ).fetchall()

    addr_dim = cur.execute(
        """
        SELECT
            c_addr_id,
            c_name,
            c_name_chn,
            c_firstyear,
            c_lastyear,
            c_admin_type,
            c_admin_cat_code,
            x_coord,
            y_coord,
            CHGIS_PT_ID,
            c_alt_names,
            c_notes
        FROM ADDR_CODES
        """
    ).fetchall()

    write_csv(
        OUT_DIR / "dim_person.csv",
        dim_person,
        [
            "c_personid", "c_name", "c_name_chn", "c_female", "c_index_year",
            "c_index_year_type_code", "c_birthyear", "c_deathyear", "c_death_age",
            "c_fl_earliest_year", "c_fl_latest_year", "c_dy", "dynasty_chn", "dynasty",
            "c_index_addr_id", "index_addr_chn", "index_addr_pinyin",
            "index_addr_x", "index_addr_y", "c_ethnicity_code", "c_choronym_code", "c_notes"
        ],
    )

    write_csv(
        OUT_DIR / "dim_address.csv",
        addr_dim,
        [
            "c_addr_id", "c_name", "c_name_chn", "c_firstyear", "c_lastyear",
            "c_admin_type", "c_admin_cat_code", "x_coord", "y_coord", "CHGIS_PT_ID",
            "c_alt_names", "c_notes"
        ],
    )

    write_csv(
        OUT_DIR / "fact_person_status.csv",
        fact_status,
        [
            "c_personid", "c_sequence", "c_status_code", "c_status_desc", "c_status_desc_chn",
            "c_firstyear", "c_lastyear", "c_source", "c_pages", "c_notes"
        ],
    )

    write_csv(
        OUT_DIR / "fact_person_address.csv",
        fact_addr,
        [
            "c_personid", "c_addr_id", "c_addr_type", "c_addr_desc", "c_addr_desc_chn",
            "c_sequence", "c_firstyear", "c_lastyear", "addr_chn", "addr_pinyin",
            "x_coord", "y_coord", "c_source", "c_pages", "c_notes"
        ],
    )

    write_csv(
        OUT_DIR / "fact_person_posting.csv",
        fact_posting,
        [
            "c_personid", "c_posting_id", "c_office_id", "c_office_chn", "c_office_trans",
            "c_dy", "c_firstyear", "c_lastyear", "c_appt_code", "c_appt_desc_chn",
            "c_appt_desc", "c_assume_office_code", "c_assume_office_desc_chn",
            "c_assume_office_desc", "posting_addr_chn", "posting_addr_pinyin",
            "x_coord", "y_coord", "c_source", "c_pages", "c_notes"
        ],
    )

    write_csv(
        OUT_DIR / "fact_person_kin.csv",
        fact_kin,
        [
            "c_personid", "c_kin_id", "c_kin_code", "c_kinrel", "c_kinrel_chn",
            "c_source", "c_pages", "c_notes"
        ],
    )

    write_csv(
        OUT_DIR / "fact_person_assoc.csv",
        fact_assoc,
        [
            "c_personid", "c_assoc_id", "c_assoc_code", "c_assoc_desc", "c_assoc_desc_chn",
            "c_assoc_first_year", "c_assoc_last_year", "c_addr_id",
            "c_source", "c_pages", "c_notes"
        ],
    )

    dict_rows = [
        ("dim_person", "c_personid", "人物主键", "BIOG_MAIN", "可溯源唯一ID"),
        ("dim_person", "c_name_chn", "中文姓名", "BIOG_MAIN", "自动拼接字段"),
        ("dim_person", "c_dy", "朝代编码", "BIOG_MAIN", "缺失时保留NULL"),
        ("dim_person", "dynasty_chn", "朝代中文名", "DYNASTIES", "通过c_dy关联"),
        ("dim_person", "c_index_addr_id", "索引地ID", "BIOG_MAIN", "0视为未知地"),
        ("dim_person", "index_addr_chn", "索引地中文名", "ADDR_CODES", "缺失用空串"),
        ("dim_person", "index_addr_x/y", "索引地坐标", "ADDR_CODES", "部分缺失"),
        ("fact_person_status", "c_status_code", "身份编码", "STATUS_DATA", "原始编码"),
        ("fact_person_status", "c_status_desc_chn", "身份中文名", "STATUS_CODES", "便于解读"),
        ("fact_person_address", "c_addr_type", "地址类型编码", "BIOG_ADDR_DATA", "原始编码"),
        ("fact_person_address", "addr_chn", "地址中文名", "ADDR_CODES", "便于解读"),
        ("fact_person_posting", "c_appt_code", "任官方式编码", "POSTED_TO_OFFICE_DATA", "原始编码"),
        ("fact_person_posting", "c_appt_desc_chn", "任官方式中文", "APPOINTMENT_CODES", "便于解读"),
        ("fact_person_kin", "c_kin_code", "亲属编码", "KIN_DATA", "原始编码"),
        ("fact_person_kin", "c_kinrel_chn", "亲属关系中文", "KINSHIP_CODES", "便于解读"),
        ("fact_person_assoc", "c_assoc_code", "社会关系编码", "ASSOC_DATA", "原始编码"),
        ("fact_person_assoc", "c_assoc_desc_chn", "社会关系中文", "ASSOC_CODES", "便于解读"),
    ]
    dump_dict(OUT_DIR / "data_dictionary.csv", dict_rows)

    def count(path: Path):
        with path.open("r", encoding="utf-8-sig") as f:
            return sum(1 for _ in f) - 1

    dim_count = count(OUT_DIR / "dim_person.csv")
    coord_rows = 0
    with (OUT_DIR / "dim_person.csv").open("r", encoding="utf-8-sig") as f:
        r = csv.reader(f)
        header = next(r)
        ix = header.index("index_addr_x")
        iy = header.index("index_addr_y")
        for row in r:
            if row[ix] not in ("", "None") and row[iy] not in ("", "None"):
                coord_rows += 1

    validation = {
        "source_db": str(DB_PATH),
        "tables": {
            "BIOG_MAIN": cur.execute("select count(*) from BIOG_MAIN").fetchone()[0],
            "STATUS_DATA": cur.execute("select count(*) from STATUS_DATA").fetchone()[0],
            "BIOG_ADDR_DATA": cur.execute("select count(*) from BIOG_ADDR_DATA").fetchone()[0],
            "POSTED_TO_OFFICE_DATA": cur.execute("select count(*) from POSTED_TO_OFFICE_DATA").fetchone()[0],
            "KIN_DATA": cur.execute("select count(*) from KIN_DATA").fetchone()[0],
            "ASSOC_DATA": cur.execute("select count(*) from ASSOC_DATA").fetchone()[0],
        },
        "outputs": {
            "dim_person": dim_count,
            "dim_person_coord": coord_rows,
            "fact_person_status": count(OUT_DIR / "fact_person_status.csv"),
            "fact_person_address": count(OUT_DIR / "fact_person_address.csv"),
            "fact_person_posting": count(OUT_DIR / "fact_person_posting.csv"),
            "fact_person_kin": count(OUT_DIR / "fact_person_kin.csv"),
            "fact_person_assoc": count(OUT_DIR / "fact_person_assoc.csv"),
            "dim_address": count(OUT_DIR / "dim_address.csv"),
        },
        "case_samples": {
            "case_person_ids": [1, 4],
            "status_sample_count": len([r for r in fact_status if r[0] in (1, 4)]),
            "posting_sample_count": len([r for r in fact_posting if r[0] in (1, 4)]),
        },
    }
    (OUT_DIR / "validation_summary.json").write_text(
        json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(json.dumps(validation, ensure_ascii=False, indent=2))
    conn.close()


if __name__ == "__main__":
    main()

