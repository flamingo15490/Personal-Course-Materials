"""
数据预处理模块
负责下载、清洗和准备训练数据
"""

import os
import re
import zipfile
import json


class DataPreprocessor:
    """数据预处理器"""
    
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.raw_dir = os.path.join(data_dir, 'raw')
        self.processed_dir = os.path.join(data_dir, 'processed')
        
        # 创建目录
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
    
    def download_data(self, url=None, password=None):
        """
        下载数据集
        由于网盘下载需要手动操作，这里提供说明
        """
        print("=" * 60)
        print("数据下载说明")
        print("=" * 60)
        print("1. 访问: https://disk.pku.edu.cn/link/AA461D5FD138B04031959E48243648F0CB")
        print("2. 提取码: 1898")
        print("3. 下载文件: news2016zh_valid.zip (约105MB)")
        print("4. 将下载的文件放到: {}".format(self.raw_dir))
        print("=" * 60)
        
        # 检查文件是否已存在
        zip_path = os.path.join(self.raw_dir, 'news2016zh_valid.zip')
        if os.path.exists(zip_path):
            print("数据文件已存在: {}".format(zip_path))
            return zip_path
        else:
            print("数据文件不存在，请手动下载")
            return None
    
    def extract_data(self, zip_path):
        """解压数据文件"""
        if not zip_path or not os.path.exists(zip_path):
            print("错误: 找不到zip文件")
            return False
        
        print("正在解压: {}".format(zip_path))
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.raw_dir)
            print("解压完成")
            return True
        except Exception as e:
            print("解压失败: {}".format(e))
            return False
    
    def clean_text(self, text):
        """
        清洗文本
        - 去除特殊字符
        - 保留中文、英文、数字和基本标点
        """
        # 去除URL
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # 去除邮箱
        text = re.sub(r'\S+@\S+', '', text)
        
        # 去除非中文、英文、数字、常见标点的字符
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9，。！？；：""''（）【】《》]', ' ', text)
        
        # 合并多个空格
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def process_file(self, input_file, output_file):
        """处理单个文件（支持 .txt 和 .json 格式）"""
        print("处理文件: {}".format(input_file))
        
        lines = []
        
        # 根据文件扩展名选择处理方式
        if input_file.endswith('.json'):
            # 处理 JSON 格式（每行一个 JSON 对象）
            with open(input_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            # 提取 content 字段
                            content = data.get('content', '')
                            if content:
                                cleaned = self.clean_text(content)
                                if cleaned:
                                    lines.append(cleaned)
                        except json.JSONDecodeError:
                            # 如果不是有效 JSON，当作普通文本处理
                            cleaned = self.clean_text(line)
                            if cleaned:
                                lines.append(cleaned)
        else:
            # 处理普通文本文件
            with open(input_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        cleaned = self.clean_text(line)
                        if cleaned:
                            lines.append(cleaned)
        
        # 保存处理后的数据
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print("处理完成，保存到: {}".format(output_file))
        print("  总行数: {}".format(len(lines)))
        
        return lines
    
    def prepare_data(self):
        """准备数据的主函数"""
        # 1. 检查/下载数据
        zip_path = self.download_data()
        
        # 2. 解压数据
        if zip_path and os.path.exists(zip_path):
            self.extract_data(zip_path)
        
        # 3. 查找数据文件（支持 .txt 和 .json）
        data_files = []
        for root, dirs, files in os.walk(self.raw_dir):
            for file in files:
                is_valid_name = 'valid' in file.lower() or 'news' in file.lower()
                is_valid_ext = file.endswith('.txt') or file.endswith('.json')
                if is_valid_name and is_valid_ext:
                    data_files.append(os.path.join(root, file))
        
        if not data_files:
            print("警告: 未找到数据文件")
            print("请确保数据文件在: {}".format(self.raw_dir))
            return None
        
        # 4. 处理数据
        all_lines = []
        for data_file in data_files:
            output_file = os.path.join(
                self.processed_dir, 
                os.path.basename(data_file)
            )
            lines = self.process_file(data_file, output_file)
            all_lines.extend(lines)
        
        # 5. 保存合并后的训练数据
        train_file = os.path.join(self.processed_dir, 'train.txt')
        with open(train_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(all_lines))
        
        print("\n" + "="*60)
        print("数据准备完成")
        print("="*60)
        print("总文本行数: {}".format(len(all_lines)))
        print("训练数据: {}".format(train_file))
        
        return train_file


if __name__ == '__main__':
    preprocessor = DataPreprocessor()
    preprocessor.prepare_data()
