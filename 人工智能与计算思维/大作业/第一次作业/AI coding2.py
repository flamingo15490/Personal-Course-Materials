"""
作品质量深度分析系统（已修复格式错误和中文字体问题）
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib
from scipy import stats
import warnings
import os
warnings.filterwarnings('ignore')

# ==================== 中文字体解决方案 ====================
def setup_chinese_font():
    """
    自动设置中文字体，解决中文显示为方块的问题
    返回：是否成功设置中文字体
    """
    try:
        # 方法1：使用系统自带字体
        font_options = [
            'SimHei',              # Windows 黑体
            'Microsoft YaHei',     # Windows 微软雅黑
            'DengXian',            # Windows 等线
            'FangSong',            # Windows 仿宋
            'KaiTi',               # Windows 楷体
            'STHeiti',             # macOS 黑体
            'Hiragino Sans GB',    # macOS 冬青黑体
            'PingFang SC',         # macOS 苹方
            'WenQuanYi Zen Hei',   # Linux 文泉驿
            'DejaVu Sans',         # 跨平台
            'Arial Unicode MS',    # 跨平台
        ]

        # 尝试设置字体
        for font in font_options:
            try:
                plt.rcParams['font.sans-serif'] = [font]
                plt.rcParams['axes.unicode_minus'] = False

                # 测试字体是否有效
                fig, ax = plt.subplots(figsize=(1, 1))
                ax.text(0.5, 0.5, '测试中文', fontname=font, ha='center', va='center')
                plt.close(fig)

                print(f"✓ 成功设置中文字体: {font}")
                return True
            except:
                continue

        # 如果都不行，使用默认字体
        print("⚠ 警告: 未找到中文字体，图表将显示为英文")
        return False

    except Exception as e:
        print(f"字体设置失败: {e}")
        return False

# 初始化字体设置
CHINESE_ENABLED = setup_chinese_font()

# 设置图表样式
plt.rcParams['figure.figsize'] = (14, 10)
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'
sns.set_style("whitegrid")

# 颜色方案
COLOR_PALETTE = {
    '高质量': '#2ca02c',    # 绿色
    '中等质量': '#ff7f0e',  # 橙色
    '低质量': '#d62728',    # 红色
    '强烈推荐': '#1f77b4',  # 蓝色
    '推荐': '#ffbb78',      # 浅橙色
    '不推荐': '#9467bd'     # 紫色
}

class WorkQualityAnalyzer:
    """作品质量分析器"""

    def __init__(self, data_file='runResult00.txt'):
        """初始化分析器"""
        self.work_df = self.load_work_data(data_file)
        if not self.work_df.empty:
            self.prepare_data()

    def load_work_data(self, file_path):
        """加载作品数据"""
        try:
            print(f"正在加载文件: {file_path}")

            # 尝试不同编码和分隔符
            try:
                # 尝试UTF-8编码，空格分隔
                df = pd.read_csv(file_path, delim_whitespace=True, encoding='utf-8')
                print("✓ 使用UTF-8编码和空格分隔符成功加载")
            except:
                try:
                    # 尝试GBK编码
                    df = pd.read_csv(file_path, delim_whitespace=True, encoding='gbk')
                    print("✓ 使用GBK编码和空格分隔符成功加载")
                except:
                    try:
                        # 尝试制表符分隔
                        df = pd.read_csv(file_path, sep='\t', encoding='utf-8')
                        print("✓ 使用UTF-8编码和制表符分隔符成功加载")
                    except:
                        # 如果都不行，尝试自动检测
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()

                        # 解析数据
                        data = []
                        for i, line in enumerate(lines):
                            line = line.strip()
                            if line and not any(keyword in line for keyword in ['作品编号', '作品类别']):
                                parts = line.split()
                                if len(parts) >= 3:
                                    data.append(parts[:3])  # 只取前三列

                        if data:
                            df = pd.DataFrame(data, columns=['作品编号', '得分构型', '作品类别'])
                            print("✓ 使用自定义解析成功加载")
                        else:
                            raise ValueError("文件内容为空或格式错误")

            # 清理数据
            df = df.dropna()  # 删除空行
            df = df.reset_index(drop=True)

            print(f"✓ 成功加载 {len(df)} 条作品记录")
            print("数据列:", df.columns.tolist())
            print("前5行数据:")
            print(df.head())

            return df

        except Exception as e:
            print(f"❌ 加载数据失败: {e}")
            print("将创建示例数据进行分析演示...")
            return self.create_sample_data()

    def create_sample_data(self):
        """创建示例数据用于演示"""
        print("⚠ 注意：正在使用示例数据，请确保您的数据格式正确")

        # 创建示例数据
        np.random.seed(42)

        # 作品类别
        categories = ['大数据应用', '人工智能应用', '软件应用与开发',
                     '数媒动漫与短片', '数媒静态设计', '物联网应用']

        # 得分构型
        patterns = ['000', '100', '110', '111', '200', '210', '211', '220', '221', '222']
        pattern_weights = [0.05, 0.1, 0.15, 0.2, 0.05, 0.1, 0.15, 0.05, 0.1, 0.05]

        data = []
        for i in range(200):  # 200件作品
            work_id = f'W{i+1:04d}'
            category = np.random.choice(categories, p=[0.2, 0.2, 0.15, 0.15, 0.15, 0.15])
            pattern = np.random.choice(patterns, p=pattern_weights)
            data.append([work_id, pattern, category])

        df = pd.DataFrame(data, columns=['作品编号', '得分构型', '作品类别'])
        print("示例数据创建完成，共200条记录")

        return df

    def prepare_data(self):
        """准备和清洗数据"""
        print("\n正在准备数据...")

        # 确保得分构型是字符串
        self.work_df['得分构型'] = self.work_df['得分构型'].astype(str)

        # 清理数据：移除非数字字符，只保留三位数字
        def clean_pattern(pattern):
            pattern_str = str(pattern)
            # 只保留数字
            digits = ''.join(filter(str.isdigit, pattern_str))
            # 如果不足3位，补齐
            if len(digits) == 3:
                return digits
            elif len(digits) > 3:
                return digits[:3]  # 取前三位
            else:
                return '000'  # 默认值

        self.work_df['得分构型'] = self.work_df['得分构型'].apply(clean_pattern)

        # 计算总分
        def calculate_total_score(pattern):
            try:
                return sum(int(digit) for digit in pattern)
            except:
                return 0

        self.work_df['总分'] = self.work_df['得分构型'].apply(calculate_total_score)

        # 计算构型特征
        def pattern_to_list(pattern):
            try:
                return [int(digit) for digit in str(pattern)]
            except:
                return [0, 0, 0]

        self.work_df['构型列表'] = self.work_df['得分构型'].apply(pattern_to_list)

        # 计算构型特征
        self.work_df['最高分'] = self.work_df['构型列表'].apply(lambda x: max(x) if x else 0)
        self.work_df['最低分'] = self.work_df['构型列表'].apply(lambda x: min(x) if x else 0)
        self.work_df['平均分'] = self.work_df['总分'] / 3
        self.work_df['评分差异'] = self.work_df['最高分'] - self.work_df['最低分']

        # 判断作品质量等级
        def classify_quality(total_score):
            if total_score >= 5:
                return '高质量'
            elif total_score >= 3:
                return '中等质量'
            else:
                return '低质量'

        self.work_df['质量等级'] = self.work_df['总分'].apply(classify_quality)

        # 判断是否为争议作品
        self.work_df['争议作品'] = self.work_df['构型列表'].apply(
            lambda x: (0 in x) and (2 in x) if x else False
        )

        # 判断是否为高风险作品（如200构型）
        self.work_df['高风险作品'] = self.work_df['得分构型'] == '200'

        print("✓ 数据准备完成")
        print(f"- 作品总数: {len(self.work_df)}")
        print(f"- 作品类别数: {self.work_df['作品类别'].nunique()}")
        print(f"- 得分构型种类: {self.work_df['得分构型'].nunique()}")
        print(f"- 总分范围: {self.work_df['总分'].min()} - {self.work_df['总分'].max()}")

    def part_two_quality_analysis(self):
        """
        二、作品质量分析（总体分析）
        这部分分析整个数据集的作品质量特征
        """
        print("\n" + "="*60)
        print("二、作品质量分析（总体分析）")
        print("="*60)

        if self.work_df.empty:
            print("⚠ 没有可分析的数据")
            return None

        # 创建分析图表
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))

        if CHINESE_ENABLED:
            fig.suptitle('二、作品质量分析（总体分析）', fontsize=16, fontweight='bold')
        else:
            fig.suptitle('Part 2: Overall Quality Analysis', fontsize=16, fontweight='bold')

        # 1.1 总分分布直方图
        ax1 = axes[0, 0]
        scores = self.work_df['总分'].value_counts().sort_index()
        bars = ax1.bar(scores.index, scores.values, color='skyblue', edgecolor='black', alpha=0.8)

        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom', fontsize=10)

        if CHINESE_ENABLED:
            ax1.set_xlabel('总分（0-6分）', fontsize=12)
            ax1.set_ylabel('作品数量', fontsize=12)
            ax1.set_title('作品总分分布', fontsize=14, fontweight='bold')
        else:
            ax1.set_xlabel('Total Score (0-6)', fontsize=12)
            ax1.set_ylabel('Number of Works', fontsize=12)
            ax1.set_title('Distribution of Total Scores', fontsize=14, fontweight='bold')

        ax1.set_xticks(range(0, 7))
        ax1.grid(True, alpha=0.3, linestyle='--')

        # 1.2 质量等级分布饼图
        ax2 = axes[0, 1]
        quality_counts = self.work_df['质量等级'].value_counts()
        colors = ['#4CAF50', '#FFC107', '#F44336']  # 绿、黄、红

        if CHINESE_ENABLED:
            labels = quality_counts.index.tolist()
        else:
            # 英文标签
            label_mapping = {'高质量': 'High Quality', '中等质量': 'Medium Quality', '低质量': 'Low Quality'}
            labels = [label_mapping.get(label, label) for label in quality_counts.index]

        wedges, texts, autotexts = ax2.pie(quality_counts.values, labels=labels,
                                          autopct='%1.1f%%', colors=colors, startangle=90)

        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        if CHINESE_ENABLED:
            ax2.set_title('作品质量等级分布', fontsize=14, fontweight='bold')
        else:
            ax2.set_title('Distribution of Quality Levels', fontsize=14, fontweight='bold')

        # 1.3 得分构型分布
        ax3 = axes[0, 2]
        pattern_counts = self.work_df['得分构型'].value_counts().head(10)

        if len(pattern_counts) > 0:
            # 根据构型总分排序
            pattern_counts = pattern_counts.sort_index(key=lambda x: x.map(
                lambda p: sum(int(d) for d in str(p))
            ))

            bars = ax3.bar(range(len(pattern_counts)), pattern_counts.values,
                          color=plt.cm.viridis(np.linspace(0, 1, len(pattern_counts))))

            ax3.set_xticks(range(len(pattern_counts)))
            ax3.set_xticklabels(pattern_counts.index, rotation=45, ha='right')

            if CHINESE_ENABLED:
                ax3.set_xlabel('得分构型', fontsize=12)
                ax3.set_ylabel('作品数量', fontsize=12)
                ax3.set_title('Top 10 得分构型分布', fontsize=14, fontweight='bold')
            else:
                ax3.set_xlabel('Score Pattern', fontsize=12)
                ax3.set_ylabel('Number of Works', fontsize=12)
                ax3.set_title('Top 10 Score Patterns', fontsize=14, fontweight='bold')

            # 添加构型解读
            pattern_meanings = {
                '222': 'All Strong',
                '221': '2 Strong 1 Rec',
                '211': '1 Strong 2 Rec',
                '210': 'Mixed',
                '200': '1 Strong 2 Not',
                '111': 'All Rec',
                '110': '2 Rec 1 Not',
                '100': '1 Rec 2 Not',
                '000': 'All Not'
            }

            for i, (pattern, count) in enumerate(pattern_counts.items()):
                meaning = pattern_meanings.get(pattern, '')
                ax3.text(i, count + max(pattern_counts.values)*0.02,
                        meaning, ha='center', va='bottom', fontsize=9, rotation=0)

        # 1.4 最高分与最低分分布
        ax4 = axes[1, 0]
        max_scores = self.work_df['最高分'].value_counts().sort_index()
        min_scores = self.work_df['最低分'].value_counts().sort_index()

        x = np.arange(len(max_scores))
        width = 0.35

        bars1 = ax4.bar(x - width/2, max_scores.values, width, label='Max Score', color='#2196F3', alpha=0.8)
        bars2 = ax4.bar(x + width/2, min_scores.values, width, label='Min Score', color='#FF9800', alpha=0.8)

        if CHINESE_ENABLED:
            ax4.set_xlabel('评分值', fontsize=12)
            ax4.set_ylabel('作品数量', fontsize=12)
            ax4.set_title('作品最高分与最低分分布', fontsize=14, fontweight='bold')
        else:
            ax4.set_xlabel('Score Value', fontsize=12)
            ax4.set_ylabel('Number of Works', fontsize=12)
            ax4.set_title('Distribution of Max and Min Scores', fontsize=14, fontweight='bold')

        ax4.set_xticks(x)
        ax4.set_xticklabels(max_scores.index)
        ax4.legend()
        ax4.grid(True, alpha=0.3, linestyle='--')

        # 1.5 评分差异分布
        ax5 = axes[1, 1]
        diff_counts = self.work_df['评分差异'].value_counts().sort_index()

        colors = ['#8BC34A' if d <= 1 else '#FFC107' if d == 2 else '#F44336'
                 for d in diff_counts.index]

        bars = ax5.bar(diff_counts.index, diff_counts.values, color=colors, edgecolor='black')

        for bar in bars:
            height = bar.get_height()
            ax5.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom', fontsize=10)

        if CHINESE_ENABLED:
            ax5.set_xlabel('评分差异（最高分-最低分）', fontsize=12)
            ax5.set_ylabel('作品数量', fontsize=12)
            ax5.set_title('作品评分差异分布', fontsize=14, fontweight='bold')
        else:
            ax5.set_xlabel('Score Difference (Max - Min)', fontsize=12)
            ax5.set_ylabel('Number of Works', fontsize=12)
            ax5.set_title('Distribution of Score Differences', fontsize=14, fontweight='bold')

        ax5.set_xticks(diff_counts.index)

        # 1.6 争议作品分析
        ax6 = axes[1, 2]
        controversial = self.work_df['争议作品'].value_counts()

        if len(controversial) == 2:
            if CHINESE_ENABLED:
                labels = ['非争议作品', '争议作品']
            else:
                labels = ['Non-Controversial', 'Controversial']

            colors = ['#4CAF50', '#F44336']
            wedges, texts, autotexts = ax6.pie(controversial.values, labels=labels,
                                              autopct='%1.1f%%', colors=colors,
                                              startangle=90, explode=(0, 0.1))

            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
        else:
            if CHINESE_ENABLED:
                ax6.text(0.5, 0.5, '无争议作品数据', ha='center', va='center',
                        fontsize=12, transform=ax6.transAxes)
            else:
                ax6.text(0.5, 0.5, 'No Controversial Data', ha='center', va='center',
                        fontsize=12, transform=ax6.transAxes)

        if CHINESE_ENABLED:
            ax6.set_title('争议作品比例分析', fontsize=14, fontweight='bold')
        else:
            ax6.set_title('Controversial Works Analysis', fontsize=14, fontweight='bold')

        plt.tight_layout()
        plt.savefig('part2_quality_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()

        # 生成统计分析报告
        report = self.generate_quality_report()

        return fig, report

    def generate_quality_report(self):
        """生成作品质量分析报告"""
        print("\n" + "-"*60)
        if CHINESE_ENABLED:
            print("作品质量分析报告")
        else:
            print("Work Quality Analysis Report")
        print("-"*60)

        report = []
        if CHINESE_ENABLED:
            report.append("作品质量分析报告")
        else:
            report.append("Work Quality Analysis Report")
        report.append("="*60)
        report.append(f"Analysis Time: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # 基本统计
        if CHINESE_ENABLED:
            report.append("一、基本统计信息")
        else:
            report.append("1. Basic Statistics")
        report.append("-"*40)
        report.append(f"Total Works: {len(self.work_df):,}")
        report.append(f"Number of Categories: {self.work_df['作品类别'].nunique()}")
        report.append(f"Score Pattern Types: {self.work_df['得分构型'].nunique()}")
        report.append("")

        # 总分统计
        if CHINESE_ENABLED:
            report.append("二、总分统计分析")
        else:
            report.append("2. Total Score Statistics")
        report.append("-"*40)
        report.append(f"Average Total Score: {self.work_df['总分'].mean():.2f}")
        report.append(f"Median Total Score: {self.work_df['总分'].median():.1f}")
        report.append(f"Std of Total Score: {self.work_df['总分'].std():.2f}")
        report.append(f"Score Range: {self.work_df['总分'].min()} - {self.work_df['总分'].max()}")
        report.append("")

        # 总分分布详情
        score_dist = self.work_df['总分'].value_counts().sort_index()
        if CHINESE_ENABLED:
            report.append("三、总分分布详情")
        else:
            report.append("3. Score Distribution Details")
        report.append("-"*40)
        for score, count in score_dist.items():
            percentage = (count / len(self.work_df)) * 100
            report.append(f"Score {score}: {count:3d} works ({percentage:5.1f}%)")
        report.append("")

        # 质量等级统计
        if CHINESE_ENABLED:
            report.append("四、质量等级统计")
        else:
            report.append("4. Quality Level Statistics")
        report.append("-"*40)
        quality_dist = self.work_df['质量等级'].value_counts()
        for level, count in quality_dist.items():
            percentage = (count / len(self.work_df)) * 100
            if not CHINESE_ENABLED:
                level = {'高质量': 'High', '中等质量': 'Medium', '低质量': 'Low'}.get(level, level)
            report.append(f"{level}: {count:3d} works ({percentage:5.1f}%)")
        report.append("")

        # 得分构型统计
        if CHINESE_ENABLED:
            report.append("五、主要得分构型统计")
        else:
            report.append("5. Main Score Pattern Statistics")
        report.append("-"*40)
        pattern_dist = self.work_df['得分构型'].value_counts().head(10)
        for pattern, count in pattern_dist.items():
            percentage = (count / len(self.work_df)) * 100
            total_score = sum(int(d) for d in str(pattern))
            report.append(f"Pattern {pattern} (Score{total_score}): {count:3d} works ({percentage:5.1f}%)")
        report.append("")

        # 保存报告
        if CHINESE_ENABLED:
            report_filename = '作品质量分析报告.txt'
        else:
            report_filename = 'work_quality_analysis_report.txt'

        report_text = "\n".join(report)
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report_text)

        print(f"✓ Report saved to: {report_filename}")

        # 打印报告到控制台
        print("\n" + report_text)

        return report_text

    def part_three_category_comparison(self):
        """
        三、各类别作品质量对比
        这部分分析不同类别作品的质量差异
        """
        print("\n" + "="*60)
        if CHINESE_ENABLED:
            print("三、各类别作品质量对比")
        else:
            print("Part 3: Category Quality Comparison")
        print("="*60)

        if self.work_df.empty:
            print("⚠ No data available for analysis")
            return None

        # 1. 按类别统计
        category_stats = self.calculate_category_statistics()

        if category_stats.empty:
            print("⚠ Insufficient category data")
            return None

        # 2. 创建分析图表
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))

        if CHINESE_ENABLED:
            fig.suptitle('三、各类别作品质量对比', fontsize=16, fontweight='bold')
        else:
            fig.suptitle('Part 3: Category Quality Comparison', fontsize=16, fontweight='bold')

        # 2.1 各类别作品数量对比
        ax1 = axes[0, 0]
        categories = category_stats.sort_values('作品数量', ascending=False).head(10)

        # 确保索引是字符串
        categories_index = [str(idx)[:15] for idx in categories.index]

        bars = ax1.barh(range(len(categories)), categories['作品数量'].values,
                       color=plt.cm.Set3(np.linspace(0, 1, len(categories))))

        ax1.set_yticks(range(len(categories)))
        ax1.set_yticklabels(categories_index, fontsize=10)

        if CHINESE_ENABLED:
            ax1.set_xlabel('作品数量', fontsize=12)
            ax1.set_title('各类别作品数量Top 10', fontsize=14, fontweight='bold')
        else:
            ax1.set_xlabel('Number of Works', fontsize=12)
            ax1.set_title('Top 10 Categories by Work Count', fontsize=14, fontweight='bold')

        ax1.invert_yaxis()

        # 在条形图上显示数量
        for i, v in enumerate(categories['作品数量'].values):
            ax1.text(v + max(categories['作品数量'].values) * 0.01, i,
                    str(int(v)), va='center', fontsize=10)

        # 2.2 各类别平均总分对比
        ax2 = axes[0, 1]
        categories_score = category_stats.sort_values('平均总分', ascending=False).head(10)

        # 确保索引是字符串
        categories_score_index = [str(idx)[:12] for idx in categories_score.index]

        colors = []
        for score in categories_score['平均总分']:
            if score >= 4:
                colors.append('#4CAF50')  # 绿色，高质量
            elif score >= 2:
                colors.append('#FFC107')  # 黄色，中等质量
            else:
                colors.append('#F44336')  # 红色，低质量

        bars = ax2.bar(range(len(categories_score)), categories_score['平均总分'].values,
                      color=colors, edgecolor='black')

        ax2.set_xticks(range(len(categories_score)))
        ax2.set_xticklabels(categories_score_index, rotation=45, ha='right', fontsize=10)

        if CHINESE_ENABLED:
            ax2.set_ylabel('平均总分', fontsize=12)
            ax2.set_title('各类别平均总分Top 10', fontsize=14, fontweight='bold')
        else:
            ax2.set_ylabel('Average Total Score', fontsize=12)
            ax2.set_title('Top 10 Categories by Average Score', fontsize=14, fontweight='bold')

        avg_score = category_stats['平均总分'].mean()
        ax2.axhline(y=avg_score, color='r', linestyle='--',
                   alpha=0.7, label=f"Overall Avg: {avg_score:.2f}")
        ax2.legend()

        # 在条形图上显示分数
        for i, v in enumerate(categories_score['平均总分'].values):
            ax2.text(i, v + 0.1, f'{v:.2f}', ha='center', fontsize=10)

        # 2.3 各类别高质量作品比例
        ax3 = axes[0, 2]
        categories_high_quality = category_stats.sort_values('高质量比例', ascending=False).head(10)

        # 确保索引是字符串
        categories_hq_index = [str(idx)[:15] for idx in categories_high_quality.index]

        bars = ax3.barh(range(len(categories_high_quality)),
                       categories_high_quality['高质量比例'].values * 100,
                       color=plt.cm.Greens(np.linspace(0.3, 0.9, len(categories_high_quality))))

        ax3.set_yticks(range(len(categories_high_quality)))
        ax3.set_yticklabels(categories_hq_index, fontsize=10)

        if CHINESE_ENABLED:
            ax3.set_xlabel('高质量作品比例 (%)', fontsize=12)
            ax3.set_title('各类别高质量作品比例Top 10', fontsize=14, fontweight='bold')
        else:
            ax3.set_xlabel('High Quality Works Ratio (%)', fontsize=12)
            ax3.set_title('Top 10 Categories by High Quality Ratio', fontsize=14, fontweight='bold')

        ax3.invert_yaxis()

        # 添加百分比标签
        for i, v in enumerate(categories_high_quality['高质量比例'].values * 100):
            ax3.text(v + 1, i, f'{v:.1f}%', va='center', fontsize=10)

        # 2.4 各类别争议作品比例
        ax4 = axes[1, 0]
        categories_controversial = category_stats.sort_values('争议比例', ascending=False).head(10)

        # 确保索引是字符串
        categories_con_index = [str(idx)[:15] for idx in categories_controversial.index]

        bars = ax4.barh(range(len(categories_controversial)),
                       categories_controversial['争议比例'].values * 100,
                       color=plt.cm.Reds(np.linspace(0.3, 0.9, len(categories_controversial))))

        ax4.set_yticks(range(len(categories_controversial)))
        ax4.set_yticklabels(categories_con_index, fontsize=10)

        if CHINESE_ENABLED:
            ax4.set_xlabel('争议作品比例 (%)', fontsize=12)
            ax4.set_title('各类别争议作品比例Top 10', fontsize=14, fontweight='bold')
        else:
            ax4.set_xlabel('Controversial Works Ratio (%)', fontsize=12)
            ax4.set_title('Top 10 Categories by Controversial Ratio', fontsize=14, fontweight='bold')

        ax4.invert_yaxis()

        # 添加百分比标签
        for i, v in enumerate(categories_controversial['争议比例'].values * 100):
            ax4.text(v + 0.5, i, f'{v:.1f}%', va='center', fontsize=10)

        # 2.5 各类别得分构型分布热力图
        ax5 = axes[1, 1]

        # 准备热力图数据
        all_patterns = ['000', '100', '110', '111', '200', '210', '211', '220', '221', '222']

        # 获取前8个类别
        top_categories = category_stats.sort_values('作品数量', ascending=False).head(8).index

        # 创建数据矩阵
        heatmap_data = []
        for category in top_categories:
            category_data = self.work_df[self.work_df['作品类别'] == category]
            pattern_counts = category_data['得分构型'].value_counts()

            row = []
            for pattern in all_patterns:
                count = pattern_counts.get(pattern, 0)
                # 转换为比例
                proportion = count / len(category_data) if len(category_data) > 0 else 0
                row.append(proportion * 100)  # 转换为百分比

            heatmap_data.append(row)

        heatmap_data = np.array(heatmap_data)

        # 创建热力图
        im = ax5.imshow(heatmap_data, cmap='YlOrRd', aspect='auto')

        ax5.set_xticks(range(len(all_patterns)))
        ax5.set_xticklabels(all_patterns, rotation=45, ha='right', fontsize=9)
        ax5.set_yticks(range(len(top_categories)))

        # 确保类别名称是字符串
        top_categories_labels = [str(cat)[:10] for cat in top_categories]
        ax5.set_yticklabels(top_categories_labels, fontsize=9)

        if CHINESE_ENABLED:
            ax5.set_xlabel('得分构型', fontsize=12)
            ax5.set_title('各类别得分构型分布热力图', fontsize=14, fontweight='bold')
        else:
            ax5.set_xlabel('Score Pattern', fontsize=12)
            ax5.set_title('Score Pattern Distribution by Category', fontsize=14, fontweight='bold')

        # 添加颜色条
        plt.colorbar(im, ax=ax5, label='Ratio (%)')

        # 在热力图中显示数值
        for i in range(len(top_categories)):
            for j in range(len(all_patterns)):
                value = heatmap_data[i, j]
                if value > 0:
                    ax5.text(j, i, f'{value:.0f}%', ha='center', va='center',
                            fontsize=8, color='black' if value < 50 else 'white')

        # 2.6 类别质量散点图（数量 vs 质量）
        ax6 = axes[1, 2]

        # 确保数据是数值类型
        work_counts = pd.to_numeric(category_stats['作品数量'], errors='coerce').fillna(0)
        avg_scores = pd.to_numeric(category_stats['平均总分'], errors='coerce').fillna(0)
        hq_ratios = pd.to_numeric(category_stats['高质量比例'], errors='coerce').fillna(0) * 100
        con_ratios = pd.to_numeric(category_stats['争议比例'], errors='coerce').fillna(0) * 100

        scatter = ax6.scatter(work_counts, avg_scores,
                             s=hq_ratios + 20,  # 大小表示高质量比例
                             c=con_ratios,  # 颜色表示争议比例
                             cmap='RdBu_r', alpha=0.7, edgecolors='black')

        # 标注主要类别
        for idx, row in category_stats.iterrows():
            work_count = work_counts.get(idx, 0)
            avg_score = avg_scores.get(idx, 0)

            if work_count > work_counts.quantile(0.7) or avg_score > avg_scores.quantile(0.7):
                ax6.annotate(str(idx)[:8],
                           (work_count, avg_score),
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=9, alpha=0.8)

        if CHINESE_ENABLED:
            ax6.set_xlabel('作品数量', fontsize=12)
            ax6.set_ylabel('平均总分', fontsize=12)
            ax6.set_title('类别质量分布散点图', fontsize=14, fontweight='bold')
        else:
            ax6.set_xlabel('Number of Works', fontsize=12)
            ax6.set_ylabel('Average Total Score', fontsize=12)
            ax6.set_title('Category Quality Distribution', fontsize=14, fontweight='bold')

        ax6.grid(True, alpha=0.3, linestyle='--')

        # 添加颜色条
        plt.colorbar(scatter, ax=ax6, label='Controversial Ratio (%)')

        plt.tight_layout()
        plt.savefig('part3_category_comparison.png', dpi=300, bbox_inches='tight')
        plt.show()

        # 3. 生成类别对比报告
        category_report = self.generate_category_report(category_stats)

        return fig, category_report

    def calculate_category_statistics(self):
        """计算各类别统计指标"""
        if self.work_df.empty:
            return pd.DataFrame()

        stats_list = []

        for category, group in self.work_df.groupby('作品类别'):
            # 确保类别名称是字符串
            category_str = str(category)

            stats = {
                '作品数量': len(group),
                '平均总分': group['总分'].mean(),
                '总分标准差': group['总分'].std(),
                '总分中位数': group['总分'].median(),
                '最高总分': group['总分'].max(),
                '最低总分': group['总分'].min(),
            }

            # 质量等级统计
            quality_counts = group['质量等级'].value_counts(normalize=True)
            stats['高质量比例'] = quality_counts.get('高质量', 0)
            stats['中等质量比例'] = quality_counts.get('中等质量', 0)
            stats['低质量比例'] = quality_counts.get('低质量', 0)

            # 争议作品统计
            stats['争议作品数量'] = group['争议作品'].sum()
            stats['争议比例'] = group['争议作品'].mean()

            # 高风险作品统计
            stats['高风险作品数量'] = group['高风险作品'].sum()
            stats['高风险比例'] = group['高风险作品'].mean()

            stats_list.append((category_str, stats))

        # 转换为DataFrame
        if stats_list:
            stats_df = pd.DataFrame([stats for _, stats in stats_list],
                                   index=[cat for cat, _ in stats_list])

            # 计算排名
            stats_df['质量排名'] = stats_df['平均总分'].rank(ascending=False, method='min')
            stats_df['数量排名'] = stats_df['作品数量'].rank(ascending=False, method='min')
            stats_df['争议排名'] = stats_df['争议比例'].rank(ascending=False, method='min')

            return stats_df.sort_values('平均总分', ascending=False)

        return pd.DataFrame()

    def generate_category_report(self, category_stats):
        """生成各类别对比报告"""
        print("\n" + "-"*60)
        if CHINESE_ENABLED:
            print("各类别作品质量对比报告")
        else:
            print("Category Quality Comparison Report")
        print("-"*60)

        report = []
        if CHINESE_ENABLED:
            report.append("各类别作品质量对比报告")
        else:
            report.append("Category Quality Comparison Report")
        report.append("="*60)
        report.append(f"Analysis Time: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Categories: {len(category_stats)}")
        report.append("")

        # 总体统计
        if CHINESE_ENABLED:
            report.append("一、总体统计")
        else:
            report.append("1. Overall Statistics")
        report.append("-"*40)
        report.append(f"Average Score (All): {category_stats['平均总分'].mean():.2f}")
        report.append(f"Std of Scores (All): {category_stats['平均总分'].std():.2f}")
        report.append(f"High Quality Ratio (All): {category_stats['高质量比例'].mean()*100:.1f}%")
        report.append(f"Controversial Ratio (All): {category_stats['争议比例'].mean()*100:.1f}%")
        report.append("")

        # 质量排名
        if CHINESE_ENABLED:
            report.append("二、类别质量排名（按平均总分）")
        else:
            report.append("2. Category Quality Ranking (by Average Score)")
        report.append("-"*40)
        top_categories = category_stats.head(10)

        for rank, (category, row) in enumerate(top_categories.iterrows(), 1):
            # 确保数值是合适的类型
            work_count = int(row['作品数量']) if pd.notnull(row['作品数量']) else 0
            avg_score = float(row['平均总分']) if pd.notnull(row['平均总分']) else 0.0
            hq_ratio = float(row['高质量比例']) * 100 if pd.notnull(row['高质量比例']) else 0.0
            con_ratio = float(row['争议比例']) * 100 if pd.notnull(row['争议比例']) else 0.0

            report.append(f"{rank:2d}. {str(category)[:20]:20s} "
                         f"Avg Score: {avg_score:.2f} | "
                         f"Works: {work_count:3d} | "
                         f"High Quality: {hq_ratio:5.1f}% | "
                         f"Controversial: {con_ratio:5.1f}%")
        report.append("")

        # 数量排名
        if CHINESE_ENABLED:
            report.append("三、类别作品数量排名")
        else:
            report.append("3. Category Work Count Ranking")
        report.append("-"*40)
        top_by_count = category_stats.sort_values('作品数量', ascending=False).head(10)

        for rank, (category, row) in enumerate(top_by_count.iterrows(), 1):
            work_count = int(row['作品数量']) if pd.notnull(row['作品数量']) else 0
            avg_score = float(row['平均总分']) if pd.notnull(row['平均总分']) else 0.0
            quality_rank = int(row['质量排名']) if pd.notnull(row['质量排名']) else 0

            report.append(f"{rank:2d}. {str(category)[:20]:20s} "
                         f"Works: {work_count:3d} | "
                         f"Avg Score: {avg_score:.2f} | "
                         f"Quality Rank: {quality_rank}")
        report.append("")

        # 争议排名
        if CHINESE_ENABLED:
            report.append("四、类别争议作品比例排名（需要关注）")
        else:
            report.append("4. Category Controversial Ratio Ranking (Need Attention)")
        report.append("-"*40)
        top_controversial = category_stats.sort_values('争议比例', ascending=False).head(10)

        for rank, (category, row) in enumerate(top_controversial.iterrows(), 1):
            con_ratio = float(row['争议比例']) * 100 if pd.notnull(row['争议比例']) else 0.0
            con_count = int(row['争议作品数量']) if pd.notnull(row['争议作品数量']) else 0
            avg_score = float(row['平均总分']) if pd.notnull(row['平均总分']) else 0.0

            report.append(f"{rank:2d}. {str(category)[:20]:20s} "
                         f"Controversial: {con_ratio:5.1f}% | "
                         f"Controversial Count: {con_count:3d} | "
                         f"Avg Score: {avg_score:.2f}")
        report.append("")

        # 保存报告
        if CHINESE_ENABLED:
            report_filename = '各类别作品质量对比报告.txt'
        else:
            report_filename = 'category_quality_comparison_report.txt'

        report_text = "\n".join(report)
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report_text)

        print(f"✓ Report saved to: {report_filename}")

        # 打印报告到控制台
        print("\n" + report_text)

        return report_text

    def save_all_data(self):
        """保存所有分析数据到Excel文件"""
        if self.work_df.empty:
            print("⚠ No data to save")
            return

        try:
            # 保存原始数据和处理后的数据
            output_file = 'complete_work_analysis_data.xlsx'

            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # 原始数据
                self.work_df.to_excel(writer, sheet_name='Raw Data', index=False)

                # 作品质量分析统计
                quality_stats_data = {
                    'Statistic': ['Total Works', 'Average Score', 'Median Score', 'Score Std',
                                'Max Score', 'Min Score', 'High Quality Works',
                                'Medium Quality Works', 'Low Quality Works',
                                'Controversial Works', 'High Risk Works'],
                    'Value': [
                        len(self.work_df),
                        self.work_df['总分'].mean(),
                        self.work_df['总分'].median(),
                        self.work_df['总分'].std(),
                        self.work_df['总分'].max(),
                        self.work_df['总分'].min(),
                        len(self.work_df[self.work_df['质量等级'] == '高质量']),
                        len(self.work_df[self.work_df['质量等级'] == '中等质量']),
                        len(self.work_df[self.work_df['质量等级'] == '低质量']),
                        int(self.work_df['争议作品'].sum()),
                        int(self.work_df['高风险作品'].sum())
                    ]
                }
                quality_stats = pd.DataFrame(quality_stats_data)
                quality_stats.to_excel(writer, sheet_name='Overall Stats', index=False)

                # 各类别统计
                category_stats = self.calculate_category_statistics()
                if not category_stats.empty:
                    category_stats.to_excel(writer, sheet_name='Category Stats')

                # 得分构型统计
                pattern_stats = self.work_df['得分构型'].value_counts().reset_index()
                pattern_stats.columns = ['Score Pattern', 'Work Count']
                pattern_stats['Ratio'] = pattern_stats['Work Count'] / len(self.work_df)
                pattern_stats['Total Score'] = pattern_stats['Score Pattern'].apply(
                    lambda x: sum(int(d) for d in str(x))
                )
                pattern_stats = pattern_stats.sort_values('Work Count', ascending=False)
                pattern_stats.to_excel(writer, sheet_name='Pattern Stats', index=False)

                # 争议作品明细
                controversial_works = self.work_df[self.work_df['争议作品']].sort_values('总分', ascending=False)
                if not controversial_works.empty:
                    controversial_works.to_excel(writer, sheet_name='Controversial Works', index=False)

                # 高风险作品明细
                high_risk_works = self.work_df[self.work_df['高风险作品']]
                if not high_risk_works.empty:
                    high_risk_works.to_excel(writer, sheet_name='High Risk Works', index=False)

            print(f"✓ Complete analysis data saved to: {output_file}")

        except Exception as e:
            print(f"❌ Error saving data: {e}")

def main():
    """主程序"""
    print("="*70)
    if CHINESE_ENABLED:
        print("作品质量深度分析系统")
        print("分析内容：")
        print("1. 二、作品质量分析（总体分析）")
        print("2. 三、各类别作品质量对比")
    else:
        print("Work Quality Deep Analysis System")
        print("Analysis Content:")
        print("1. Part 2: Overall Quality Analysis")
        print("2. Part 3: Category Quality Comparison")
    print("="*70)

    # 检查文件是否存在
    import os
    data_file = 'runResult00.txt'

    if not os.path.exists(data_file):
        print(f"⚠ Warning: File {data_file} does not exist")
        print("Will use sample data for demonstration")

    # 创建分析器
    analyzer = WorkQualityAnalyzer(data_file)

    if analyzer.work_df.empty:
        print("❌ Cannot load data, please check file path and format")
        return

    # 执行第一部分分析：作品质量分析
    print("\n" + "="*70)
    if CHINESE_ENABLED:
        print("开始执行：二、作品质量分析（总体分析）")
    else:
        print("Starting: Part 2 - Overall Quality Analysis")
    print("="*70)

    try:
        fig1, report1 = analyzer.part_two_quality_analysis()
        if fig1:
            print("✓ Part 2 analysis completed, chart saved as: part2_quality_analysis.png")
        if report1:
            print("✓ Part 2 report generated")
    except Exception as e:
        print(f"❌ Part 2 analysis error: {e}")
        import traceback
        traceback.print_exc()

    # 执行第二部分分析：各类别作品质量对比
    print("\n" + "="*70)
    if CHINESE_ENABLED:
        print("开始执行：三、各类别作品质量对比")
    else:
        print("Starting: Part 3 - Category Quality Comparison")
    print("="*70)

    try:
        fig2, report2 = analyzer.part_three_category_comparison()
        if fig2:
            print("✓ Part 3 analysis completed, chart saved as: part3_category_comparison.png")
        if report2:
            print("✓ Part 3 report generated")
    except Exception as e:
        print(f"❌ Part 3 analysis error: {e}")
        import traceback
        traceback.print_exc()

    # 保存所有数据
    print("\n" + "="*70)
    print("Saving complete analysis data...")
    analyzer.save_all_data()

    print("\n" + "="*70)
    if CHINESE_ENABLED:
        print("分析完成！生成的文件：")
        print("1. part2_quality_analysis.png - 总体分析图表")
        print("2. part3_category_comparison.png - 类别对比图表")
        print("3. 作品质量分析报告.txt - 总体分析报告")
        print("4. 各类别作品质量对比报告.txt - 类别对比报告")
        print("5. complete_work_analysis_data.xlsx - 完整分析数据")
    else:
        print("Analysis completed! Generated files:")
        print("1. part2_quality_analysis.png - Overall analysis chart")
        print("2. part3_category_comparison.png - Category comparison chart")
        print("3. work_quality_analysis_report.txt - Overall analysis report")
        print("4. category_quality_comparison_report.txt - Category comparison report")
        print("5. complete_work_analysis_data.xlsx - Complete analysis data")
    print("="*70)

if __name__ == "__main__":
    # 检查必要的库
    required_libraries = ['pandas', 'numpy', 'matplotlib', 'seaborn']

    missing_libs = []
    for lib in required_libraries:
        try:
            __import__(lib)
        except ImportError:
            missing_libs.append(lib)

    if missing_libs:
        print("Missing required libraries, please install with:")
        print(f"pip install {' '.join(missing_libs)}")
    else:
        # 运行主程序
        main()