# -*- coding: utf-8 -*-
"""
北京大学讣告信息抽取程序 v2 - 改进版
"""
import json
import re
import csv
import os
import sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

INPUT_FILE = r'D:\虚拟C盘\study\0\obituaries_raw.json'
OUTPUT_CSV = r'D:\虚拟C盘\study\0\obituaries_structured.csv'
OUTPUT_JSON = r'D:\虚拟C盘\study\0\obituaries_structured.json'

def clean_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    # Collapse multiple spaces/newlines into single space
    text = re.sub(r'\s+', ' ', text)
    return text

def extract_name(title, text):
    title_clean = title.strip().replace('\u200b', '').replace('\u3000', '').replace(' ', '')
    if title_clean in ['讣告', '讣\u3000告', '讣  告']:
        lines = text.split('\n')
        for line in lines[:8]:
            line = line.strip()
            if not line:
                continue
            # "XXX同志/教授因..." or "北京大学XXX同志/教授"
            m = re.search(r'(?:北京大学)?(?:物理|化学|数学|中文|历史|哲学|经济|法学|外语|信息|生命|地球|医学|护理|药学|光华|政府|教育|心理|艺术|新闻|考古|社会|体育|工学|软件|马克思主义|城市|环境|建筑|国际关系|人口|歌剧|对外汉语|继续教育|深圳研究生院)?[\u4e00-\u9fff]*?([\u4e00-\u9fff]{2,4})(?:同志|教授|副教授|讲师|先生|老师|院士|研究员)\s*(?:因|于)', line)
            if m:
                return m.group(1)
            # Try simpler: "XXX同志/教授"
            m = re.search(r'([\u4e00-\u9fff]{2,4})(?:同志|教授|副教授|先生|老师|院士)\s*(?:因|于|，|。)', line)
            if m:
                return m.group(1)
        return ''

    title_clean = re.sub(r'^【讣告】\s*', '', title_clean)
    title_clean = re.sub(r'^沉痛悼念\s*', '', title_clean)

    # XXX + role + 讣告
    m = re.match(r'^([\u4e00-\u9fff\u00b7·]{2,6})(?:教授|副教授|讲师|老师|同志|先生|院士|研究员|高级工程师|高级实验师|实验师)讣', title_clean)
    if m:
        return m.group(1).replace('\u200b', '').strip()

    # XXX讣告
    m = re.match(r'^([\u4e00-\u9fff]{2,4})讣', title_clean)
    if m:
        return m.group(1)

    # Fallback
    lines = text.split('\n')
    for line in lines[:5]:
        line = line.strip()
        m = re.search(r'([\u4e00-\u9fff]{2,4})(?:同志|教授|副教授|先生|老师|院士|研究员)\s*(?:因|于)', line)
        if m:
            return m.group(1)
    return ''

def extract_title_role(title, text, name):
    title_clean = title.strip().replace('\u200b', '').replace('\u3000', '').replace(' ', '')
    title_clean = re.sub(r'^【讣告】\s*', '', title_clean)
    title_clean = re.sub(r'^沉痛悼念\s*', '', title_clean)

    # From title directly
    for role in ['院士', '资深教授', '教授', '副教授', '讲师', '研究员', '高级工程师', '高级实验师', '实验师', '工程师',
                 '先生', '同志', '老师']:
        if name and f'{name}{role}' in title_clean:
            return role
        if role + '讣' in title_clean:
            return role

    # "讣告" alone - check content
    if title_clean in ['讣告']:
        first_text = '\n'.join(text.split('\n')[:10])
        for role in ['院士', '资深教授', '教授', '副教授', '研究员', '讲师', '老师', '先生', '同志']:
            if role in first_text:
                return role

    return ''

