import pandas as pd
from pathlib import Path
ROOT = Path.cwd()
IN = ROOT / "output_cbdb_v1"
df = pd.read_csv(IN / "fact_person_assoc.csv", usecols=["c_assoc_desc_chn"], encoding="utf-8", on_bad_lines="skip")
df = df[df["c_assoc_desc_chn"] != "未詳"]
print(f"Total unique assoc_desc_chn: {df['c_assoc_desc_chn'].nunique()}")
print("\nAll unique values:")
for v in sorted(df["c_assoc_desc_chn"].unique()):
    print(f"  {v}")
