# -*- coding: utf-8 -*-
"""
北京大学门户 - 单位公告讣告爬虫 (v4 - raw URL params)
"""
import requests
import json
import time
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

PORTAL_URL = 'https://portal.pku.edu.cn/portal2017/'
PAGES_DIR = r'D:\虚拟C盘\study\0\pages'
OUTPUT_FILE = r'D:\虚拟C盘\study\0\obituaries_raw.json'
BATCH_SIZE = 200
REQUEST_DELAY = 0.25
MAX_RETRIES = 3

def create_session():
    s = requests.Session()
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    })
    s.get(PORTAL_URL, timeout=15)
    return s

def fetch_list(session, start, limit, keyword=''):
    url = f'https://portal.pku.edu.cn/portal2017/notice/retrAllDeptNotice.do?start={start}&limit={limit}&keyword={keyword}'
    for attempt in range(MAX_RETRIES):
        try:
            r = session.post(url, timeout=15)
            return r.json()
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2)
            else:
                print(f'  [ERROR] list start={start}: {e}')
                return None

def fetch_detail(session, notice_id):
    url = f'https://portal.pku.edu.cn/portal2017/notice/getDeptNoticeDetailById.do?id={notice_id}'
    for attempt in range(MAX_RETRIES):
        try:
            r = session.post(url, timeout=15)
            return r.json()
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2)
            else:
                print(f'  [ERROR] detail id={notice_id}: {e}')
                return None

def main():
    session = create_session()
    print(f'Session established')

    # Load existing
    existing = {}
    if os.path.exists(OUTPUT_FILE) and os.path.getsize(OUTPUT_FILE) > 10:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            for item in json.load(f):
                existing[item['id']] = item
        print(f'Loaded {len(existing)} existing obituaries')

    # Step 1: Scan all notices
    data = fetch_list(session, 0, 1)
    if not data:
        print('Failed to connect')
        return
    total = data.get('results', 0)
    print(f'Total notices: {total}')

    obituary_items = []
    scanned = 0
    for start in range(0, total, BATCH_SIZE):
        if scanned > 0 and scanned % 5000 == 0:
            session = create_session()
        data = fetch_list(session, start, BATCH_SIZE)
        if not data:
            continue
        rows = data.get('rows', [])
        for row in rows:
            if '\u8ba3' in row.get('Title', ''):
                obituary_items.append(row)
        scanned += len(rows)
        if scanned % 2000 == 0:
            print(f'  Scanned {scanned}/{total}, found {len(obituary_items)} obituaries')
        time.sleep(0.1)

    print(f'\nTotal obituaries found: {len(obituary_items)}')

    # Step 2: Fetch details
    new_ids = [o['Number'] for o in obituary_items if o['Number'] not in existing or not existing[o['Number']].get('html_content')]
    print(f'Need to fetch {len(new_ids)} details')

    fetched = 0
    for i, obit in enumerate(obituary_items):
        nid = obit['Number']
        if nid in existing and existing[nid].get('html_content'):
            continue

        if fetched > 0 and fetched % 80 == 0:
            session = create_session()

        detail_data = fetch_detail(session, nid)
        notice_detail = {}
        if detail_data and detail_data.get('success'):
            notice_detail = detail_data.get('notice', {})
            html = notice_detail.get('noticeContent', '')
            filepath = os.path.join(PAGES_DIR, f'{nid}.html')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)

        existing[nid] = {
            'id': nid,
            'title': obit.get('Title', ''),
            'list_time': obit.get('Time', ''),
            'department': obit.get('Department', ''),
            'type': obit.get('Type', ''),
            'doc_url': obit.get('DocUrl', ''),
            'file_name': notice_detail.get('fileName', ''),
            'file_no': notice_detail.get('fileNo', ''),
            'html_content': notice_detail.get('noticeContent', '')
        }
        fetched += 1
        if fetched % 20 == 0:
            print(f'  Fetched {fetched}/{len(new_ids)} details')
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(list(existing.values()), f, ensure_ascii=False, indent=2)
        time.sleep(REQUEST_DELAY)

    results = list(existing.values())
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f'\nDone! Saved {len(results)} obituaries')

if __name__ == '__main__':
    main()
