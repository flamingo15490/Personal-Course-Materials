"""
主程序入口
整合数据预处理、模型训练和输入法功能
"""

import os
import sys
import argparse

from data_preprocessing import DataPreprocessor
from language_model import NGramLanguageModel
from pinyin_input import PinyinInputMethod


def setup_directories():
    """创建必要的目录结构"""
    dirs = ['data', 'data/raw', 'data/processed', 'models']
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def preprocess_data():
    """数据预处理步骤"""
    print("=" * 60)
    print("步骤1: 数据预处理")
    print("=" * 60)
    
    preprocessor = DataPreprocessor()
    train_file = preprocessor.prepare_data()
    
    return train_file


def train_model(train_file, model_file='models/language_model.pkl', n=2):
    """训练语言模型"""
    print("\n" + "=" * 60)
    print("步骤2: 训练语言模型")
    print("=" * 60)
    
    if not train_file or not os.path.exists(train_file):
        print("错误: 找不到训练数据文件: {}".format(train_file))
        print("请先运行数据预处理步骤")
        return None
    
    model = NGramLanguageModel(n=n)
    model.train(train_file)
    
    # 保存模型
    os.makedirs(os.path.dirname(model_file), exist_ok=True)
    model.save(model_file)
    
    return model


def interactive_mode(model_path='models/language_model.pkl'):
    """交互式输入法模式"""
    print("\n" + "=" * 60)
    print("拼音输入法 - 交互模式")
    print("=" * 60)
    print("输入拼音（用空格分隔），输入 'quit' 退出")
    print("例如: zhong wen 或 zhongwen")
    print("-" * 60)
    
    # 初始化输入法
    ime = PinyinInputMethod(model_path=model_path)
    
    while True:
        try:
            user_input = input("\n拼音: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("再见！")
                break
            
            if not user_input:
                continue
            
            # 转换拼音
            results = ime.convert(user_input, top_k=5)
            
            if results:
                print("候选结果:")
                for i, result in enumerate(results, 1):
                    print("  {}. {}".format(i, result['text']))
            else:
                print("无法识别该拼音")
                
        except KeyboardInterrupt:
            print("\n再见！")
            break
        except Exception as e:
            print("错误: {}".format(e))


def demo_mode(model_path='models/language_model.pkl'):
    """演示模式"""
    print("\n" + "=" * 60)
    print("拼音输入法 - 演示模式")
    print("=" * 60)
    
    ime = PinyinInputMethod(model_path=model_path)
    
    test_cases = [
        "zhongwen",
        "pinyin shurufa",
        "beijing daxue",
        "tianqi henhao",
        "xuexi jiqixuexi"
    ]
    
    for pinyin in test_cases:
        print("\n输入: {}".format(pinyin))
        results = ime.convert(pinyin, top_k=3)
        print("候选结果:")
        for i, result in enumerate(results, 1):
            print("  {}. {}".format(i, result['text']))


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='拼音输入法')
    parser.add_argument('--mode', choices=['preprocess', 'train', 'interactive', 'demo', 'all'],
                       default='interactive', help='运行模式')
    parser.add_argument('--model', default='models/language_model.pkl', help='模型文件路径')
    parser.add_argument('--data', default='data/processed/train.txt', help='训练数据路径')
    parser.add_argument('--n', type=int, default=2, help='N-gram阶数')
    
    args = parser.parse_args()
    
    # 创建目录
    setup_directories()
    
    if args.mode == 'preprocess':
        preprocess_data()
    
    elif args.mode == 'train':
        if os.path.exists(args.data):
            train_model(args.data, args.model, args.n)
        else:
            print("错误: 找不到训练数据: {}".format(args.data))
            print("请先运行: python main.py --mode preprocess")
    
    elif args.mode == 'interactive':
        if os.path.exists(args.model):
            interactive_mode(args.model)
        else:
            print("错误: 找不到模型文件: {}".format(args.model))
            print("请先运行: python main.py --mode train")
    
    elif args.mode == 'demo':
        if os.path.exists(args.model):
            demo_mode(args.model)
        else:
            print("错误: 找不到模型文件: {}".format(args.model))
            print("请先运行: python main.py --mode train")
    
    elif args.mode == 'all':
        # 完整流程
        train_file = preprocess_data()
        if train_file:
            train_model(train_file, args.model, args.n)
            interactive_mode(args.model)


if __name__ == '__main__':
    main()
