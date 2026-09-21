"""
语言模型模块
实现基于字的N-gram语言模型
"""

import os
import json
import pickle
from collections import defaultdict, Counter
import math


class NGramLanguageModel:
    """N-gram语言模型"""
    
    def __init__(self, n=2):
        """
        初始化N-gram模型
        n: N-gram的阶数，默认2-gram (bigram)
        """
        self.n = n
        self.ngram_counts = defaultdict(Counter)  # n-gram计数
        self.context_counts = Counter()  # (n-1)-gram计数
        self.vocab = set()  # 词汇表
        self.vocab_size = 0
        
    def tokenize(self, text):
        """将文本切分为字符列表"""
        return list(text)
    
    def train(self, text_file):
        """
        训练语言模型
        text_file: 训练数据文件路径
        """
        print(f"开始训练 {self.n}-gram 语言模型...")
        
        # 读取训练数据
        with open(text_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            chars = self.tokenize(line)
            
            # 添加句子开始和结束标记
            chars = ['<BOS>'] + chars + ['<EOS>']
            
            # 更新词汇表
            self.vocab.update(chars)
            
            # 统计n-gram
            for i in range(len(chars) - self.n + 1):
                ngram = tuple(chars[i:i + self.n])
                context = tuple(chars[i:i + self.n - 1])
                
                self.ngram_counts[context][ngram[-1]] += 1
                self.context_counts[context] += 1
        
        self.vocab_size = len(self.vocab)
        
        print(f"训练完成")
        print(f"  词汇表大小: {self.vocab_size}")
        print(f"  训练文本行数: {total_lines}")
        
    def get_probability(self, char, context):
        """
        计算条件概率 P(char | context)
        使用加一平滑（Laplace平滑）
        """
        context = tuple(context)
        
        count = self.ngram_counts[context][char]
        context_count = self.context_counts[context]
        
        # 加一平滑
        vocab_size = max(self.vocab_size, 1)  # 避免除零
        probability = (count + 1) / (context_count + vocab_size)
        
        return probability
    
    def get_log_probability(self, text):
        """
        计算文本的对数概率
        """
        chars = self.tokenize(text)
        chars = ['<BOS>'] + chars + ['<EOS>']
        
        log_prob = 0.0
        
        for i in range(self.n - 1, len(chars)):
            context = chars[i - self.n + 1:i]
            char = chars[i]
            
            prob = self.get_probability(char, context)
            log_prob += math.log(prob)
        
        return log_prob
    
    def predict_next(self, context, top_k=5):
        """
        给定上下文，预测下一个最可能的字
        context: 上下文（字符列表）
        top_k: 返回前k个最可能的字
        """
        context = tuple(context[-(self.n - 1):]) if len(context) >= self.n - 1 else tuple(context)
        
        # 获取所有可能的下一个字及其概率
        candidates = []
        for char in self.vocab:
            prob = self.get_probability(char, context)
            candidates.append((char, prob))
        
        # 按概率排序
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        return candidates[:top_k]
    
    def save(self, model_file):
        """保存模型"""
        model_data = {
            'n': self.n,
            'ngram_counts': dict(self.ngram_counts),
            'context_counts': dict(self.context_counts),
            'vocab': list(self.vocab),
            'vocab_size': self.vocab_size
        }
        
        with open(model_file, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"模型已保存到: {model_file}")
    
    def load(self, model_file):
        """加载模型"""
        with open(model_file, 'rb') as f:
            model_data = pickle.load(f)
        
        self.n = model_data['n']
        self.ngram_counts = defaultdict(Counter, model_data['ngram_counts'])
        self.context_counts = Counter(model_data['context_counts'])
        self.vocab = set(model_data['vocab'])
        self.vocab_size = model_data['vocab_size']
        
        print(f"模型已加载: {model_file}")
        print(f"  N-gram阶数: {self.n}")
        print(f"  词汇表大小: {self.vocab_size}")


class UnigramModel:
    """一元语言模型（用于回退）"""
    
    def __init__(self):
        self.char_counts = Counter()
        self.total_count = 0
        self.vocab_size = 0
    
    def train(self, text_file):
        """训练一元模型"""
        print("训练一元语言模型...")
        
        with open(text_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    chars = list(line)
                    self.char_counts.update(chars)
                    self.total_count += len(chars)
        
        self.vocab_size = len(self.char_counts)
        print(f"✓ 一元模型训练完成，词汇表大小: {self.vocab_size}")
    
    def get_probability(self, char):
        """获取字的概率（加一平滑）"""
        count = self.char_counts[char]
        return (count + 1) / (self.total_count + self.vocab_size)


if __name__ == '__main__':
    # 测试代码
    model = NGramLanguageModel(n=2)
    
    # 创建测试数据
    test_data = """今天天气很好
明天会下雨
我喜欢学习
北京大学是一所好学校
机器学习很有趣"""
    
    with open('test_train.txt', 'w', encoding='utf-8') as f:
        f.write(test_data)
    
    model.train('test_train.txt')
    
    # 测试预测
    context = ['今']
    predictions = model.predict_next(context, top_k=5)
    print(f"\n给定上下文 '{context}'，预测下一个字:")
    for char, prob in predictions:
        print(f"  {char}: {prob:.4f}")
    
    # 测试概率计算
    log_prob = model.get_log_probability("今天天气很好")
    print(f"\n'今天天气很好' 的对数概率: {log_prob:.4f}")
    
    # 保存和加载测试
    model.save('test_model.pkl')
    
    new_model = NGramLanguageModel()
    new_model.load('test_model.pkl')
    
    # 清理测试文件
    os.remove('test_train.txt')
    os.remove('test_model.pkl')
    
    print("\n测试完成")
