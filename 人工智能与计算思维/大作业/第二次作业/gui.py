"""
GUI界面模块
使用Tkinter实现简单的拼音输入法界面
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pinyin_input import PinyinInputMethod


class PinyinIMEGUI:
    """拼音输入法GUI"""
    
    def __init__(self, root, model_path='models/language_model.pkl'):
        self.root = root
        self.root.title("拼音输入法")
        self.root.geometry("600x400")
        self.root.configure(bg='#f0f0f0')
        
        # 初始化输入法
        self.ime = None
        self.load_model(model_path)
        
        # 创建界面
        self.create_widgets()
    
    def load_model(self, model_path):
        """加载语言模型"""
        try:
            if os.path.exists(model_path):
                self.ime = PinyinInputMethod(model_path=model_path)
                self.model_loaded = True
            else:
                self.model_loaded = False
                self.ime = PinyinInputMethod()  # 使用空模型
        except Exception as e:
            messagebox.showerror("错误", "加载模型失败: {}".format(e))
            self.model_loaded = False
            self.ime = PinyinInputMethod()
    
    def create_widgets(self):
        """创建界面组件"""
        # 标题
        title_label = tk.Label(
            self.root,
            text="拼音输入法",
            font=("微软雅黑", 24, "bold"),
            bg='#f0f0f0',
            fg='#333333'
        )
        title_label.pack(pady=20)
        
        # 模型状态
        if self.model_loaded:
            status_text = "模型已加载"
            status_color = "green"
        else:
            status_text = "模型未加载（使用基础字典）"
            status_color = "orange"
        
        status_label = tk.Label(
            self.root,
            text=status_text,
            font=("微软雅黑", 10),
            bg='#f0f0f0',
            fg=status_color
        )
        status_label.pack()
        
        # 输入框框架
        input_frame = tk.Frame(self.root, bg='#f0f0f0')
        input_frame.pack(pady=20, padx=30, fill=tk.X)
        
        # 拼音输入标签
        pinyin_label = tk.Label(
            input_frame,
            text="拼音:",
            font=("微软雅黑", 12),
            bg='#f0f0f0'
        )
        pinyin_label.pack(side=tk.LEFT)
        
        # 拼音输入框
        self.pinyin_var = tk.StringVar()
        self.pinyin_entry = tk.Entry(
            input_frame,
            textvariable=self.pinyin_var,
            font=("微软雅黑", 14),
            width=30
        )
        self.pinyin_entry.pack(side=tk.LEFT, padx=10)
        self.pinyin_entry.bind('<Return>', lambda e: self.convert())
        self.pinyin_entry.bind('<KeyRelease>', lambda e: self.convert())
        
        # 转换按钮
        convert_btn = tk.Button(
            input_frame,
            text="转换",
            font=("微软雅黑", 11),
            command=self.convert,
            bg='#4CAF50',
            fg='white',
            padx=15
        )
        convert_btn.pack(side=tk.LEFT)
        
        # 结果显示框架
        result_frame = tk.Frame(self.root, bg='#f0f0f0')
        result_frame.pack(pady=10, padx=30, fill=tk.BOTH, expand=True)
        
        # 结果标签
        result_label = tk.Label(
            result_frame,
            text="候选结果:",
            font=("微软雅黑", 12),
            bg='#f0f0f0'
        )
        result_label.pack(anchor=tk.W)
        
        # 结果列表框
        self.result_listbox = tk.Listbox(
            result_frame,
            font=("微软雅黑", 14),
            height=8,
            selectmode=tk.SINGLE
        )
        self.result_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 滚动条
        scrollbar = tk.Scrollbar(self.result_listbox)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.result_listbox.yview)
        
        # 双击选择
        self.result_listbox.bind('<Double-Button-1>', self.select_result)
        
        # 说明标签
        help_text = "提示: 输入拼音（如 'zhongwen' 或 'zhong wen'），按回车或点击转换"
        help_label = tk.Label(
            self.root,
            text=help_text,
            font=("微软雅黑", 9),
            bg='#f0f0f0',
            fg='#666666'
        )
        help_label.pack(pady=10)
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("微软雅黑", 9),
            bg='#e0e0e0',
            anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 设置焦点
        self.pinyin_entry.focus()
    
    def convert(self):
        """转换拼音"""
        pinyin = self.pinyin_var.get().strip()
        
        if not pinyin:
            self.result_listbox.delete(0, tk.END)
            return
        
        try:
            # 清空结果列表
            self.result_listbox.delete(0, tk.END)
            
            # 转换
            results = self.ime.convert(pinyin, top_k=10)
            
            if results:
                for i, result in enumerate(results, 1):
                    display_text = "{}. {}".format(i, result['text'])
                    self.result_listbox.insert(tk.END, display_text)
                
                self.status_var.set("找到 {} 个候选结果".format(len(results)))
            else:
                self.result_listbox.insert(tk.END, "无匹配结果")
                self.status_var.set("未找到匹配的汉字")
                
        except Exception as e:
            self.status_var.set("转换错误: {}".format(e))
    
    def select_result(self, event):
        """双击选择结果"""
        selection = self.result_listbox.curselection()
        if selection:
            index = selection[0]
            text = self.result_listbox.get(index)
            # 提取汉字部分
            if '. ' in text:
                chinese = text.split('. ', 1)[1]
                self.pinyin_var.set(chinese)
                self.status_var.set("已选择: {}".format(chinese))


def main():
    """主函数"""
    root = tk.Tk()
    
    # 设置DPI感知（Windows）
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    # 创建应用
    model_path = 'models/language_model.pkl'
    app = PinyinIMEGUI(root, model_path)
    
    # 运行
    root.mainloop()


if __name__ == '__main__':
    main()
