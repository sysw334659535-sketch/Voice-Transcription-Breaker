import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
import re

# 尝试导入分词库，若未安装则降级为字符硬切分
try:
    import jieba
except ImportError:
    jieba = None


class VoiceTranscriptionBreaker:
    def __init__(self, root):
        self.root = root
        self.root.title("同期声智能断句工具V4.5 Powered by sysw334659535-sketch")
        self.root.geometry("850x700")

        # 核心参数配置
        self.max_line_length = 18
        self.punct_to_space = "，；:;：。！？!?；;"

        self.sync_voice_filter_var = tk.BooleanVar(value=True)

        self.create_widgets()

    def create_widgets(self):
        # 顶部工具栏 (完整保留所有功能)
        btn_frame = tk.Frame(self.root, padx=10, pady=10)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="⚡ 极速智能断句", command=self.process_text).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="清空面板", command=self.clear_all).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(btn_frame, text="仅处理【同期/同期声】段落", variable=self.sync_voice_filter_var).pack(
            side=tk.RIGHT, padx=5)

        # 输入输出文本框
        self.input_text = scrolledtext.ScrolledText(self.root, height=12, font=("微软雅黑", 11))
        self.input_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.output_text = scrolledtext.ScrolledText(self.root, height=12, font=("微软雅黑", 11))
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 底部状态栏与复制按钮
        bottom_frame = tk.Frame(self.root, padx=10, pady=5)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)  # <-- 已修复为 tk.BOTTOM

        self.status_var = tk.StringVar(value="就绪 - V4.5 全场景自适应断句引擎已就位")
        tk.Label(bottom_frame, textvariable=self.status_var, anchor=tk.W, fg="gray").pack(side=tk.LEFT)

        ttk.Button(bottom_frame, text="一键复制结果", command=self.copy_to_clipboard).pack(side=tk.RIGHT)

    def process_text(self):
        if not jieba:
            messagebox.showwarning("警告", "未检测到 jieba 分词库，断句质量会下降。\n请在终端运行: pip install jieba")

        raw_text = self.input_text.get("1.0", tk.END)
        cleaned_text = raw_text.replace('\xa0', ' ').strip()

        if not cleaned_text:
            messagebox.showinfo("提示", "请输入有效的待处理文本")
            return

        # 根据勾选状态，走不同的分流逻辑
        if self.sync_voice_filter_var.get():
            # 【模式 A：同期声精准模式】
            lines = cleaned_text.splitlines()
            segments = []
            cur_seg, in_sync = [], False
            for line in lines:
                s = line.strip()
                if re.match(r"【同期(?:声)?[:：]?\s*】", s):
                    if cur_seg: segments.append("\n".join(cur_seg))
                    cur_seg = [re.sub(r"^【同期(?:声)?[:：]?\s*】", "", s).strip()]
                    in_sync = True
                elif re.match(r"【(?:导语|配音|正文|口播)[:：]?\s*】", s):
                    if in_sync and cur_seg: segments.append("\n".join(cur_seg))
                    cur_seg, in_sync = [], False
                elif in_sync and s:
                    cur_seg.append(s)
            if in_sync and cur_seg: segments.append("\n".join(cur_seg))

            if not segments:
                messagebox.showinfo("提示", "未在文本中检索到【同期声】或【同期】段落")
                return

            # 传入 is_sync_voice=True，强制启动身份识别
            final_out = "\n\n".join(
                [self.algorithmic_segmentation(s, is_sync_voice=True) for s in segments if s.strip()])
        else:
            # 【模式 B：全文本通用模式】
            # 不再进行宏观结构过滤，保留用户原本的段落感 (\n\n)
            paragraphs = cleaned_text.split("\n\n")
            # 传入 is_sync_voice=False，关闭身份识别，全文本无差别切分
            final_out = "\n\n".join(
                [self.algorithmic_segmentation(p, is_sync_voice=False) for p in paragraphs if p.strip()])

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, final_out)
        self.status_var.set("处理完成！已根据当前模式完成自适应断句。")

    def algorithmic_segmentation(self, text, is_sync_voice=True):
        """双层解构断句引擎：宏观掌控气口，微观保护语法"""

        # 1. 隔离括号互动
        text = re.sub(r'([（(].*?[）)])', r'\n\1\n', text)

        # 2. 转化人工断点
        text = text.replace("//", "\n").replace("\\\\", "\n").replace("/", " ").replace("\\", " ")

        # 3. 融合顿号
        text = text.replace("、", "")

        raw_lines = text.splitlines()
        final_lines = []
        is_first_line = True

        # 核心语法词性保护词库
        prefer_start_with = {"因为", "为了", "然后", "以及", "并且", "去", "来", "以便", "从而"}
        cant_end_with = {"和", "与", "跟", "及", "把", "被", "让", "向", "对", "在", "从", "由", "要", "会", "能",
                         "不能", "是", "有", "这", "那", "为", "一些", "这些", "那些", "一个", "这种", "那种", "个",
                         "名", "位"}
        cant_start_with = {"的", "地", "得", "了", "着", "过"}

        for line in raw_lines:
            line = line.strip()
            if not line:
                continue

            # 【核心修复点】：只有在 is_sync_voice 为 True 时才剥离首行身份牌
            if is_sync_voice and is_first_line and not line.startswith(("（", "(")):
                is_first_line = False

                # 轨1：找冒号
                colon_match = re.search(r'[:：]', line)
                if colon_match and colon_match.start() < 35:
                    speaker_part = line[:colon_match.end()].strip()
                    dialogue_part = line[colon_match.end():].strip()
                else:
                    # 轨2：找空格兜底
                    line_frags = line.split(maxsplit=2)
                    if len(line_frags) >= 3:
                        if len(line_frags[1]) <= 4:
                            speaker_part = line_frags[0] + " " + line_frags[1]
                            dialogue_part = line_frags[2]
                        else:
                            speaker_part = line_frags[0]
                            dialogue_part = line_frags[1] + " " + line_frags[2]
                    elif len(line_frags) == 2:
                        if len(line_frags[1]) <= 4:
                            speaker_part = line_frags[0] + " " + line_frags[1]
                            dialogue_part = ""
                        else:
                            speaker_part = line_frags[0]
                            dialogue_part = line_frags[1]
                    else:
                        speaker_part = line
                        dialogue_part = ""

                if speaker_part:
                    final_lines.append(speaker_part)
                line_text = dialogue_part
            else:
                # 普通文本模式下，或者非首行，直接进入待切分正文
                line_text = line

            if not line_text.strip():
                continue

            # 纯括号互动断句
            if line_text.startswith(("（", "(")) and line_text.endswith(("）", ")")):
                p_words = list(jieba.cut(line_text)) if jieba else [line_text[i:i + 5] for i in
                                                                    range(0, len(line_text), 5)]
                temp_p = ""
                for pw in p_words:
                    if len(temp_p) + len(pw) > self.max_line_length:
                        if temp_p: final_lines.append(temp_p)
                        temp_p = pw
                    else:
                        temp_p += pw
                if temp_p: final_lines.append(temp_p)
                continue

            # 替换杂乱标点为内部温和空格
            for p in self.punct_to_space:
                line_text = line_text.replace(p, " ")

            # 切分为宏观气口组
            breath_groups = [g.strip() for g in line_text.split() if g.strip()]

            current_sub_line = ""
            for group in breath_groups:
                # 第一层：单气口块超长微观解构
                if len(group) > self.max_line_length:
                    if current_sub_line:
                        final_lines.append(current_sub_line)
                        current_sub_line = ""

                    words = list(jieba.cut(group)) if jieba else [group[i:i + 5] for i in range(0, len(group), 5)]
                    temp_words = []
                    temp_len = 0

                    for w in words:
                        if temp_len + len(w) > self.max_line_length or (w in prefer_start_with and temp_len >= 8):
                            if temp_words and temp_words[-1] in cant_end_with and len(temp_words) > 1:
                                dangling_w = temp_words.pop()
                                final_lines.append("".join(temp_words))
                                temp_words = [dangling_w, w]
                                temp_len = len(dangling_w) + len(w)
                            elif w in cant_start_with and temp_words:
                                temp_words.append(w)
                                final_lines.append("".join(temp_words))
                                temp_words = []
                                temp_len = 0
                            else:
                                if temp_words: final_lines.append("".join(temp_words))
                                temp_words = [w]
                                temp_len = len(w)
                        else:
                            temp_words.append(w)
                            temp_len += len(w)
                    if temp_words:
                        current_sub_line = "".join(temp_words)

                else:
                    # 第二层：宏观拼装
                    if not current_sub_line:
                        current_sub_line = group
                    else:
                        if len(current_sub_line) + len(group) <= self.max_line_length:
                            current_sub_line += group
                        else:
                            final_lines.append(current_sub_line)
                            current_sub_line = group

            if current_sub_line:
                final_lines.append(current_sub_line)

        return "\n".join(final_lines)

    def clear_all(self):
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
        self.status_var.set("已清空")

    def copy_to_clipboard(self):
        content = self.output_text.get("1.0", tk.END).strip()
        if content:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.status_var.set("✅ 结果已复制到系统剪贴板")
        else:
            messagebox.showinfo("提示", "没有可复制的内容")


if __name__ == "__main__":
    root = tk.Tk()

    try:
        icon_path = r"C:\Users\33465\Desktop\logo.ico"
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except Exception:
        pass

    app = VoiceTranscriptionBreaker(root)
    root.mainloop()
