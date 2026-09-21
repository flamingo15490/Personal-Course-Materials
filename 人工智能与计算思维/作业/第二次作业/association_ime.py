"""
联想输入法核心模块
提供联想字查询功能
"""

import os
import json


class AssociationIME:
    """
    联想输入法核心类
    根据输入的汉字，提供可能的后续联想字
    """
    
    def __init__(self, data_path=None):
        """
        初始化联想输入法
        data_path: 联想数据文件路径
        """
        self.associations = {}
        self.metadata = {}
        
        if data_path and os.path.exists(data_path):
            self.load_data(data_path)
        else:
            # 尝试默认路径
            default_path = os.path.join('data', 'models', 'association_data.json')
            if os.path.exists(default_path):
                self.load_data(default_path)
    
    def load_data(self, data_path):
        """
        加载联想数据
        """
        print(f"加载联想数据: {data_path}")
        
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.metadata = data.get('metadata', {})
        self.associations = data.get('associations', {})
        
        print(f"数据加载完成:")
        print(f"  - 总字符数: {self.metadata.get('total_chars', 'N/A')}")
        print(f"  - 不重复汉字: {self.metadata.get('unique_chars', 'N/A')}")
        print(f"  - 有联想数据的汉字: {len(self.associations)}")
        print(f"  - 每个汉字保留top_k: {self.metadata.get('top_k', 'N/A')}")
    
    def get_suggestions(self, char, max_suggestions=None):
        """
        获取指定汉字的后续联想字
        
        参数:
            char: 当前汉字
            max_suggestions: 最多返回多少个联想字（None表示返回全部）
        
        返回:
            列表，格式: [(联想字, 频率), ...]
        """
        if char not in self.associations:
            return []
        
        suggestions = self.associations[char]
        
        if max_suggestions:
            return suggestions[:max_suggestions]
        
        return suggestions
    
    def get_suggestion_text(self, char, max_suggestions=10):
        """
        获取联想字文本（仅返回汉字，不包含频率）
        
        参数:
            char: 当前汉字
            max_suggestions: 最多返回多少个联想字
        
        返回:
            字符串，如 "国 国 华 央 心..."
        """
        suggestions = self.get_suggestions(char, max_suggestions)
        return ' '.join([c for c, _ in suggestions])
    
    def is_char_supported(self, char):
        """
        检查是否支持该汉字的联想
        """
        return char in self.associations
    
    def get_stats(self):
        """
        获取统计信息
        """
        return {
            'total_chars': self.metadata.get('total_chars', 0),
            'unique_chars': self.metadata.get('unique_chars', 0),
            'association_chars': len(self.associations),
            'top_k': self.metadata.get('top_k', 0)
        }


if __name__ == '__main__':
    # 测试代码
    print("=" * 60)
    print("联想输入法核心模块测试")
    print("=" * 60)
    
    # 初始化
    ime = AssociationIME()
    
    if not ime.associations:
        print("错误: 未找到联想数据文件")
        print("请先运行 association_processor.py 生成数据")
    else:
        # 测试一些常用字
        test_chars = ['中', '国', '人', '大', '学', '北', '京']
        
        print("\n联想字测试:")
        for char in test_chars:
            suggestions = ime.get_suggestions(char, max_suggestions=5)
            if suggestions:
                suggestion_str = ', '.join([f"{c}({n})" for c, n in suggestions])
                print(f"  '{char}' → {suggestion_str}")
            else:
                print(f"  '{char}' → (无联想数据)")
        
        print("\n统计信息:")
        stats = ime.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
