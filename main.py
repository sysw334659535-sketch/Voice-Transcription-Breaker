# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import threading
import os
import sys
import re


class VoiceTranscriptionBreaker:
    def __init__(self, root):
        self.root = root
        self.root.title("同期声智能断句工具 V2.3")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # 配置参数
        self.max_line_length = 18
        self.ideal_line_length = 15
        self.punctuation_to_remove = "，、；:;：。！？!?；;/\\"
        self.punctuation_to_keep = "《》「」『』【】〈〉〔〕〖〗\"\"''（）()%±+-×÷=≠≈≤≥"
        self.voice_words = {"好", "嗯", "哦", "哎", "啊", "呀", "吧", "呢", "啦", "嘿", "呵", "嗨"}

        # 模型路径
        if getattr(sys, 'frozen', False):
            self.model_path = os.path.join(sys._MEIPASS, "deepseek_model")
        else:
            self.default_model_path = "D:/models/deepseek-coder-1.5b-base"
            self.model_path = self.default_model_path

        self.model = None
        self.tokenizer = None

        # 开关
        self.sync_voice_filter_var = tk.BooleanVar(value=True)

        self.create_widgets()
        self.status_label.config(text="请先选择并加载模型")

    def create_widgets(self):
        info_frame = tk.Frame(self.root, padx=10, pady=5)
        info_frame.pack(fill=tk.X)
        self.status_label = tk.Label(info_frame, text="就绪", font=("微软雅黑", 9), fg="blue")
        self.status_label.pack(side=tk.RIGHT)

        load_frame = tk.Frame(self.root, padx=10, pady=5)
        load_frame.pack(fill=tk.X)
        ttk.Button(load_frame, text="加载模型", command=self.load_model_manually).pack(side=tk.LEFT, padx=5)
        tk.Label(load_frame, text="启动时需手动加载模型以避免错误", font=("微软雅黑", 9), fg="red").pack(side=tk.LEFT,
                                                                                                         padx=5)

        input_frame = tk.LabelFrame(self.root, text="输入同期声文本", padx=10, pady=5)
        input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.input_text = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, height=10, font=("微软雅黑", 11))
        self.input_text.pack(fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(self.root, padx=10, pady=5)
        btn_frame.pack(fill=tk.X)
        ttk.Checkbutton(btn_frame, text="仅处理【同期声】", variable=self.sync_voice_filter_var).pack(side=tk.RIGHT,
                                                                                                    padx=5)
        self.process_btn = ttk.Button(btn_frame, text="开始断句", command=self.process_text, state=tk.DISABLED)
        self.process_btn.pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="清空", command=self.clear_all).pack(side=tk.RIGHT, padx=5)

        path_frame = tk.Frame(self.root, padx=10, pady=5)
        path_frame.pack(fill=tk.X)
        tk.Label(path_frame, text="模型路径:", font=("微软雅黑", 9)).pack(side=tk.LEFT)
        self.path_var = tk.StringVar(value=self.model_path)
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=50)
        path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(path_frame, text="浏览...", command=self.browse_model_path).pack(side=tk.RIGHT, padx=5)

        output_frame = tk.LabelFrame(self.root, text="断句结果", padx=10, pady=5)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, height=10, font=("微软雅黑", 11))
        self.output_text.pack(fill=tk.BOTH, expand=True)

        status_bar = tk.Frame(self.root, bd=1, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var = tk.StringVar(value="准备就绪 - 请先加载模型")
        tk.Label(status_bar, textvariable=self.status_var, anchor=tk.W, padx=5).pack(side=tk.LEFT)
        ttk.Button(status_bar, text="复制结果", command=self.copy_to_clipboard).pack(side=tk.RIGHT, padx=5, pady=2)

    def browse_model_path(self):
        if getattr(sys, 'frozen', False):
            messagebox.showinfo("提示", "打包版本已内置模型，无需选择路径")
            return
        path = filedialog.askdirectory(title="选择DeepSeek模型目录", initialdir=self.default_model_path)
        if path:
            self.model_path = path
            self.path_var.set(self.model_path)
            self.status_var.set(f"已选择模型路径: {os.path.basename(self.model_path)}")

    def load_model_manually(self):
        if getattr(sys, 'frozen', False):
            self.model_path = os.path.join(sys._MEIPASS, "deepseek_model")
            if not os.path.exists(self.model_path):
                messagebox.showerror("错误", "内置模型文件缺失，请重新获取程序")
                return
        else:
            if not os.path.exists(self.model_path):
                messagebox.showerror("错误", f"模型路径不存在: {self.model_path}")
                return

        self.status_label.config(text="正在加载模型...")
        self.process_btn.config(state=tk.DISABLED)
        self.status_var.set("模型加载中... 这可能需要几分钟")
        self.model = None
        self.tokenizer = None
        threading.Thread(target=self._load_model_in_thread, daemon=True).start()

    def _load_model_in_thread(self):
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=True)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path, torch_dtype=torch.float16, device_map="cpu", trust_remote_code=True
            )
            self.model = torch.quantization.quantize_dynamic(self.model, {torch.nn.Linear}, dtype=torch.qint8)
            self.model.eval()
            torch.set_num_threads(os.cpu_count())
            self.root.after(0, lambda: self.status_label.config(text="模型加载完成"))
            self.root.after(0, lambda: self.process_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.status_var.set(f"模型已加载: {os.path.basename(self.model_path)}"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"模型加载失败: {str(e)}"))
            self.root.after(0, lambda: self.status_label.config(text="模型加载失败"))
            self.root.after(0, lambda: self.status_var.set("模型加载失败，请检查路径和依赖"))
            self.model = None
            self.tokenizer = None

    def process_text(self):
        if self.model is None or self.tokenizer is None:
            messagebox.showerror("错误", "请先成功加载模型")
            return

        text = self.input_text.get("1.0", tk.END).strip()

        if self.sync_voice_filter_var.get():
            lines = text.splitlines()
            filtered_lines = []
            current_segment = []
            in_sync_voice = False
            for line in lines:
                stripped = line.strip()
                # 修复：使用正则兼容【同期声】和【同期】两种写法（"声"字变为可选）
                if re.match(r"【同期声?[:：]?\s*】", stripped):
                    if current_segment:
                        filtered_lines.extend(current_line.rstrip() for current_line in current_segment)
                        filtered_lines.append("##SEGMENT##")
                    current_segment = [line]
                    in_sync_voice = True
                elif re.match(r"【(?:导语|配音|正文)[:：]?\s*】", stripped):
                    if in_sync_voice and current_segment:
                        filtered_lines.extend(current_line.rstrip() for current_line in current_segment)
                        filtered_lines.append("##SEGMENT##")
                    current_segment = []
                    in_sync_voice = False
                elif in_sync_voice:
                    current_segment.append(line)
            if in_sync_voice and current_segment:
                filtered_lines.extend(current_line.rstrip() for current_line in current_segment)
                filtered_lines.append("##SEGMENT##")

            text = "\n".join(filtered_lines)
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = text.lstrip('\n')

            has_content = any("##SEGMENT##" not in line and line.strip() for line in text.splitlines())
            if not has_content:
                messagebox.showinfo("提示", "未检测到【同期声】或【同期】内容")
                return
        else:
            if not text.strip():
                messagebox.showinfo("提示", "请输入需要断句的文本")
                return

        self.process_btn.config(state=tk.DISABLED)
        self.output_text.delete("1.0", tk.END)

        progress_window = tk.Toplevel(self.root)
        progress_window.title("处理中...")
        progress_window.geometry("300x100")
        progress_window.transient(self.root)
        progress_window.grab_set()
        progress_label = tk.Label(progress_window, text="正在处理文本...")
        progress_label.pack(pady=10)
        progress_bar = ttk.Progressbar(progress_window, orient="horizontal", length=280, mode="determinate")
        progress_bar.pack(pady=5)

        threading.Thread(
            target=self._process_text_in_background,
            args=(text, progress_bar, progress_window, progress_label),
            daemon=True
        ).start()

    def _process_text_in_background(self, text, progress_bar, progress_window, progress_label):
        try:
            chunks = self.split_text_into_chunks(text)
            total_chunks = len(chunks)
            results = []

            for i, chunk in enumerate(chunks):
                result = self._process_single_chunk(chunk)
                results.append(result)

                completed = i + 1
                progress = int(completed / total_chunks * 100)
                self.root.after(0, lambda p=progress: progress_bar.config(value=p))
                self.root.after(0,
                                lambda c=completed, t=total_chunks: progress_label.config(text=f"处理中... ({c}/{t})"))

            final_result = "".join(results)
            final_text = self.post_process(final_result)

            self.root.after(0, lambda: self.output_text.delete("1.0", tk.END))
            self.root.after(0, lambda: self.output_text.insert(tk.END, final_text))
            self.root.after(0, lambda: self.status_var.set("处理完成"))
            self.root.after(0, lambda: self.process_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: progress_window.destroy())

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"处理失败: {str(e)}"))
            self.root.after(0, lambda: self.status_var.set("处理失败"))
            self.root.after(0, lambda: self.process_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: progress_window.destroy())

    def _process_single_chunk(self, chunk):
        if self.model is None or self.tokenizer is None:
            return chunk

        prompt = (
            f"你是专业新闻同期声断句专家，任务是按自然语义停顿将文本断成短句，每行控制在{self.ideal_line_length}字左右。\n\n"
            f"【严格断句规则】：\n"
            f"1. 语义优先：主谓宾结构不能拆分\n"
            f"2. 并列结构：用“和”“或”“以及”连接的短语保持完整\n"
            f"3. 修饰成分：定语、状语尽量与中心词合并\n"
            f"4. 语气词处理：嗯、啊、呀、吧等必须与下一句合并\n"
            f"5. 标点处理：\n"
            f"   - 去除：{self.punctuation_to_remove}\n"
            f"   - 保留：{self.punctuation_to_keep}\n"
            f"6. 每行长度：{self.ideal_line_length}-{self.max_line_length}字，超长强制断在语义边界\n"
            f"7. 禁止断在：人名后、数量词后、动词后、介词后\n\n"
            f"文本：\n{chunk}\n\n"
            f"请直接输出断句后的文本，每行一句，不要编号，不要解释：\n"
        )

        try:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    attention_mask=inputs.attention_mask,
                    max_new_tokens=min(512, len(chunk) * 2),
                    temperature=0.35,
                    top_p=0.9,
                    do_sample=True,
                    num_beams=1,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    early_stopping=True,
                )
            result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)[len(prompt):].strip()
            return result
        except Exception as e:
            print(f"处理块失败: {e}")
            return chunk

    def split_text_into_chunks(self, text, max_length=512):
        sentences = re.split(f'([{self.punctuation_to_keep}])', text)
        chunks = []
        current_chunk = ""
        for i in range(0, len(sentences), 2):
            sentence = sentences[i] + sentences[i + 1] if i < len(sentences) - 1 else sentences[i]
            if len(current_chunk) + len(sentence) > max_length and current_chunk:
                chunks.append(current_chunk)
                current_chunk = sentence
            else:
                current_chunk += sentence
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    def post_process(self, text):
        text = text.replace("//", "\n").replace("\\\\", "\n")

        for punct in self.punctuation_to_remove:
            text = text.replace(punct, " ")

        raw_lines = text.splitlines()
        lines = []
        for line in raw_lines:
            cleaned_line = re.sub(r'[ \t]+', ' ', line).strip()
            if cleaned_line:
                lines.append(cleaned_line)

        processed_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if line == "##SEGMENT##":
                processed_lines.append(line)
                i += 1
                continue
            if line in self.voice_words and i + 1 < len(lines):
                next_line = lines[i + 1]
                if next_line and next_line != "##SEGMENT##":
                    processed_lines.append(f"{line} {next_line}")
                    i += 2
                    continue
            processed_lines.append(line)
            i += 1

        final_lines = []
        for line in processed_lines:
            if line == "##SEGMENT##":
                final_lines.append(line)
                continue
            if len(line) <= self.max_line_length:
                final_lines.append(line)
            else:
                words = line.split()
                current = ""
                for word in words:
                    if len(current) + len(word) > self.max_line_length and current:
                        final_lines.append(current.strip())
                        current = word
                    else:
                        current += " " + word if current else word
                if current:
                    final_lines.append(current.strip())

        result_lines = []
        for i, line in enumerate(final_lines):
            if line == "##SEGMENT##":
                result_lines.append(line)
                continue
            if i > 0 and result_lines and result_lines[-1] in self.voice_words:
                result_lines[-1] = f"{result_lines[-1]} {line}"
            else:
                result_lines.append(line)

        # 7. 修复：使用正则同时去除【同期声】和【同期】两种标签
        cleaned_lines = []
        for line in result_lines:
            if line == "##SEGMENT##":
                cleaned_lines.append(line)
                continue
            line = re.sub(r"【同期声?】", "", line).strip()
            if line:
                cleaned_lines.append(line)

        result_text = "\n".join(cleaned_lines)
        segments = result_text.split("##SEGMENT##")
        output_lines = []
        for i, segment in enumerate(segments):
            segment = segment.strip()
            if not segment:
                continue
            seg_lines = [line for line in segment.splitlines() if line.strip()]

            merged = []
            for j, line in enumerate(seg_lines):
                if line in {"在", "从", "到", "于", "为", "被", "把"} and j > 0:
                    merged[-1] = f"{merged[-1]} {line}"
                else:
                    merged.append(line)
            output_lines.extend(merged)
            if i < len(segments) - 1:
                output_lines.append("")

        return "\n".join(output_lines).rstrip()

    def clear_all(self):
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
        self.status_var.set("已清空")

    def copy_to_clipboard(self):
        result = self.output_text.get("1.0", tk.END)
        if result.strip():
            self.root.clipboard_clear()
            self.root.clipboard_append(result)
            self.status_var.set("结果已复制到剪贴板")
        else:
            messagebox.showinfo("提示", "没有内容可复制")


def disable_network():
    def socket_send(*args, **kwargs):
        raise ConnectionError("程序网络功能已禁用")

    def socket_connect(*args, **kwargs):
        raise ConnectionError("程序网络功能已禁用")

    import socket
    original_send = socket.socket.send
    original_connect = socket.socket.connect
    socket.socket.send = socket_send
    socket.socket.connect = socket_connect
    return original_send, original_connect


if __name__ == "__main__":
    try:
        original_send, original_connect = disable_network()
    except Exception as e:
        print(f"网络禁用失败: {e}")

    root = tk.Tk()
    try:
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(sys._MEIPASS, "logo.ico")
        else:
            icon_path = r"logo.ico"
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
    except Exception as e:
        print(f"图标加载失败: {e}")

    app = VoiceTranscriptionBreaker(root)
    root.mainloop()
