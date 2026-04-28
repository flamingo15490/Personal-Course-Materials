"""
作品评审数据深度分析系统
功能：对评委评分数据和作品评分数据进行多维度分析
作者：基于用户需求定制
日期：2024年
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

"""
自动解决Matplotlib中文字体问题
运行此代码前，请先安装必要的库：pip install matplotlib wget
"""
import os
import sys
from matplotlib.font_manager import FontProperties, fontManager

warnings.filterwarnings('ignore')


def setup_chinese_font():
    """自动设置中文字体，解决中文显示问题"""
    try:
        # 尝试不同的中文字体
        font_options = [
            'SimHei',  # 黑体
            'Microsoft YaHei',  # 微软雅黑
            'Arial Unicode MS',  # Arial Unicode
            'DejaVu Sans',  # Linux系统字体
            'sans-serif'  # 系统默认无衬线字体
        ]

        # 获取当前系统可用的字体
        available_fonts = [f.name for f in fontManager.ttflist]

        # 查找可用的中文字体
        selected_font = None
        for font in font_options:
            if any(font.lower() in f.lower() for f in available_fonts):
                selected_font = font
                print(f"找到可用字体: {selected_font}")
                break

        if selected_font:
            # 设置全局字体
            plt.rcParams['font.sans-serif'] = [selected_font]
            plt.rcParams['axes.unicode_minus'] = False
            print(f"✓ 已成功设置中文字体: {selected_font}")
            return True
        else:
            # 如果没有找到中文字体，使用默认字体并警告
            print("警告: 未找到中文字体，尝试使用默认字体")
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'sans-serif']
            plt.rcParams['axes.unicode_minus'] = False
            return False

    except Exception as e:
        print(f"字体设置失败: {e}")
        return False


# 在主程序开始前调用
setup_chinese_font()
# 设置中文字体和绘图样式
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

# 颜色方案
COLOR_PALETTE = {
    '强烈推荐': '#1f77b4',  # 蓝色
    '推荐': '#ff7f0e',      # 橙色
    '不推荐': '#d62728',    # 红色
    '高质量': '#2ca02c',    # 绿色
    '中等质量': '#ffbb78',  # 浅橙色
    '低质量': '#9467bd'     # 紫色
}

class JudgeAnalysis:
    """评委评分风格分析类"""

    def __init__(self, judge_file='runResult01.txt'):
        """初始化评委数据"""
        self.judge_df = self.load_judge_data(judge_file)
        self.calculate_judge_metrics()

    def load_judge_data(self, file_path):
        """加载评委数据"""
        try:
            df = pd.read_csv(file_path, delim_whitespace=True, encoding='utf-8')
            print(f"✓ 成功加载评委数据，共 {len(df)} 位评委")
            return df
        except Exception as e:
            print(f"加载评委数据失败: {e}")
            return pd.DataFrame()

    def calculate_judge_metrics(self):
        """计算评委评分指标"""
        if self.judge_df.empty:
            return

        # 计算总评分次数
        self.judge_df['总评分次数'] = (self.judge_df['强烈推荐'] +
                                      self.judge_df['推荐'] +
                                      self.judge_df['不推荐'])

        # 计算各项评分比例
        self.judge_df['强烈推荐比例'] = self.judge_df['强烈推荐'] / self.judge_df['总评分次数']
        self.judge_df['推荐比例'] = self.judge_df['推荐'] / self.judge_df['总评分次数']
        self.judge_df['不推荐比例'] = self.judge_df['不推荐'] / self.judge_df['总评分次数']

        # 计算评分严格度指数（0-1，越高表示越严格）
        # 公式：严格度 = 不推荐比例 + 0.5*推荐比例
        self.judge_df['严格度指数'] = (self.judge_df['不推荐比例'] +
                                      0.5 * self.judge_df['推荐比例'])

        # 计算评分积极性指数（0-1，越高表示越积极）
        self.judge_df['积极性指数'] = (self.judge_df['强烈推荐比例'] +
                                      0.5 * self.judge_df['推荐比例'])

        # 标准化评分差异（衡量评分的一致性）
        # 使用熵的概念：评分分布越均匀，熵值越大
        from scipy.stats import entropy

        def calculate_score_entropy(row):
            probs = [row['强烈推荐比例'], row['推荐比例'], row['不推荐比例']]
            return entropy(probs)

        self.judge_df['评分熵值'] = self.judge_df.apply(calculate_score_entropy, axis=1)

        print("✓ 已完成评委指标计算")

    def identify_anomalous_judges(self, threshold=0.05):
        """识别评分异常的评委"""
        if self.judge_df.empty:
            return pd.DataFrame()

        # 找出评分分布异常的评委
        anomalous_judges = []

        # 1. 过于严格的评委（不推荐比例 > 80%）
        strict_judges = self.judge_df[self.judge_df['不推荐比例'] > 0.8].copy()
        if not strict_judges.empty:
            strict_judges['异常类型'] = '过于严格'
            anomalous_judges.append(strict_judges)

        # 2. 过于宽松的评委（强烈推荐比例 > 70%）
        lenient_judges = self.judge_df[self.judge_df['强烈推荐比例'] > 0.7].copy()
        if not lenient_judges.empty:
            lenient_judges['异常类型'] = '过于宽松'
            anomalous_judges.append(lenient_judges)

        # 3. 评分不一致的评委（熵值过低，评分过于集中）
        mean_entropy = self.judge_df['评分熵值'].mean()
        std_entropy = self.judge_df['评分熵值'].std()
        inconsistent_judges = self.judge_df[
            self.judge_df['评分熵值'] < (mean_entropy - 1.5 * std_entropy)
        ].copy()
        if not inconsistent_judges.empty:
            inconsistent_judges['异常类型'] = '评分不一致'
            anomalous_judges.append(inconsistent_judges)

        # 合并所有异常评委
        if anomalous_judges:
            result_df = pd.concat(anomalous_judges, ignore_index=True)
            result_df = result_df[['姓名', '异常类型', '强烈推荐比例',
                                  '推荐比例', '不推荐比例', '严格度指数', '评分熵值']]
            return result_df.sort_values('严格度指数', ascending=False)

        return pd.DataFrame()

    def plot_judge_style_analysis(self):
        """绘制评委评分风格分析图"""
        if self.judge_df.empty:
            return

        fig, axes = plt.subplots(2, 3, figsize=(18, 12))

        # 1. 评委评分分布雷达图（前6位评委）
        ax1 = axes[0, 0]
        sample_judges = self.judge_df.head(6)
        angles = np.linspace(0, 2*np.pi, 3, endpoint=False)
        angles = np.concatenate((angles, [angles[0]]))

        for idx, row in sample_judges.iterrows():
            values = [row['强烈推荐比例'], row['推荐比例'], row['不推荐比例'], row['强烈推荐比例']]
            ax1.plot(angles, values, 'o-', linewidth=2, label=row['姓名'][:4])
            ax1.fill(angles, values, alpha=0.25)

        ax1.set_xticks(angles[:-1])
        ax1.set_xticklabels(['强烈推荐', '推荐', '不推荐'])
        ax1.set_title('评委评分风格雷达图（前6位）')
        ax1.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))

        # 2. 评分严格度分布
        ax2 = axes[0, 1]
        sns.histplot(data=self.judge_df, x='严格度指数', bins=20, kde=True, ax=ax2)
        ax2.axvline(self.judge_df['严格度指数'].mean(), color='red', linestyle='--',
                   label=f"均值: {self.judge_df['严格度指数'].mean():.3f}")
        ax2.set_xlabel('严格度指数（越高越严格）')
        ax2.set_ylabel('评委数量')
        ax2.set_title('评委评分严格度分布')
        ax2.legend()

        # 3. 各评分比例分布
        ax3 = axes[0, 2]
        score_types = ['强烈推荐比例', '推荐比例', '不推荐比例']
        score_data = self.judge_df[score_types]

        box_data = [score_data[col] for col in score_types]
        bp = ax3.boxplot(box_data, labels=['强烈推荐', '推荐', '不推荐'])
        ax3.set_ylabel('比例')
        ax3.set_title('各评分类型比例分布')

        # 4. 严格度与积极性关系散点图
        ax4 = axes[1, 0]
        scatter = ax4.scatter(self.judge_df['严格度指数'],
                            self.judge_df['积极性指数'],
                            c=self.judge_df['总评分次数'],
                            s=100, alpha=0.7, cmap='viridis')

        # 添加颜色条
        plt.colorbar(scatter, ax=ax4, label='总评分次数')

        # 标注异常评委
        anomalous_judges = self.identify_anomalous_judges()
        if not anomalous_judges.empty:
            for _, judge in anomalous_judges.iterrows():
                judge_data = self.judge_df[self.judge_df['姓名'] == judge['姓名']]
                if not judge_data.empty:
                    ax4.annotate(judge['姓名'][:4],
                               (judge_data['严格度指数'].values[0],
                                judge_data['积极性指数'].values[0]),
                               xytext=(5, 5), textcoords='offset points',
                               fontsize=9, color='red')

        ax4.set_xlabel('严格度指数')
        ax4.set_ylabel('积极性指数')
        ax4.set_title('评委评分风格散点图（点大小=评分次数）')
        ax4.grid(True, alpha=0.3)

        # 5. 总评分次数分布
        ax5 = axes[1, 1]
        self.judge_df['总评分次数'].hist(bins=20, ax=ax5, color='skyblue', edgecolor='black')
        ax5.axvline(self.judge_df['总评分次数'].mean(), color='red', linestyle='--',
                   label=f"均值: {self.judge_df['总评分次数'].mean():.1f}")
        ax5.set_xlabel('总评分次数')
        ax5.set_ylabel('评委数量')
        ax5.set_title('评委工作量分布')
        ax5.legend()

        # 6. 评分熵值分布
        ax6 = axes[1, 2]
        sns.violinplot(data=self.judge_df, y='评分熵值', ax=ax6, color='lightgreen')
        ax6.scatter(x=np.zeros(len(self.judge_df)), y=self.judge_df['评分熵值'],
                   alpha=0.5, s=20, color='blue')
        ax6.set_ylabel('评分熵值（越高表示评分越均匀）')
        ax6.set_title('评委评分一致性分析')
        ax6.set_xticklabels([''])

        plt.tight_layout()
        plt.savefig('评委评分风格综合分析.png', dpi=300, bbox_inches='tight')
        plt.show()

        return fig

class WorkAnalysis:
    """作品质量分析类"""

    def __init__(self, work_file='runResult00.txt'):
        """初始化作品数据"""
        self.work_df = self.load_work_data(work_file)
        self.calculate_work_metrics()

    def load_work_data(self, file_path):
        """加载作品数据"""
        try:
            # 尝试不同的分隔符
            try:
                df = pd.read_csv(file_path, sep='\t', encoding='utf-8')
            except:
                df = pd.read_csv(file_path, delim_whitespace=True, encoding='utf-8')

            print(f"✓ 成功加载作品数据，共 {len(df)} 件作品")
            return df
        except Exception as e:
            print(f"加载作品数据失败: {e}")
            return pd.DataFrame()

    def calculate_work_metrics(self):
        """计算作品质量指标"""
        if self.work_df.empty:
            return

        # 确保列名正确
        if '得分构型' in self.work_df.columns:
            # 计算作品总分
            self.work_df['总分'] = self.work_df['得分构型'].apply(
                lambda x: sum(int(digit) for digit in str(x))
            )

            # 将得分构型转换为列表格式
            self.work_df['构型列表'] = self.work_df['得分构型'].apply(
                lambda x: [int(digit) for digit in str(x)]
            )

            # 计算构型特征
            self.work_df['最高分'] = self.work_df['构型列表'].apply(max)
            self.work_df['最低分'] = self.work_df['构型列表'].apply(min)
            self.work_df['评分差异'] = self.work_df['最高分'] - self.work_df['最低分']

            # 判断是否为高质量作品（总分>=5）
            self.work_df['高质量作品'] = self.work_df['总分'] >= 5

            # 判断是否为争议作品（包含0分和2分）
            self.work_df['争议作品'] = self.work_df['构型列表'].apply(
                lambda x: 0 in x and 2 in x
            )

            print("✓ 已完成作品指标计算")

    def analyze_by_category(self):
        """按作品类别进行分析"""
        if self.work_df.empty or '作品类别' not in self.work_df.columns:
            return pd.DataFrame()

        # 按类别分组统计
        category_stats = []

        for category, group in self.work_df.groupby('作品类别'):
            stats = {
                '作品类别': category,
                '作品数量': len(group),
                '平均总分': group['总分'].mean(),
                '总分标准差': group['总分'].std(),
                '高质量作品比例': group['高质量作品'].mean(),
                '争议作品比例': group['争议作品'].mean(),
                '平均最高分': group['最高分'].mean(),
                '平均最低分': group['最低分'].mean(),
            }

            # 统计各得分构型的数量
            for score_pattern in ['222', '221', '211', '210', '200', '111', '110', '100', '000']:
                stats[f'构型{score_pattern}_数量'] = len(group[group['得分构型'] == score_pattern])
                stats[f'构型{score_pattern}_比例'] = len(group[group['得分构型'] == score_pattern]) / len(group)

            category_stats.append(stats)

        category_df = pd.DataFrame(category_stats)

        # 计算排名
        category_df['质量排名'] = category_df['平均总分'].rank(ascending=False, method='min')
        category_df['数量排名'] = category_df['作品数量'].rank(ascending=False, method='min')

        return category_df.sort_values('平均总分', ascending=False)

    def plot_category_analysis(self):
        """绘制作品类别分析图"""
        if self.work_df.empty:
            return

        # 获取类别统计
        category_stats = self.analyze_by_category()
        if category_stats.empty:
            return

        fig, axes = plt.subplots(2, 3, figsize=(18, 12))

        # 1. 各类别作品数量和质量（气泡图）
        ax1 = axes[0, 0]
        scatter = ax1.scatter(category_stats['作品数量'],
                            category_stats['平均总分'],
                            s=category_stats['高质量作品比例']*500 + 100,
                            c=category_stats['争议作品比例'],
                            cmap='RdBu_r', alpha=0.7, edgecolors='black')

        # 标注主要类别
        for idx, row in category_stats.iterrows():
            if row['作品数量'] > category_stats['作品数量'].quantile(0.7) or \
               row['平均总分'] > category_stats['平均总分'].quantile(0.7):
                ax1.annotate(row['作品类别'][:8],
                           (row['作品数量'], row['平均总分']),
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=9)

        plt.colorbar(scatter, ax=ax1, label='争议作品比例')
        ax1.set_xlabel('作品数量')
        ax1.set_ylabel('平均总分')
        ax1.set_title('各类别作品数量与质量关系（气泡大小=高质量比例）')
        ax1.grid(True, alpha=0.3)

        # 2. 各类别总分分布（箱线图）
        ax2 = axes[0, 1]

        # 选取作品数量较多的前10个类别
        top_categories = category_stats.nlargest(10, '作品数量')['作品类别'].tolist()
        top_data = self.work_df[self.work_df['作品类别'].isin(top_categories)]

        # 按平均总分排序
        category_order = category_stats.sort_values('平均总分', ascending=False)['作品类别'].tolist()
        category_order = [cat for cat in category_order if cat in top_categories]

        sns.boxplot(data=top_data, x='总分', y='作品类别',
                   order=category_order, ax=ax2, palette='viridis')
        ax2.set_xlabel('作品总分')
        ax2.set_ylabel('作品类别')
        ax2.set_title('各类别作品总分分布（前10个类别）')

        # 3. 各类别得分构型分布（堆叠条形图）
        ax3 = axes[0, 2]

        # 计算各构型比例
        pattern_cols = [col for col in category_stats.columns if '构型' in col and '比例' in col]
        pattern_data = category_stats.set_index('作品类别')[pattern_cols]

        # 重命名列
        pattern_data.columns = [col.replace('构型', '').replace('_比例', '')
                              for col in pattern_data.columns]

        # 选取前8个类别
        top_pattern_data = pattern_data.head(8)

        top_pattern_data.plot(kind='barh', stacked=True, ax=ax3,
                            colormap='tab20c', width=0.8)
        ax3.set_xlabel('比例')
        ax3.set_ylabel('作品类别')
        ax3.set_title('各类别得分构型分布（前8个类别）')
        ax3.legend(title='得分构型', bbox_to_anchor=(1.05, 1), loc='upper left')

        # 4. 高质量作品比例排名
        ax4 = axes[1, 0]
        high_quality_data = category_stats.nlargest(10, '高质量作品比例')
        bars = ax4.barh(range(len(high_quality_data)),
                       high_quality_data['高质量作品比例'].values)

        # 设置颜色
        for i, (_, row) in enumerate(high_quality_data.iterrows()):
            bars[i].set_color(COLOR_PALETTE['高质量'] if i < 3 else COLOR_PALETTE['中等质量'])

        ax4.set_yticks(range(len(high_quality_data)))
        ax4.set_yticklabels(high_quality_data['作品类别'].values, fontsize=9)
        ax4.set_xlabel('高质量作品比例')
        ax4.set_title('高质量作品比例Top 10类别')
        ax4.invert_yaxis()

        # 5. 争议作品比例排名
        ax5 = axes[1, 1]
        controversial_data = category_stats.nlargest(10, '争议作品比例')
        bars = ax5.barh(range(len(controversial_data)),
                       controversial_data['争议作品比例'].values,
                       color=COLOR_PALETTE['低质量'])

        ax5.set_yticks(range(len(controversial_data)))
        ax5.set_yticklabels(controversial_data['作品类别'].values, fontsize=9)
        ax5.set_xlabel('争议作品比例')
        ax5.set_title('争议作品比例Top 10类别（需要关注）')
        ax5.invert_yaxis()

        # 6. 总分分布直方图
        ax6 = axes[1, 2]
        sns.histplot(data=self.work_df, x='总分', bins=7, kde=True, ax=ax6)
        ax6.set_xlabel('作品总分（0-6分）')
        ax6.set_ylabel('作品数量')
        ax6.set_title('所有作品总分分布')

        # 标记各分数段的含义
        score_labels = {
            0: '全部不推荐',
            1: '质量较低',
            2: '质量一般',
            3: '质量中等',
            4: '质量良好',
            5: '质量优秀',
            6: '全部强烈推荐'
        }

        for score, label in score_labels.items():
            count = len(self.work_df[self.work_df['总分'] == score])
            if count > 0:
                ax6.annotate(f"{label}\n({count}件)",
                           (score, count),
                           xytext=(0, 10), textcoords='offset points',
                           ha='center', fontsize=8, alpha=0.7)

        plt.tight_layout()
        plt.savefig('作品类别质量综合分析.png', dpi=300, bbox_inches='tight')
        plt.show()

        return fig

    def analyze_score_patterns(self):
        """深入分析得分构型"""
        if self.work_df.empty:
            return pd.DataFrame()

        # 统计各得分构型的作品数量
        pattern_stats = self.work_df['得分构型'].value_counts().reset_index()
        pattern_stats.columns = ['得分构型', '作品数量']

        # 计算总分
        pattern_stats['总分'] = pattern_stats['得分构型'].apply(
            lambda x: sum(int(digit) for digit in str(x))
        )

        # 计算构型特征
        pattern_stats['构型解读'] = pattern_stats['得分构型'].apply(
            lambda x: self.interpret_pattern(x)
        )

        # 按总分和作品数量排序
        pattern_stats = pattern_stats.sort_values(['总分', '作品数量'], ascending=[False, False])

        return pattern_stats

    def interpret_pattern(self, pattern):
        """解读得分构型的含义"""
        scores = [int(digit) for digit in str(pattern)]

        if pattern == '222':
            return "三位评委都强烈推荐（最高质量）"
        elif pattern == '221':
            return "两位强烈推荐，一位推荐（质量优秀）"
        elif pattern == '220':
            return "两位强烈推荐，一位不推荐（有争议的优秀作品）"
        elif pattern == '211':
            return "一位强烈推荐，两位推荐（质量良好）"
        elif pattern == '210':
            return "强推、推荐、不推荐各一（争议较大）"
        elif pattern == '200':
            return "一位强烈推荐，两位不推荐（高风险争议作品）"
        elif pattern == '111':
            return "三位评委都推荐（质量稳定）"
        elif pattern == '110':
            return "两位推荐，一位不推荐（质量一般）"
        elif pattern == '100':
            return "一位推荐，两位不推荐（质量较差）"
        elif pattern == '000':
            return "三位评委都不推荐（最低质量）"
        else:
            return "其他评分组合"

class IntegratedAnalysis:
    """综合分析类（整合评委和作品数据）"""

    def __init__(self, judge_file='runResult01.txt', work_file='runResult00.txt'):
        """初始化分析器"""
        self.judge_analyzer = JudgeAnalysis(judge_file)
        self.work_analyzer = WorkAnalysis(work_file)

    def generate_comprehensive_report(self):
        """生成综合分析报告"""
        print("=" * 60)
        print("作品评审数据深度分析报告")
        print("=" * 60)

        # 1. 评委分析
        print("\n一、评委评分风格分析")
        print("-" * 40)

        if not self.judge_analyzer.judge_df.empty:
            print(f"1. 评委总数: {len(self.judge_analyzer.judge_df)} 人")
            print(f"2. 总评分次数: {self.judge_analyzer.judge_df['总评分次数'].sum():,} 次")
            print(f"3. 平均严格度指数: {self.judge_analyzer.judge_df['严格度指数'].mean():.3f}")
            print(f"4. 平均评分熵值: {self.judge_analyzer.judge_df['评分熵值'].mean():.3f}")

            # 识别异常评委
            anomalous_judges = self.judge_analyzer.identify_anomalous_judges()
            if not anomalous_judges.empty:
                print(f"\n5. 发现 {len(anomalous_judges)} 位评分异常评委:")
                for _, judge in anomalous_judges.iterrows():
                    print(f"   - {judge['姓名']}: {judge['异常类型']} "
                          f"(不推荐比例: {judge['不推荐比例']:.1%})")
            else:
                print("\n5. 未发现明显评分异常评委")

        # 2. 作品分析
        print("\n二、作品质量分析")
        print("-" * 40)

        if not self.work_analyzer.work_df.empty:
            print(f"1. 作品总数: {len(self.work_analyzer.work_df):,} 件")
            print(f"2. 作品类别数: {self.work_analyzer.work_df['作品类别'].nunique()} 类")
            print(f"3. 作品平均总分: {self.work_analyzer.work_df['总分'].mean():.2f}")
            print(f"4. 高质量作品比例: {self.work_analyzer.work_df['高质量作品'].mean():.1%}")
            print(f"5. 争议作品比例: {self.work_analyzer.work_df['争议作品'].mean():.1%}")

            # 分析得分构型
            pattern_stats = self.work_analyzer.analyze_score_patterns()
            if not pattern_stats.empty:
                print(f"\n6. 得分构型分布:")
                for _, row in pattern_stats.head(5).iterrows():
                    print(f"   - 构型 {row['得分构型']}: {row['作品数量']} 件 ({row['构型解读']})")

        # 3. 按类别分析
        print("\n三、各类别作品质量对比")
        print("-" * 40)

        category_stats = self.work_analyzer.analyze_by_category()
        if not category_stats.empty:
            print("质量最高的3个类别:")
            for _, row in category_stats.head(3).iterrows():
                print(f"  {row['作品类别']}: 平均总分 {row['平均总分']:.2f}, "
                      f"高质量比例 {row['高质量作品比例']:.1%}")

            print("\n质量最低的3个类别:")
            for _, row in category_stats.tail(3).iterrows():
                print(f"  {row['作品类别']}: 平均总分 {row['平均总分']:.2f}, "
                      f"高质量比例 {row['高质量作品比例']:.1%}")

        print("\n" + "=" * 60)
        print("分析完成！详细结果请查看生成的文件和图表。")
        print("=" * 60)

    def save_all_results(self):
        """保存所有分析结果到文件"""
        with pd.ExcelWriter('深度分析结果汇总.xlsx', engine='openpyxl') as writer:
            # 保存评委数据
            if not self.judge_analyzer.judge_df.empty:
                self.judge_analyzer.judge_df.to_excel(
                    writer, sheet_name='评委详细数据', index=False
                )

            # 保存异常评委
            anomalous_judges = self.judge_analyzer.identify_anomalous_judges()
            if not anomalous_judges.empty:
                anomalous_judges.to_excel(
                    writer, sheet_name='异常评委名单', index=False
                )

            # 保存作品数据
            if not self.work_analyzer.work_df.empty:
                self.work_analyzer.work_df.to_excel(
                    writer, sheet_name='作品详细数据', index=False
                )

            # 保存类别统计
            category_stats = self.work_analyzer.analyze_by_category()
            if not category_stats.empty:
                category_stats.to_excel(
                    writer, sheet_name='类别质量统计', index=False
                )

            # 保存构型分析
            pattern_stats = self.work_analyzer.analyze_score_patterns()
            if not pattern_stats.empty:
                pattern_stats.to_excel(
                    writer, sheet_name='得分构型分析', index=False
                )

        print("✓ 所有分析结果已保存到: 深度分析结果汇总.xlsx")

    def run_all_analysis(self):
        """运行所有分析"""
        print("开始进行深度数据分析...")
        print("=" * 60)

        # 1. 评委分析
        print("\n1. 进行评委评分风格分析...")
        if not self.judge_analyzer.judge_df.empty:
            self.judge_analyzer.plot_judge_style_analysis()

        # 2. 作品分析
        print("\n2. 进行作品质量分析...")
        if not self.work_analyzer.work_df.empty:
            self.work_analyzer.plot_category_analysis()

        # 3. 综合分析
        print("\n3. 生成综合分析报告...")
        self.generate_comprehensive_report()

        # 4. 保存结果
        print("\n4. 保存分析结果...")
        self.save_all_results()

        # 5. 生成分析报告文本
        self.generate_text_report()

        print("\n" + "=" * 60)
        print("所有分析已完成！")
        print("生成的文件:")
        print("1. 深度分析结果汇总.xlsx - 包含所有详细数据")
        print("2. 评委评分风格综合分析.png - 评委分析图表")
        print("3. 作品类别质量综合分析.png - 作品分析图表")
        print("4. 深度分析报告.txt - 文本分析报告")
        print("=" * 60)

    def generate_text_report(self):
        """生成文本分析报告"""
        report_lines = []

        report_lines.append("=" * 60)
        report_lines.append("作品评审数据深度分析报告")
        report_lines.append("=" * 60)
        report_lines.append("生成时间: " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))
        report_lines.append("")

        # 评委分析部分
        report_lines.append("一、评委评分风格分析")
        report_lines.append("-" * 40)

        if not self.judge_analyzer.judge_df.empty:
            report_lines.append(f"评委总数: {len(self.judge_analyzer.judge_df)} 人")
            report_lines.append(f"总评分次数: {self.judge_analyzer.judge_df['总评分次数'].sum():,} 次")
            report_lines.append(f"平均每位评委评分次数: {self.judge_analyzer.judge_df['总评分次数'].mean():.1f} 次")
            report_lines.append(f"评委平均严格度指数: {self.judge_analyzer.judge_df['严格度指数'].mean():.3f}")
            report_lines.append(f"评委平均积极性指数: {self.judge_analyzer.judge_df['积极性指数'].mean():.3f}")
            report_lines.append("")

            # 最严格和最宽松的评委
            strictest = self.judge_analyzer.judge_df.nlargest(3, '严格度指数')
            most_lenient = self.judge_analyzer.judge_df.nsmallest(3, '严格度指数')

            report_lines.append("最严格的3位评委:")
            for _, judge in strictest.iterrows():
                report_lines.append(f"  {judge['姓名']}: 严格度指数 {judge['严格度指数']:.3f}, "
                                  f"不推荐比例 {judge['不推荐比例']:.1%}")

            report_lines.append("")
            report_lines.append("最宽松的3位评委:")
            for _, judge in most_lenient.iterrows():
                report_lines.append(f"  {judge['姓名']}: 严格度指数 {judge['严格度指数']:.3f}, "
                                  f"强烈推荐比例 {judge['强烈推荐比例']:.1%}")

            # 异常评委
            anomalous_judges = self.judge_analyzer.identify_anomalous_judges()
            if not anomalous_judges.empty:
                report_lines.append("")
                report_lines.append(f"发现 {len(anomalous_judges)} 位评分异常评委:")
                for _, judge in anomalous_judges.iterrows():
                    report_lines.append(f"  {judge['姓名']}: {judge['异常类型']} "
                                      f"(不推荐比例: {judge['不推荐比例']:.1%}, "
                                      f"强烈推荐比例: {judge['强烈推荐比例']:.1%})")

        # 作品分析部分
        report_lines.append("")
        report_lines.append("二、作品质量分析")
        report_lines.append("-" * 40)

        if not self.work_analyzer.work_df.empty:
            report_lines.append(f"作品总数: {len(self.work_analyzer.work_df):,} 件")
            report_lines.append(f"作品类别数: {self.work_analyzer.work_df['作品类别'].nunique()} 类")
            report_lines.append(f"作品平均总分: {self.work_analyzer.work_df['总分'].mean():.2f}")
            report_lines.append(f"高质量作品比例(总分≥5): {self.work_analyzer.work_df['高质量作品'].mean():.1%}")
            report_lines.append(f"争议作品比例: {self.work_analyzer.work_df['争议作品'].mean():.1%}")
            report_lines.append("")

            # 得分构型分析
            pattern_stats = self.work_analyzer.analyze_score_patterns()
            if not pattern_stats.empty:
                report_lines.append("得分构型分布:")
                for _, row in pattern_stats.iterrows():
                    report_lines.append(f"  构型 {row['得分构型']}: {row['作品数量']} 件 ({row['构型解读']})")

            # 类别分析
            category_stats = self.work_analyzer.analyze_by_category()
            if not category_stats.empty:
                report_lines.append("")
                report_lines.append("各类别质量排名:")
                for idx, row in category_stats.iterrows():
                    rank = int(row['质量排名'])
                    report_lines.append(f"  {rank:2d}. {row['作品类别']:20s} "
                                      f"平均总分: {row['平均总分']:.2f} "
                                      f"高质量比例: {row['高质量作品比例']:.1%} "
                                      f"作品数: {row['作品数量']}")

        # 建议部分
        report_lines.append("")
        report_lines.append("三、管理建议")
        report_lines.append("-" * 40)
        report_lines.append("1. 评委管理建议:")
        report_lines.append("   - 对评分过于严格或宽松的评委进行校准培训")
        report_lines.append("   - 建立评委评分一致性评估机制")
        report_lines.append("   - 考虑评委评分风格进行评审分组")
        report_lines.append("")
        report_lines.append("2. 作品质量改进建议:")
        report_lines.append("   - 重点关注低质量类别，提供针对性指导")
        report_lines.append("   - 对争议作品进行二次评审")
        report_lines.append("   - 分析高质量作品的共同特征")
        report_lines.append("")
        report_lines.append("3. 评审流程优化建议:")
        report_lines.append("   - 优化评审分组，平衡各组的严格度")
        report_lines.append("   - 建立评分标准化的校准机制")
        report_lines.append("   - 定期分析评审数据，持续改进流程")

        # 保存报告
        with open('深度分析报告.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))

        print("✓ 文本分析报告已保存到: 深度分析报告.txt")

# 主程序
def main():
    """主函数"""
    print("作品评审数据深度分析系统")
    print("=" * 50)

    try:
        # 创建分析器
        analyzer = IntegratedAnalysis('runResult01.txt', 'runResult00.txt')

        # 运行所有分析
        analyzer.run_all_analysis()

    except Exception as e:
        print(f"分析过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 运行主程序
    main()