def extract_dates(text):
    birth_date = ''
    death_date = ''

    # Death date patterns
    death_patterns = [
        r'于\s*(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日[^。\n]*?(?:逝世|辞世|去世|离世|安详辞世|安详离世|与世长辞|永远离开|病逝|罹难|辞世|停止呼吸|心脏停止跳动)',
        r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日[^。\n]{0,40}?(?:逝世|辞世|去世|离世|病逝|与世长辞|罹难|停止呼吸)',
        r'(?:逝世|辞世|去世|离世)[^。\n]*?(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日',
    ]
    for pattern in death_patterns:
        m = re.search(pattern, text)
        if m:
            death_date = f'{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}'
            break

    # Birth date patterns
    birth_patterns = [
        r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日\s*(?:出生于|生于)',
        r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(?:出生于|生于)',
        r'(?:出生于|生于)\s*(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日',
        r'(?:出生于|生于)\s*(\d{4})\s*年\s*(\d{1,2})\s*月',
    ]
    for pattern in birth_patterns:
        m = re.search(pattern, text)
        if m:
            groups = m.groups()
            if len(groups) >= 3:
                birth_date = f'{groups[0]}-{int(groups[1]):02d}-{int(groups[2]):02d}'
            elif len(groups) >= 2:
                birth_date = f'{groups[0]}-{int(groups[1]):02d}-00'
            break

    return birth_date, death_date

def extract_age(text):
    patterns = [r'享年\s*(\d{1,3})\s*岁', r'终年\s*(\d{1,3})\s*岁']
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            return int(m.group(1))
    return None

