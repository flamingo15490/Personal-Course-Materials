# 第二次作业 - 输入法

## 作业要求

基于新浪新闻数据集构建中文输入法模型。

### 任务1：数据预处理
- 下载数据集
- 清洗文本数据
- 构建训练集和验证集

### 任务2：构建语言模型
- 实现N-gram语言模型
- 计算字/词的概率分布

### 任务3：实现拼音输入法
- 构建拼音到汉字的映射
- 实现拼音输入转汉字的算法
- 使用语言模型进行候选排序

### 任务4：GUI界面（可选）
- 使用PyQt6或Tkinter实现简单的输入法界面

## 文件说明

- `data_preprocessing.py`: 数据预处理脚本
- `language_model.py`: 语言模型实现
- `pinyin_input.py`: 拼音输入法核心算法
- `gui.py`: 图形界面（可选）
- `main.py`: 主程序入口

## 运行方式

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 数据预处理
```bash
python main.py --mode preprocess
```

### 3. 训练模型
```bash
python main.py --mode train
```

### 4. 交互式使用
```bash
python main.py --mode interactive
```

### 5. 演示模式
```bash
python main.py --mode demo
```

### 6. 完整流程（预处理+训练+交互）
```bash
python main.py --mode all
```

### 7. 启动GUI界面
```bash
python gui.py
```

## 数据下载

由于数据集需要从北大网盘下载，请手动完成以下步骤：

1. 访问: https://disk.pku.edu.cn/link/AA461D5FD138B04031959E48243648F0CB
2. 提取码: 1898
3. 下载文件: `news2016zh_valid.zip` (约105MB)
4. 将下载的文件放到: `data/raw/` 目录下

## 项目结构

```
homework_input_method/
├── README.md
├── requirements.txt
├── main.py
├── gui.py
├── data_preprocessing.py
├── language_model.py
├── pinyin_input.py
├── data/
│   ├── raw/
│   │   └── news2016zh_valid.zip  (需手动下载)
│   └── processed/
│       └── train.txt
└── models/
    └── language_model.pkl
```

## 算法说明

### N-gram语言模型
- 使用基于字的Bigram（2-gram）模型
- 采用加一平滑（Laplace平滑）处理未登录词
- 计算条件概率 P(字|上下文)

### 拼音输入法算法
1. 拼音切分：将连续拼音字符串切分为单个拼音
2. 候选生成：根据拼音查找所有可能的汉字
3. 路径搜索：使用Beam Search算法找到最优汉字序列
4. 语言模型排序：使用N-gram模型对候选结果排序

### Beam Search
- 保留概率最高的k个候选路径
- 逐步扩展，直到处理完所有拼音
- 返回最优的汉字序列
