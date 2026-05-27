# 🎙️ Voice-Transcription-Breaker (同期声智能断句工具)

![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Offline](https://img.shields.io/badge/Status-Offline_Safe-success.svg)

**Voice-Transcription-Breaker** 是一款基于 DeepSeek 大语言模型（LLM）开发的本地化桌面 GUI 应用。专为新闻媒体工作者、记者和视频后期剪辑师打造。

在新闻制作和短视频剪辑中，长篇的采访录音（同期声）转写文本往往需要切分成适合做视频字幕的短句。传统工具大多只能“按字数”死板截断，导致主谓宾分离或语义破碎。本工具通过引入本地部署的 LLM 进行自然语言理解，实现了**真正的“自然语义级”断句**。

---

## ✨ 核心特性

* 🧠 **语义级智能断句**：彻底告别机械截断。模型能够精准识别主谓宾结构、并列短语和修饰成分，在保证单行字数（默认 15-18 字）的同时，确保断句符合人类自然朗读习惯。
* 🎯 **智能标签识别**：专为新闻稿件优化。自动识别并提取稿件中的 `【同期声】` 或 `【同期】` 标签内容，不破坏导语、配音等原稿结构。
* 🛡️ **极致隐私与安全**：**完全离线运行**。程序在代码底层强行禁用了 Socket 网络通信，并支持 CPU 动态量化推理（qint8），确保未公开的新闻稿件和机密素材绝对不会泄露。
* ⚡ **平滑的多线程架构**：内置单后台线程与异步队列调度。即使面对万字长文，也能保持 UI 界面流畅响应，完美避免多任务并发导致的 CPU 死锁和程序卡顿。
* 🧹 **深度文本清洗与排版**：内置强大的正则后处理引擎。
  * 自动将双斜杠 `//` 或 `\\` 转换为独立换行。
  * 智能合并语气词（如将“啊”、“呢”自动与下一句合并，避免单字成行）。
  * 防止介词（如“在”、“从”、“到”）错误出现在行首。

---

## 🛠️ 环境依赖与前置准备

### 1. 基础环境
* **操作系统**: Windows (推荐), macOS, Linux
* **Python 版本**: Python 3.8 或更高版本

### 2. 下载本地离线模型
本工具默认使用 [DeepSeek](https://huggingface.co/deepseek-ai) 系列开源模型，完全在本地 CPU 上运行。为了保证离线可用，请提前下载模型：
1. 前往 Hugging Face 或 魔搭社区 (ModelScope)。
2. 下载所需模型（推荐使用 `deepseek-coder-1.5b-base` 或其他适用的小参数模型）。
3. 将模型文件夹存放在本地任意目录，例如：`D:/models/deepseek-coder-1.5b-base`。

---

## 🚀 安装与运行
### 第一步：克隆代码仓库

git clone [https://github.com/你的用户名/Voice-Transcription-Breaker.git](https://github.com/你的用户名/Voice-Transcription-Breaker.git)
cd Voice-Transcription-Breaker

第二步：安装依赖包
建议使用虚拟环境（venv 或 conda）。在终端中运行以下命令安装核心依赖：

pip install -r requirements.txt
(核心依赖包含 torch, transformers, accelerate 等)

第三步：启动程序
python main.py

📖 使用指南
加载模型：打开软件后，在底部“模型路径”处点击【浏览...】选择你提前下载好的 DeepSeek 本地模型文件夹，然后点击【加载模型】。首次加载需等待几十秒至一分钟。

输入文本：将含有原稿或同期声文本的内容粘贴至左侧输入框。

功能筛选：

勾选 仅处理【同期声】：软件会自动提取包含 【同期声】 或 【同期】 标签的内容进行处理，忽略正文和配音。

取消勾选：对输入框内的全文进行强制断句。

开始处理：点击【开始断句】，弹出的进度条会实时显示处理进度。

获取结果：处理完成后，结果将展示在下方输出框，点击右下角【复制结果】即可直接用于视频剪辑软件。

📦 打包为独立 EXE (可选)
如果你希望将该工具发送给不懂代码的同事直接双击使用，可以通过 PyInstaller 将其打包为 .exe 可执行文件。本代码已内置了对打包环境（sys._MEIPASS）的兼容支持。

在项目根目录下执行以下命令：
pip install pyinstaller
pyinstaller --noconfirm --onedir --windowed --icon "logo.ico" --add-data "logo.ico;." main.py
提示：为避免打包后的程序体积过大（模型通常有数 GB），上述命令仅打包了代码和 UI。请将打包生成的文件夹和你的模型文件夹一起发给同事，并让他们在软件中手动选择一次模型路径即可。

📄 开源协议 (License)
本项目采用 MIT License 开源协议，允许任何人自由使用、修改和分发，但请保留原作者版权声明。

免责声明：本工具仅供学习交流和提高媒体工作效率使用。断句结果受限于本地大语言模型的理解能力，请在正式发布或上屏前进行必要的人工校对。
