"""
联想输入法 GUI 界面
使用 Tkinter 实现
界面包含：多行文本框、输入框、显示标签
"""

import tkinter as tk
from tkinter import scrolledtext, font as tkfont
import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from association_ime import AssociationIME


class AssociationIMEGUI:
    """
    联想输入法图形界面
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("联想输入法")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # 设置字体
        self.font_large = tkfont.Font(family="Microsoft YaHei", size=14)
        self.font_normal = tkfont.Font(family="Microsoft YaHei", size=12)
        self.font_small = tkfont.Font(family="Microsoft YaHei", size=10)
        
        # 初始化联想输入法核心
        self.ime = self._init_ime()
        
        # 创建界面组件
        self._create_widgets()
        
        # 绑定事件
        self._bind_events()
    
    def _init_ime(self):
        """
        初始化联想输入法
        """
        # 尝试多个可能的数据文件路径
        possible_paths = [
            os.path.join('data', 'models', 'association_data.json'),
            os.path.join(os.path.dirname(__file__), 'data', 'models', 'association_data.json'),
            'association_data.json'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return AssociationIME(path)
        
        # 如果找不到数据文件，返回空对象
        print("警告: 未找到联想数据文件，请先运行数据处理程序")
        return AssociationIME()
    
    def _create_widgets(self):
        """
        创建界面组件
        """
        # 主框架
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # === 组件1: 多行文本框（显示输入历史） ===
        text_frame = tk.LabelFrame(main_frame, text="输入文本", font=self.font_normal, padx=10, pady=10)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.text_area = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=self.font_large,
            height=10
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)
        self.text_area.config(state=tk.DISABLED)  # 只读
        
        # === 组件2: 输入框 ===
        input_frame = tk.LabelFrame(main_frame, text="输入汉字", font=self.font_normal, padx=10, pady=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(
            input_frame,
            textvariable=self.input_var,
            font=self.font_large,
            justify='center'
        )
        self.input_entry.pack(fill=tk.X, expand=True)
        self.input_entry.focus()
        
        # === 组件3: 显示标签（显示联想后续字） ===
        suggestion_frame = tk.LabelFrame(main_frame, text="联想后续字", font=self.font_normal, padx=10, pady=10)
        suggestion_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.suggestion_var = tk.StringVar(value="请输入汉字查看联想...")
        self.suggestion_label = tk.Label(
            suggestion_frame,
            textvariable=self.suggestion_var,
            font=self.font_large,
            fg="blue",
            wraplength=700,
            justify='left'
        )
        self.suggestion_label.pack(fill=tk.X, expand=True)
        
        # === 状态栏 ===
        self.status_var = tk.StringVar()
        if self.ime.associations:
            stats = self.ime.get_stats()
            self.status_var.set(f"已加载 {stats['association_chars']} 个汉字的联想数据")
        else:
            self.status_var.set("未加载联想数据")
        
        status_bar = tk.Label(main_frame, textvariable=self.status_var, font=self.font_small, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # === 说明标签 ===
        help_text = "使用说明: 在输入框中输入汉字，下方会显示可能的后续联想字"
        help_label = tk.Label(main_frame, text=help_text, font=self.font_small, fg="gray")
        help_label.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))
    
    def _bind_events(self):
        """
        绑定事件
        """
        # 输入框内容变化时更新联想
        self.input_var.trace('w', self._on_input_change)
        
        # 输入框按键事件
        self.input_entry.bind('<Return>', self._on_enter_pressed)
        self.input_entry.bind('<Key>', self._on_key_pressed)
    
    def _on_input_change(self, *args):
        """
        输入框内容变化时的回调
        """
        text = self.input_var.get()
        
        if not text:
            self.suggestion_var.set("请输入汉字查看联想...")
            return
        
        # 获取最后一个字符
        last_char = text[-1]
        
        # 检查是否是汉字
        if '\u4e00' <= last_char <= '\u9fff':
            # 获取联想字
            suggestions = self.ime.get_suggestions(last_char, max_suggestions=10)
            
            if suggestions:
                # 格式化显示
                suggestion_text = ' '.join([f"{c}" for c, _ in suggestions])
                freq_text = ' '.join([f"({n})" for _, n in suggestions])
                self.suggestion_var.set(f"{suggestion_text}\n{freq_text}")
            else:
                self.suggestion_var.set(f"'{last_char}' 暂无联想数据")
        else:
            self.suggestion_var.set(f"'{last_char}' 不是汉字，无联想")
    
    def _on_enter_pressed(self, event):
        """
        按下回车键时的回调
        """
        text = self.input_var.get()
        
        if text:
            # 添加到多行文本框
            self.text_area.config(state=tk.NORMAL)
            
            # 如果是第一个字符，不添加换行
            if self.text_area.index('end-1c') != '1.0':
                self.text_area.insert(tk.END, '\n')
            
            self.text_area.insert(tk.END, text)
            self.text_area.see(tk.END)  # 滚动到底部
            self.text_area.config(state=tk.DISABLED)
            
            # 清空输入框
            self.input_var.set('')
            
            # 更新状态
            self.status_var.set(f"已添加文本，当前共 {self.text_area.index('end-1c').split('.')[0]} 行")
    
    def _on_key_pressed(self, event):
        """
        按键事件处理
        支持数字键快速选择联想字
        """
        # 获取当前输入
        text = self.input_var.get()
        
        if not text:
            return
        
        last_char = text[-1]
        
        # 检查是否是数字键（1-9）
        if event.char.isdigit():
            num = int(event.char)
            if 1 <= num <= 9:
                suggestions = self.ime.get_suggestions(last_char, max_suggestions=9)
                if num <= len(suggestions):
                    # 选择第num个联想字
                    selected_char = suggestions[num - 1][0]
                    self.input_var.set(text + selected_char)
                    return 'break'  # 阻止默认行为


def main():
    """
    主函数
    """
    root = tk.Tk()
    
    # 设置DPI感知（Windows）
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    app = AssociationIMEGUI(root)
    
    # 启动主循环
    root.mainloop()


if __name__ == '__main__':
    main()
