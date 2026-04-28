"""
联想输入法 - 主程序入口
整合数据处理、核心功能和GUI界面
"""

import os
import sys
import argparse


def check_data_exists():
    """
    检查联想数据文件是否存在
    """
    data_path = os.path.join('data', 'models', 'association_data.json')
    return os.path.exists(data_path)


def run_data_processing():
    """
    运行数据处理程序
    """
    print("=" * 60)
    print("步骤1: 数据处理")
    print("=" * 60)
    
    from association_processor import AssociationDataProcessor
    
    processor = AssociationDataProcessor(top_k=10, min_freq=5)
    result = processor.process_all()
    
    if result:
        print(f"\n✓ 数据处理成功！")
        print(f"数据文件: {result}")
        return True
    else:
        print(f"\n✗ 数据处理失败")
        return False


def run_gui():
    """
    运行GUI界面
    """
    print("=" * 60)
    print("步骤2: 启动GUI界面")
    print("=" * 60)
    
    # 检查数据文件
    if not check_data_exists():
        print("错误: 未找到联想数据文件")
        print("请先运行: python association_main.py --mode process")
        return False
    
    # 启动GUI
    try:
        from association_gui import main as gui_main
        gui_main()
        return True
    except Exception as e:
        print(f"启动GUI失败: {e}")
        return False


def run_test():
    """
    运行测试
    """
    print("=" * 60)
    print("测试模式")
    print("=" * 60)
    
    if not check_data_exists():
        print("错误: 未找到联想数据文件")
        return False
    
    from association_ime import AssociationIME
    
    ime = AssociationIME()
    
    # 测试一些常用字
    test_chars = ['中', '国', '人', '大', '学', '北', '京', '的', '是', '在']
    
    print("\n联想字测试:")
    for char in test_chars:
        suggestions = ime.get_suggestions(char, max_suggestions=5)
        if suggestions:
            suggestion_str = ' '.join([f"{c}({n})" for c, n in suggestions])
            print(f"  '{char}' → {suggestion_str}")
        else:
            print(f"  '{char}' → (无联想数据)")
    
    print("\n统计信息:")
    stats = ime.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    return True


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='联想输入法')
    parser.add_argument(
        '--mode',
        choices=['all', 'process', 'gui', 'test'],
        default='all',
        help='运行模式: all(完整流程), process(仅数据处理), gui(仅GUI), test(测试)'
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("联想输入法")
    print("=" * 60)
    
    if args.mode == 'all':
        # 完整流程: 数据处理 + GUI
        if run_data_processing():
            print("\n" + "=" * 60)
            input("数据处理完成，按回车键启动GUI界面...")
            run_gui()
    
    elif args.mode == 'process':
        # 仅数据处理
        run_data_processing()
    
    elif args.mode == 'gui':
        # 仅GUI
        run_gui()
    
    elif args.mode == 'test':
        # 测试模式
        run_test()


if __name__ == '__main__':
    main()
