# -*- coding: utf-8 -*-
import pandas as pd
import os

base = os.path.join(r'D:\虚拟C盘\study\人工智能与计算思维大作业', 'output_cbdb_v1')
dim = pd.read_csv(os.path.join(base, 'dim_person.csv'), encoding='utf-8-sig', usecols=['c_personid', 'c_name_chn', 'dynasty_chn'])
print('dim_person rows:', len(dim))

assoc = pd.read_csv(os.path.join(base, 'fact_person_assoc.csv'), encoding='utf-8-sig', usecols=['c_personid', 'c_assoc_id'])
all_ids = set(assoc['c_personid']) | set(assoc['c_assoc_id'])
dim_ids = set(dim['c_personid'])
matched = all_ids & dim_ids
print(f'assoc unique persons: {len(all_ids)}')
print(f'matched in dim_person: {len(matched)}')
print(f'coverage: {len(matched)/len(all_ids)*100:.1f}%')

assoc_full = pd.read_csv(os.path.join(base, 'fact_person_assoc.csv'), encoding='utf-8-sig')
assoc_full = assoc_full.merge(dim[['c_personid', 'dynasty_chn']], on='c_personid', how='left')
print()
print('Assoc by dynasty (top 10):')
dy_counts = assoc_full['dynasty_chn'].value_counts().head(10)
print(dy_counts.to_string())

# Kinship
kin = pd.read_csv(os.path.join(base, 'fact_person_kin.csv'), encoding='utf-8-sig', usecols=['c_personid', 'c_kin_id'])
kin_all = set(kin['c_personid']) | set(kin['c_kin_id'])
kin_matched = kin_all & dim_ids
print(f'\nkin unique persons: {len(kin_all)}')
print(f'matched in dim_person: {len(kin_matched)}')
print(f'coverage: {len(kin_matched)/len(kin_all)*100:.1f}%')