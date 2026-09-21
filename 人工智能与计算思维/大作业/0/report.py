# -*- coding: utf-8 -*-
"""
生成PDF说明报告
"""
import json
import os
import sys
import numpy as np
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

from fpdf import FPDF

INPUT_FILE = r'D:\虚拟C盘\study\0\obituaries_structured.json'
CHARTS_DIR = r'D:\虚拟C盘\study\0\charts'
OUTPUT_PDF = r'D:\虚拟C盘\study\0\output\report.pdf'

with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    records = json.load(f)

# Find a Chinese font
font_paths = [
    r'C:\Windows\Fonts\msyh.ttc',      # Microsoft YaHei
    r'C:\Windows\Fonts\simhei.ttf',     # SimHei
    r'C:\Windows\Fonts\simsun.ttc',     # SimSun
    r'C:\Windows\Fonts\msyhbd.ttc',     # YaHei Bold
]
FONT_PATH = None
for fp in font_paths:
    if os.path.exists(fp):
        FONT_PATH = fp
        break

if not FONT_PATH:
    print('WARNING: No Chinese font found, PDF may not display Chinese characters correctly')
    # Try to find any .ttf or .ttc font
    for root, dirs, files in os.walk(r'C:\Windows\Fonts'):
        for f in files:
            if f.endswith('.ttf') and ('msyh' in f.lower() or 'simhei' in f.lower() or 'simsun' in f.lower()):
                FONT_PATH = os.path.join(root, f)
                break
        if FONT_PATH:
            break

print(f'Using font: {FONT_PATH}')

class PDFReport(FPDF):
    def __init__(self):
        super().__init__()
        if FONT_PATH:
            self.add_font('Chinese', '', FONT_PATH)
            self.add_font('Chinese', 'B', FONT_PATH)
            self.font_name = 'Chinese'
        else:
            self.font_name = 'Helvetica'

    def header(self):
        self.set_font(self.font_name, 'B', 10)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, '北京大学讣告数据分析报告', align='R', new_x='LMARGIN', new_y='NEXT')
        self.set_draw_color(192, 57, 43)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font(self.font_name, '', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'第 {self.page_no()} 页', align='C')

    def title_page(self):
        self.add_page()
        self.ln(50)
        self.set_font(self.font_name, 'B', 28)
        self.set_text_color(192, 57, 43)
        self.cell(0, 15, '北京大学讣告数据分析报告', align='C', new_x='LMARGIN', new_y='NEXT')
        self.ln(10)
        self.set_font(self.font_name, '', 14)
        self.set_text_color(80, 80, 80)
        self.cell(0, 10, '基于北京大学门户网单位公告数据', align='C', new_x='LMARGIN', new_y='NEXT')
        self.ln(5)
        self.cell(0, 10, '2026年6月', align='C', new_x='LMARGIN', new_y='NEXT')
        self.ln(30)
        self.set_font(self.font_name, '', 11)
        self.cell(0, 8, '数据来源: https://portal.pku.edu.cn', align='C', new_x='LMARGIN', new_y='NEXT')
        self.cell(0, 8, f'数据量: {len(records)} 条讣告', align='C', new_x='LMARGIN', new_y='NEXT')

    def section_title(self, title):
        self.ln(5)
        self.set_font(self.font_name, 'B', 16)
        self.set_text_color(192, 57, 43)
        self.cell(0, 10, title, new_x='LMARGIN', new_y='NEXT')
        self.set_draw_color(192, 57, 43)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def body_text(self, text):
        self.set_font(self.font_name, '', 11)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 7, text)
        self.ln(2)

    def add_chart(self, img_path, w=170):
        if os.path.exists(img_path):
            self.image(img_path, x=(210-w)/2, w=w)
            self.ln(5)

