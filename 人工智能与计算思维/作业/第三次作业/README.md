# MLP 手写数字识别

用 NumPy 从零实现多层感知机（MLP），在 MNIST 数据集上完成手写数字识别，并扩展到鸢尾花分类。

**课程**: 人工智能与计算思维 2026 春季学期 · 作业 3

## AI 使用声明

本项目全程使用 **Claude Code**（Anthropic 旗下 AI 编程助手）辅助完成，具体包括：

- **方案设计**：通过 Claude Code 的 brainstorming 技能进行需求分析、架构设计和技术选型
- **代码实现**：采用 Subagent-Driven Development 模式，由 Claude Code 按 TDD 流程分 12 个 Task 逐步实现全部代码
- **代码审查**：每个 Task 经过 spec compliance review 和 code quality review 两轮 AI 审查
- **测试与验证**：全部 18 个单元测试及端到端训练验证由 Claude Code 执行

所有 AI 生成的代码均经过人工审核确认。

## 项目结构

```
├── src/
│   ├── layers.py        # Dense 层、ReLU、Softmax 激活函数
│   ├── losses.py        # 交叉熵损失函数
│   ├── mlp.py           # MLP 模型：训练、预测、保存/加载
│   ├── data_utils.py    # 数据加载与图片展示
│   ├── metrics.py       # 混淆矩阵、精准率、召回率、F1
│   └── dot_pure.py      # 纯 Python 实现矩阵乘法（替代 numpy.dot）
├── train.py             # 训练脚本
├── predict.py           # 预测与评估脚本
├── compare_versions.py  # numpy.dot vs 纯 Python dot 时间对比
├── iris_train.py        # 鸢尾花训练
├── iris_predict.py      # 鸢尾花预测
├── models/              # 保存训练好的模型权重
├── data/                # 数据集缓存
└── tests/               # 单元测试
```

## 环境配置

```bash
pip install -r requirements.txt
```

依赖：`numpy`, `matplotlib`, `scikit-learn`（仅用于数据加载）

## MLP 网络结构

```
输入层 (784) → Dense(128) → ReLU → Dense(64) → ReLU → Dense(10) → Softmax
```

- 权重初始化：He 初始化
- 损失函数：交叉熵
- 优化器：SGD + Mini-batch（batch_size=64，lr=0.01）

## 使用方法

### MNIST 手写数字识别

```bash
# 1. 训练模型
python train.py

# 2. 预测并评估（输出混淆矩阵、精准率、召回率、F1）
python predict.py
```

### 版本对比（numpy.dot vs 纯 Python）

```bash
python compare_versions.py
```

结果示例：

| Metric | numpy.dot | pure Python dot | Ratio |
|--------|-----------|-----------------|-------|
| Train time (s) | 0.0832 | 28.2559 | 339.5x |

### 鸢尾花分类

```bash
python iris_train.py
python iris_predict.py
```

### 运行测试

```bash
pytest tests/ -v
```

## 结果

| 数据集 | 测试准确率 | Macro-avg F1 |
|--------|-----------|-------------|
| MNIST | 94.89% | 94.85% |
| Iris | 100% | 100% |

## 作业需求对照

| # | 要求 | 对应文件 |
|---|------|---------|
| 1 | LLM 实现 MLP 识别 MNIST | 全部代码 |
| 2 | 按编号展示图片及 label | `src/data_utils.py` → `show_image()` |
| 3 | 训练/预测分离 + 模型持久化 | `train.py` / `predict.py` + `mlp.save()` / `mlp.load()` |
| 4 | 混淆矩阵 | `src/metrics.py` → 表格 + 可视化 |
| 5 | 精准率、召回率、F1 | `src/metrics.py` → 各类 F1 + Macro-avg |
| 6 | 两版本对比（numpy.dot vs 纯 Python） | `compare_versions.py` + `src/dot_pure.py` |
| 7 | 鸢尾花迁移 | `iris_train.py` / `iris_predict.py` |
