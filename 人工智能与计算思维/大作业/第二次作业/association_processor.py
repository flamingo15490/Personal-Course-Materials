"""
联想输入法 - 数据处理器
从新浪新闻数据计算每个汉字的后续联想字
"""

import os
import json
from collections import defaultdict, Counter


class AssociationDataProcessor:
    """
    联想输入法数据处理器
    计算每个汉字后面最可能出现的后续字
    """
    
    def __init__(self, data_dir='data', top_k=10, min_freq=5):
        """
        初始化处理器
        data_dir: 数据目录
        top_k: 每个汉字保留的后续字数量（默认10个）
        min_freq: 最小出现频率（默认5次）
        """
        self.data_dir = data_dir
        self.raw_dir = os.path.join(data_dir, 'raw')
        self.processed_dir = os.path.join(data_dir, 'processed')
        self.model_dir = os.path.join(data_dir, 'models')
        
        # 创建目录
        os.makedirs(self.processed_dir, exist_ok=True)
        os.makedirs(self.model_dir, exist_ok=True)
        
        self.top_k = top_k
        self.min_freq = min_freq
        
        # 存储每个汉字的后续字统计
        # 格式: {当前字: {后续字: 出现次数}}
        self.char_followers = defaultdict(Counter)
        self.total_chars = 0
        self.unique_chars = set()
    
    def process_large_json_file(self, file_path, chunk_size=10000):
        """
        处理大型JSON文件（逐行读取，内存友好）
        chunk_size: 每处理多少行打印一次进度
        """
        print(f"开始处理文件: {file_path}")
        print(f"策略: 逐行读取，每 {chunk_size} 行报告进度")
        
        line_count = 0
        processed_count = 0
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line_count += 1
                line = line.strip()
                
                if not line:
                    continue
                
                # 解析JSON
                try:
                    data = json.loads(line)
                    content = data.get('content', '')
                    if content:
                        self._process_text(content)
                        processed_count += 1
                except json.JSONDecodeError:
                    # 如果不是JSON格式，当作纯文本处理
                    self._process_text(line)
                    processed_count += 1
                
                # 定期报告进度
                if line_count % chunk_size == 0:
                    print(f"  已处理 {line_count} 行，有效文本 {processed_count} 条，"
                          f"已收集 {len(self.char_followers)} 个汉字的关联数据")
        
        print(f"处理完成: 共 {line_count} 行，有效文本 {processed_count} 条")
        print(f"共收集 {len(self.char_followers)} 个汉字的后续字数据")
        print(f"总字符数: {self.total_chars}，不重复汉字: {len(self.unique_chars)}")
        
        return len(self.char_followers)
    
    def _process_text(self, text):
        """
        处理单个文本，提取汉字关联关系
        """
        # 过滤出纯汉字
        chinese_chars = ''.join(c for c in text if '\u4e00' <= c <= '\u9fff')
        
        if len(chinese_chars) < 2:
            return
        
        self.total_chars += len(chinese_chars)
        self.unique_chars.update(chinese_chars)
        
        # 统计每个字的后续字
        for i in range(len(chinese_chars) - 1):
            current_char = chinese_chars[i]
            next_char = chinese_chars[i + 1]
            self.char_followers[current_char][next_char] += 1
    
    def build_association_dict(self):
        """
        构建联想字典
        每个汉字只保留top_k个最可能的后续字
        """
        print(f"\n构建联想字典（每个汉字保留前 {self.top_k} 个后续字）...")
        
        association_dict = {}
        
        for char, followers in self.char_followers.items():
            # 过滤低频后续字
            filtered = {k: v for k, v in followers.items() if v >= self.min_freq}
            
            if not filtered:
                continue
            
            # 按频率排序，取前top_k个
            top_followers = Counter(filtered).most_common(self.top_k)
            
            # 保存为列表格式: [(后续字, 频率), ...]
            association_dict[char] = top_followers
        
        print(f"联想字典构建完成: 共 {len(association_dict)} 个汉字")
        
        # 打印一些示例
        sample_chars = ['中', '国', '人', '大', '学']
        print("\n示例数据:")
        for char in sample_chars:
            if char in association_dict:
                followers = association_dict[char]
                follower_str = ', '.join([f"{c}({n})" for c, n in followers[:5]])
                print(f"  '{char}' 的后续字: {follower_str}")
        
        return association_dict
    
    def save_association_data(self, association_dict, filename='association_data.json'):
        """
        保存联想数据到文件
        """
        output_path = os.path.join(self.model_dir, filename)
        
        # 转换为可JSON序列化的格式
        data = {
            'metadata': {
                'total_chars': self.total_chars,
                'unique_chars': len(self.unique_chars),
                'association_chars': len(association_dict),
                'top_k': self.top_k,
                'min_freq': self.min_freq
            },
            'associations': association_dict
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n联想数据已保存到: {output_path}")
        
        # 计算文件大小
        file_size = os.path.getsize(output_path)
        print(f"文件大小: {file_size / 1024:.2f} KB")
        
        return output_path
    
    def process_all(self, json_file_path=None):
        """
        完整处理流程
        """
        # 1. 查找数据文件
        if json_file_path is None:
            json_file_path = os.path.join(self.raw_dir, 'news2016zh_valid.json')
        
        if not os.path.exists(json_file_path):
            # 尝试其他可能的位置
            alt_path = os.path.join(self.raw_dir, 'news2016zh_valid.zip')
            if os.path.exists(alt_path):
                print(f"请先解压数据文件: {alt_path}")
                return None
            print(f"错误: 找不到数据文件: {json_file_path}")
            return None
        
        # 2. 处理数据
        self.process_large_json_file(json_file_path)
        
        # 3. 构建联想字典
        association_dict = self.build_association_dict()
        
        # 4. 保存数据
        output_path = self.save_association_data(association_dict)
        
        return output_path


if __name__ == '__main__':
    # 使用示例
    processor = AssociationDataProcessor(top_k=10, min_freq=5)
    result = processor.process_all()
    
    if result:
        print(f"\n✓ 数据处理成功！")
        print(f"输出文件: {result}")
    else:
        print(f"\n✗ 数据处理失败")