def extract_native_place(text):
    patterns = [
        r'籍贯\s*(?:为|是|：)?\s*([\u4e00-\u9fff]{2,}(?:省|市|自治区)?[\u4e00-\u9fff]*(?:市|县|区|旗)?)',
        r'(\d{4})\s*年\s*\d{1,2}\s*月\s*(?:出生于|生于)\s*([\u4e00-\u9fff]+(?:省|市|自治区)?[\u4e00-\u9fff]*(?:市|县|区)?)',
        r'(?:出生于|生于)\s*([\u4e00-\u9fff]+(?:省|市|自治区)?[\u4e00-\u9fff]*(?:市|县|区)?)',
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            groups = m.groups()
            result = groups[-1]
            # Filter out "北京大学XX" etc
            if '大学' not in result and '学院' not in result and len(result) >= 2:
                return result
    return ''

def extract_province(native_place):
    if not native_place:
        return ''
    provinces = {
        '北京': '北京', '天津': '天津', '上海': '上海', '重庆': '重庆',
        '河北': '河北', '山西': '山西', '辽宁': '辽宁', '吉林': '吉林', '黑龙江': '黑龙江',
        '江苏': '江苏', '浙江': '浙江', '安徽': '安徽', '福建': '福建', '江西': '江西',
        '山东': '山东', '河南': '河南', '湖北': '湖北', '湖南': '湖南',
        '广东': '广东', '海南': '海南', '四川': '四川', '贵州': '贵州', '云南': '云南',
        '陕西': '陕西', '甘肃': '甘肃', '青海': '青海', '台湾': '台湾',
        '内蒙古': '内蒙古', '广西': '广西', '西藏': '西藏', '宁夏': '宁夏', '新疆': '新疆',
        '香港': '香港', '澳门': '澳门'
    }
    for key, val in provinces.items():
        if key in native_place:
            return val
    return native_place

def extract_education(text):
    for level in ['博士后', '博士', '硕士', '学士']:
        if level in text:
            return level
    return ''

def extract_undergraduate_school(text):
    # Pattern: "XXXX年毕业于/考入XXX大学XX系"
    patterns = [
        r'\d{4}\s*年[^。]*?(?:毕业于|考入|入读|进入)\s*([\u4e00-\u9fff]+(?:大学|学院))',
        r'(?:毕业于|考入|入读|进入|就读于)\s*([\u4e00-\u9fff]+(?:大学|学院))',
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            school = m.group(1).strip()
            if len(school) >= 3 and '北京大学' not in school:
                return school

    # Find first non-PKU university
    schools = re.findall(r'([\u4e00-\u9fff]{2,8}(?:大学|学院))', text)
    for s in schools:
        if s not in ['北京大学', '清华大学'] and len(s) >= 3:
            return s
    return ''

def extract_department(text, title):
    patterns = [
        r'北京大学\s*([\u4e00-\u9fff]+(?:学院|系|研究所|研究院|医院|中心|部|馆))',
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            dept = m.group(1)
            # Clean up
            if len(dept) >= 2:
                return '北京大学' + dept
    return ''

def extract_publishing_org(text):
    patterns = [
        r'([\u4e00-\u9fff]+(?:治丧委员会|治丧办公室|治丧小组))',
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            return m.group(1)
    return ''

def extract_pku_work_years(text):
    join_year = None
    join_patterns = [
        r'(\d{4})\s*年[^。]*?(?:到|进入|入职|来|调入)\s*北京大学',
        r'(?:在|于)\s*北京大学[^。]*?(\d{4})\s*年[^。]*?(?:任教|工作|留校)',
        r'北京大学[^。]*?(\d{4})\s*年[^。]*?(?:留校|任教|工作|入职)',
        r'(\d{4})\s*年[^。]*?(?:起|开始)[^。]*?北京大学',
        r'(\d{4})\s*年\s*\d{1,2}\s*月[^。]*?(?:来|到|进入|起在|起于)\s*北京大学',
    ]
    for pattern in join_patterns:
        m = re.search(pattern, text)
        if m:
            year = int(m.group(1))
            if 1920 <= year <= 2026:
                join_year = year
                break

    end_year = None
    end_patterns = [
        r'(\d{4})\s*年[^。]*?(?:逝世|辞世|去世)',
        r'(\d{4})\s*年[^。]*?(?:退休|离休|荣休)',
    ]
    for pattern in end_patterns:
        m = re.search(pattern, text)
        if m:
            year = int(m.group(1))
            if 1920 <= year <= 2026:
                end_year = year
                break

    if join_year and end_year:
        return end_year - join_year
    return None

def extract_gender(text, name):
    # Explicit markers in first 500 chars
    first = text[:800]
    if '她' in first and '他' not in first[:first.index('她')] if '她' in first else False:
        return '女'
    if re.search(r'女(?:士|性|教授|老师|同志|先生)', first):
        return '女'
    if re.search(r'男(?:士|性|教授|老师|同志)', first):
        return '男'
    if '先生' in first[:300]:
        return '男'
    if '女士' in first[:300]:
        return '女'

    # Pronoun-based
    male_pronouns = len(re.findall(r'(?<!她)(?:他|先生|同志)', first[:500]))
    female_pronouns = len(re.findall(r'她|女士', first[:500]))
    if male_pronouns > female_pronouns and male_pronouns >= 2:
        return '男'
    if female_pronouns > male_pronouns and female_pronouns >= 2:
        return '女'

    # Name-based heuristic (very rough)
    if name:
        last = name[-1]
        female_chars = '芳娟敏静丽萍红燕玲桂花莉梅琳霞珍娣慧淑媛兰英翠珠莲云凤瑞洁雅蕾颖露雪冰清素华碧倩婷瑶倩薇岚'
        male_chars = '伟强磊鑫军明勇杰峰刚辉飞龙林光志海波宁生才良福德成文武斌祥和松柏栋梁坤'
        if last in female_chars:
            return '女'
        if last in male_chars:
            return '男'

    return ''

def parse_obituary(item):
    title = item['title']
    html = item.get('html_content', '')
    text = clean_html(html)

    name = extract_name(title, text)
    birth_date, death_date = extract_dates(text)
    age = extract_age(text)
    native_place = extract_native_place(text)
    province = extract_province(native_place)
    role = extract_title_role(title, text, name)
    education = extract_education(text)
    undergrad_school = extract_undergraduate_school(text)
    department = extract_department(text, title)
    publishing_org = extract_publishing_org(text)
    pku_years = extract_pku_work_years(text)
    gender = extract_gender(text, name)

    return {
        'id': item['id'],
        'title': title,
        'name': name,
        'gender': gender,
        'birth_date': birth_date,
        'death_date': death_date,
        'age': age,
        'native_place': native_place,
        'province': province,
        'role': role,
        'education': education,
        'undergraduate_school': undergrad_school,
        'department': department,
        'publishing_org': publishing_org,
        'publish_date': item.get('list_time', '')[:10],
        'pku_work_years': pku_years,
    }

def main():
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    print(f'Parsing {len(raw_data)} obituaries...')
    results = []
    for item in raw_data:
        parsed = parse_obituary(item)
        results.append(parsed)

    # Stats
    fields = ['name', 'birth_date', 'death_date', 'age', 'native_place', 'role',
              'education', 'undergraduate_school', 'department', 'publishing_org', 'gender']
    print('\nField coverage:')
    for field in fields:
        count = sum(1 for r in results if r.get(field))
        print(f'  {field}: {count}/{len(results)} ({100*count/len(results):.1f}%)')

    # Save
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    if results:
        with open(OUTPUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)

    print(f'\nSaved {len(results)} records')

if __name__ == '__main__':
    main()