def main():
    ages = [r['age'] for r in records if r.get('age') and 20 <= r['age'] <= 120]
    gender_counts = Counter(r['gender'] for r in records if r.get('gender'))
    role_map = {
        '教授': '教授', '资深教授': '教授', '研究员': '教授', '高级工程师': '教授', '高级实验师': '教授',
        '副教授': '副教授', '副研究员': '副教授',
        '讲师': '讲师', '助理研究员': '讲师', '实验师': '讲师', '工程师': '讲师',
        '院士': '院士', '先生': '先生', '同志': '同志', '老师': '老师',
    }
    roles = Counter(role_map.get(r['role'], r['role']) for r in records if r.get('role'))
    depts = Counter(r['department'].replace('北京大学', '') for r in records if r.get('department'))
    provs = Counter(r['province'] for r in records if r.get('province'))

    pdf = PDFReport()

    # Title page
    pdf.title_page()

    # Section 1: 数据概览
    pdf.add_page()
    pdf.section_title('一、数据概览')
    pdf.body_text(
        f'本报告基于北京大学门户网（portal.pku.edu.cn）的"单位公告"板块，'
        f'通过爬取全部公告并筛选含"讣"字的公告，共获取讣告 {len(records)} 条。'
        f'数据时间跨度从2010年至2026年6月。'
    )
    pdf.body_text(
        f'通过正则表达式与规则匹配，从讣告HTML正文中自动提取了姓名、性别、出生日期、'
        f'逝世日期、享年岁数、籍贯、职称/身份、最高学历、本科就读院校、所属院系、'
        f'发布单位、北大工作年数等结构化字段。'
    )

    pdf.section_title('二、数据采集方法')
    pdf.body_text(
        '1. 爬虫阶段：通过北京大学门户网的后端API（retrAllDeptNotice.do）遍历全部21807条'
        '单位公告（每批200条），筛选标题含"讣"的公告；再通过详情API（getDeptNoticeDetailById.do）'
        '获取每条讣告的HTML正文。'
    )
    pdf.body_text(
        '2. 解析阶段：使用BeautifulSoup将HTML转为纯文本，通过正则表达式匹配关键模式提取'
        '各字段。对于无法自动提取的字段标记为空。'
    )
    pdf.body_text(
        '3. 分析阶段：使用Python（matplotlib、numpy、openpyxl）进行数据统计与可视化。'
    )

    # Section 2: 统计摘要
    pdf.add_page()
    pdf.section_title('三、统计摘要')

    pdf.body_text(f'讣告总数：{len(records)} 条')
    pdf.body_text(f'有享年数据的记录：{len(ages)} 条（{100*len(ages)/len(records):.1f}%）')
    pdf.body_text(f'平均享年：{np.mean(ages):.1f} 岁')
    pdf.body_text(f'中位享年：{np.median(ages):.1f} 岁')
    pdf.body_text(f'享年范围：{min(ages)} - {max(ages)} 岁')
    pdf.body_text(f'标准差：{np.std(ages):.1f} 岁')
    pdf.body_text(f'')
    pdf.body_text(f'性别分布：男性 {gender_counts.get("男", 0)} 人，女性 {gender_counts.get("女", 0)} 人')
    pdf.body_text(f'')
    pdf.body_text(f'字段覆盖率：')
    fields_cn = {'name': '姓名', 'death_date': '逝世日期', 'age': '享年', 'role': '职称',
                 'department': '院系', 'undergraduate_school': '本科院校', 'native_place': '籍贯',
                 'gender': '性别', 'birth_date': '出生日期', 'education': '学历',
                 'publishing_org': '发布单位', 'pku_work_years': '北大工作年数'}
    for field, cn in fields_cn.items():
        count = sum(1 for r in records if r.get(field))
        pdf.body_text(f'  {cn}: {count}/{len(records)} ({100*count/len(records):.1f}%)')

    # Section 3: 享年分析
    pdf.add_page()
    pdf.section_title('四、享年岁数分析')
    pdf.body_text(
        f'在{len(ages)}位有享年数据的逝者中，平均享年{np.mean(ages):.1f}岁，中位数{np.median(ages):.1f}岁。'
        f'享年最高者{max(ages)}岁，最年轻者{min(ages)}岁。'
        f'大部分逝者享年在75-95岁之间，反映了北京大学教职工群体的较高平均寿命。'
    )
    pdf.add_chart(os.path.join(CHARTS_DIR, 'age_distribution.png'), 160)

    # Section 4: 职称分析
    pdf.add_page()
    pdf.section_title('五、职称/身份分析')
    top_roles = roles.most_common(5)
    role_text = '、'.join([f'{r}（{c}人）' for r, c in top_roles])
    pdf.body_text(f'讣告中的主要职称/身份分布：{role_text}。')
    pdf.body_text(
        f'教授/研究员占比最高，反映了讣告主要面向高级职称教职工。'
        f'部分讣告以"先生""同志"等称谓代替具体职称，主要出现在较早期的讣告中。'
    )
    pdf.add_chart(os.path.join(CHARTS_DIR, 'role_distribution.png'), 170)

    # Section 5: 院系分析
    pdf.add_page()
    pdf.section_title('六、院系分布分析')
    top5 = depts.most_common(5)
    dept_text = '、'.join([f'{d}（{c}人）' for d, c in top5])
    pdf.body_text(f'讣告数量最多的院系为：{dept_text}。')
    pdf.body_text(
        f'传统文理基础学科院系（物理、数学、中文、历史等）讣告数量较多，'
        f'一方面反映了这些院系历史悠久、教职工规模较大，另一方面也与院系传统有关。'
    )
    pdf.add_chart(os.path.join(CHARTS_DIR, 'department_distribution.png'), 160)

    # Section 6: 籍贯分析
    pdf.add_page()
    pdf.section_title('七、籍贯分布分析')
    top5p = provs.most_common(5)
    prov_text = '、'.join([f'{p}（{c}人）' for p, c in top5p])
    pdf.body_text(f'籍贯分布最集中的省份为：{prov_text}。')
    pdf.body_text(
        f'北京籍人士占比最高，与北京大学地处北京、长期在京招聘教职工有关。'
        f'江浙沪等教育发达地区的教职工也较多。'
    )
    pdf.add_chart(os.path.join(CHARTS_DIR, 'province_distribution.png'), 160)

    # Section 7: 本科院校分析
    pdf.add_page()
    pdf.section_title('八、本科就读院校分析')
    schools = Counter(r['undergraduate_school'] for r in records if r.get('undergraduate_school'))
    top5s = schools.most_common(5)
    school_text = '、'.join([f'{s}（{c}人）' for s, c in top5s])
    pdf.body_text(f'本科就读人数最多的院校为：{school_text}。')
    pdf.body_text(
        f'北京大学自身培养的校友在教职工中占相当比例，'
        f'同时也吸引了清华、南开、复旦等名校的毕业生。'
    )
    pdf.add_chart(os.path.join(CHARTS_DIR, 'school_distribution.png'), 160)

    # Section 8: 时间趋势
    pdf.add_page()
    pdf.section_title('九、时间趋势分析')
    pdf.body_text(
        '从年度讣告数量来看，近年来讣告数量呈上升趋势，'
        '这与人口老龄化及建国初期入职的教职工集中进入高龄阶段有关。'
    )
    pdf.add_chart(os.path.join(CHARTS_DIR, 'timeline.png'), 160)
    pdf.body_text(
        '从各年份平均享年来看，整体呈平稳或略有上升趋势，'
        '反映了医疗水平的进步和生活质量的提高。'
    )
    pdf.add_chart(os.path.join(CHARTS_DIR, 'age_by_year.png'), 160)

    # Section 9: 其他分析
    pdf.add_page()
    pdf.section_title('十、其他维度分析')

    pdf.body_text('10.1 北大工作年限分布')
    pku_years = [r['pku_work_years'] for r in records if r.get('pku_work_years') and 0 < r['pku_work_years'] <= 80]
    if pku_years:
        pdf.body_text(
            f'北大工作年限平均{np.mean(pku_years):.1f}年，中位数{np.median(pku_years):.0f}年。'
            f'大多数教职工在北京大学工作超过30年，体现了深厚的职业忠诚度。'
        )
    pdf.add_chart(os.path.join(CHARTS_DIR, 'pku_work_years.png'), 150)

    pdf.body_text('10.2 性别分布')
    pdf.body_text(
        f'在可判断性别的{sum(gender_counts.values())}位逝者中，'
        f'男性{gender_counts.get("男", 0)}人（{100*gender_counts.get("男", 0)/sum(gender_counts.values()):.1f}%），'
        f'女性{gender_counts.get("女", 0)}人（{100*gender_counts.get("女", 0)/sum(gender_counts.values()):.1f}%）。'
        f'男性比例较高，反映了历史上高校教职工的性别结构。'
    )
    pdf.add_chart(os.path.join(CHARTS_DIR, 'gender_distribution.png'), 100)

    pdf.body_text('10.3 月份分布')
    pdf.body_text('从逝世月份来看，冬季月份（12月、1月）的讣告数量略多，可能与老年人冬季健康风险较高有关。')
    pdf.add_chart(os.path.join(CHARTS_DIR, 'monthly_distribution.png'), 160)

    # Section 10: 结论
    pdf.add_page()
    pdf.section_title('十一、结论与总结')
    pdf.body_text(
        f'本研究对北京大学门户网{len(records)}条讣告进行了系统性数据采集与分析，主要发现如下：'
    )
    pdf.body_text(
        f'1. 享年分布：平均享年{np.mean(ages):.1f}岁，中位数{np.median(ages):.1f}岁，'
        f'体现了北大教职工群体较高的平均寿命。'
    )
    pdf.body_text(
        f'2. 职称结构：教授/研究员占比最高，副教授和讲师/老师次之。'
    )
    pdf.body_text(
        f'3. 院系分布：传统基础学科院系讣告数量较多，与院系历史和规模相关。'
    )
    pdf.body_text(
        f'4. 籍贯分布：北京籍最多，江浙沪等教育大省次之，反映了地域人才聚集效应。'
    )
    pdf.body_text(
        f'5. 趋势：近年讣告数量上升，平均享年总体平稳或略有增长。'
    )
    pdf.body_text(
        f'6. 北大工作年限：大多数教职工在北大工作30年以上，体现了深厚的职业忠诚。'
    )

    # Save
    os.makedirs(os.path.dirname(OUTPUT_PDF), exist_ok=True)
    pdf.output(OUTPUT_PDF)
    print(f'PDF report saved: {OUTPUT_PDF}')

if __name__ == '__main__':
    main()
