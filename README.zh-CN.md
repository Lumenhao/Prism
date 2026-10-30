<p align="center">
  <img src="assets/banner.png" alt="Prism — 读、写、说" width="100%">
</p>

<h1 align="center">Prism</h1>

<p align="center"><strong>论文读完了，却讲不出来？</strong><br>把同一篇论文拆成读、写、说三种练习，并留下可以前后比较的记录。</p>

<p align="center">
  <a href="README.md">English</a> · <b>简体中文</b>
</p>

<p align="center">
  <a href="https://lumenhao.github.io/Prism/"><strong>项目主页</strong></a> ·
  <a href="#一键开始">一键开始</a> ·
  <a href="#六个工作区">六个工作区</a> ·
  <a href="#常见问题">常见问题</a>
</p>

<p align="center"><sub>Windows 10/11 · Python 3.12 · 全程本机 · MIT</sub></p>

**Prism** 是一个本地优先的学术英语工作台。从 Zotero 里挑一篇论文，把它改成三分钟的讲述稿，听示范朗读，自己录一遍，拿到一份可以反复比较的报告，再把标注送进 Anki —— 全部在同一个窗口里完成。

---

## 你可能正卡在这三个地方

**读得懂，说不出。** 论文里的好句子读完就散了，轮到自己讲，只剩下 "This paper is about…"。

**改得动，不像自己。** 模板、语法检查、润色工具各管一段，复制粘贴来回切换，最后写出来的段落谁也不像。

**背了词，用不上。** 标注留在 Zotero，复习在 Anki，口语又是另一个软件；每天很忙，却看不出进步在哪。

Prism 不打算再给你一份功能清单。它把 **同一篇论文** 放进一条闭环：在 Library 里读，在 Write 里拆句型，在 Speak 里讲出来，在 Vocab 里复习。每一次练习都留下记录，下一次可以拿来比较。

## 一键开始

不需要先装 Python，也不需要读一长串安装说明。

1. **拿到代码**：`git clone https://github.com/Lumenhao/Prism.git`，或在 GitHub 页面点 **Code → Download ZIP** 后解压。
2. **双击 `Prism.bat`。**
   第一次启动会自动创建 `.venv`、安装依赖，并把模型目录指向 `E:\LumenSuite`。依赖约 1.5 GB，通常 5–15 分钟；装完工作台会自己打开。
3. **（可选）接上你自己的资料**：
   - **Zotero**：装好 Zotero 后，在 Prism 的 Settings 里填 `zotero.sqlite` 路径。默认会找 `~/Zotero/zotero.sqlite`。
   - **Anki**：装好 Anki 与 [AnkiConnect](https://ankiweb.net/shared/info/2055492159)（插件代码 `2055492159`），启动 Anki，然后在 **Vocab → 初始化牌组** 点一下。

第一次合成语音或分析录音时，会经 `hf-mirror.com` 下载 Kokoro（约 330 MB）和 Whisper `base.en`（约 150 MB），都落在 `E:\LumenSuite\models`，之后离线可用。

> 系统要求：Windows 10/11 x64；首次安装需要联网；建议至少 6 GB 空闲磁盘。没有 E 盘时会自动改用 `%LOCALAPPDATA%\LumenSuite`，也可以用环境变量 `LUMEN_SUITE` 指定位置。

### 装到哪里

```text
E:\LumenSuite
├─ Prism\      代码、.venv、data（录音 / 报告 / 快照）
├─ models\     Kokoro、Whisper、HuggingFace / Torch 缓存
├─ tools\      Python 3.12、Anki、Vale、FFmpeg（如已安装）
└─ cache\      uv / pip / 下载缓存
```

Prism 自己产生的数据都在 `data/`，已被 `.gitignore` 排除；与这台机器相关的路径写在 `config.local.json`，不会提交。

## 第一次使用的 10 分钟

1. **Overview**：先看本周练习、Zotero 规模、Anki 到期数。点 **Start session** 直接进入口语。
2. **Library**：搜索并打开一篇你最近要讲的论文，点 **生成讲述稿**。
3. **Speak**：选 `af_heart` 音色，生成示范音；跟读后上传录音，点 **Analyze**，拿到 WER、停顿、波形与音高。
4. **Write**：按论证功能（Introduction / Methods / Results / Discussion）挑一条 Phrasebank 句型，插入段落实验室，再点 **检查段落**。
5. **Vocab**：把 Zotero 里带翻译的标注一键导出成 Anki 卡片，第二天在 Anki 里复习。

<table>
<tr>
<td><img src="assets/screenshots/overview.png" alt="Overview"></td>
<td><img src="assets/screenshots/library.png" alt="Library"></td>
</tr>
<tr>
<td><img src="assets/screenshots/speak.png" alt="Speak"></td>
<td><img src="assets/screenshots/write.png" alt="Write"></td>
</tr>
</table>

<p align="center"><img src="assets/screenshots/report.png" alt="口语分析报告" width="88%"></p>

<p align="center"><img src="assets/screenshots/overview-light.png" alt="浅色主题" width="88%"></p>

## 六个工作区

| 工作区 | 它解决什么 | 你怎么用 |
|---|---|---|
| **Overview** | 今天该练什么，一眼看到 | 看连续天数、到期卡片、最近一次口语报告；点 **Start session** 开始 |
| **Library** | 论文散落在 Zotero，找不到也拆不开 | 搜索标题 / 作者 / 期刊；看摘要、标签、标注；打开 PDF、定位到 Zotero；一键生成 3 分钟讲述稿 |
| **Speak** | 会读不会说，也没人指出问题 | **Listen** 生成示范音；**Terms** 查 17 个术语的 YouGlish 语境；**Analyze** 上传录音，得到转写、WER、停顿、波形与音高 |
| **Write** | 句型记不住，段落写完心里没底 | 按论证功能检索 40 条 Phrasebank 句型；点句子插入段落实验室；Vale 与内置规则给出可执行的修改建议 |
| **Vocab** | 标注和复习两张皮 | 预览 Zotero 标注 → 导出到 Anki；查看三个牌组的到期数；启动 Anki 或初始化牌组 |
| **Settings** | 路径、端口、模型各在哪里 | 修改 Anki 地址、Anki 路径、Zotero 库、Kokoro 音色、Whisper 模型；查看各工具的真实状态；切换深色 / 浅色 |

所有耗时任务（TTS、录音分析、Anki 导入）都在后台执行，顶部有进度，窗口不会卡住；切换页面也不会中断任务。

## 它和「把十个工具拼在一起」的区别

- **一条主线**：Read → Write → Speak → Review。每个页面只呈现当前这一步需要的输入和结果，不会甩给你一屋子工具自己找。
- **本地优先**：Zotero 以只读快照访问；Anki 走本机 `127.0.0.1:8765`；录音、转写、报告都不上传。
- **可比较**：同一篇稿子可以反复录，报告保留 WER、停顿与音高；练习记录进入周视图和连续天数。
- **可退出**：每项能力都有命令行入口（见下文）。工作台只是把它们串起来，不是黑箱。

## 常见问题

**Anki 一直显示「未连接」，是牌组名的问题吗？**
不是。连接只取决于三件事：Anki 正在运行、AnkiConnect 插件已安装并启用、端口是 `8765`。牌组统一叫 `Prism::Vocab` / `Prism::Phrases` / `Prism::Listening`，只是品牌命名；旧的 `PaperToTalk::*` 牌组会在 **Vocab → 初始化牌组** 时自动迁移卡片并清理空壳。

**为什么第一次启动很慢？**
它在安装 CPU 版 PyTorch、Kokoro、faster-whisper 等依赖，并把缓存放在 E 盘。之后再启动只需几秒。

**模型和我的录音会被上传吗？**
不会。下载模型是唯一的联网步骤；练习数据只写本地 `data/`。

**可以不用 Zotero 或 Anki 吗？**
可以。Speak 和 Write 不依赖它们；Library 需要 Zotero 数据库，Vocab 需要 Anki。缺哪个，对应页面会给提示，其他功能照常可用。

**支持 macOS / Linux 吗？**
后端是 FastAPI + 静态前端，理论上可以运行；但目前只在 Windows 上验证过启动脚本与桌面窗口。其他系统可手动 `uv pip install -r requirements.txt`，再运行 `python -m uvicorn app.server:APP --port 7317`，然后用浏览器打开。

**怎么彻底删除？**
删除仓库目录，再删除 `E:\LumenSuite`（或 `LUMEN_SUITE` 指向的位置）。已导出的卡片存在于 Anki，需要在 Anki 里删除。

## 本机验证过的结果

- **341 篇** Zotero 文献的只读索引，中文文件名也能打开；
- **40 条** Phrasebank 种子卡写入 `Prism::Phrases`；
- Kokoro `af_heart` 合成 448 词 / **177.75 秒** 示范音；
- Whisper `base.en` + Praat 分析真实录音：WER **9.8%**、内容词 WER **15.7%**，波形 320 点、音高 260 点、27 条差异；
- YouGlish 17 条术语链接；Vale 3.25.1 与 FFmpeg 7.1 可执行文件被识别；
- 38 个单元测试、`scripts/validate.py` 与 `ruff` 全部通过。

尚未完成：mpvacious / Buzz 的图形界面流程仍需按 `speaking/mpvacious.md`、`speaking/buzz-and-praat.md` 手工操作；macOS / Linux 启动脚本未验证。

## 开发与命令行

```powershell
.\setup_env.ps1                     # 建环境（Prism.bat 会自动调用）
python -m unittest discover -s tests
python scripts\validate.py
ruff check .
```

工作台没有替换原来的管线，它们仍可单独调用：

```powershell
# 口语
.\.venv\Scripts\python speaking\speak.py tts speaking\samples\sample_talk.md --out speaking\samples\sample_talk.wav
.\.venv\Scripts\python speaking\speak.py links speaking\samples\sample_talk.md --out speaking\samples\youglish.md
.\.venv\Scripts\python speaking\speak.py check speaking\samples\take1.wav --script speaking\samples\sample_talk.md

# 词汇
.\.venv\Scripts\python vocab\anki_setup.py --check
.\.venv\Scripts\python vocab\zotero_to_anki.py --dry-run

# 写作检查
E:\LumenSuite\tools\vale\vale.exe --config=writing\.vale.ini path\to\draft.md
```

## 隐私与许可

- Zotero 只读；Anki 通过本机 AnkiConnect 写入；文章、标注、录音与卡片一律不上传。
- 代码 MIT；文档与训练材料 CC BY-NC 4.0；第三方归属见 [NOTICE.md](NOTICE.md) 与 [PRIVACY.md](PRIVACY.md)。
- 示例讲稿是 2004 年石墨烯论文的口语改写，不含原文段落或图片。
- `data/`、`config.local.json`、模型与录音均在 `.gitignore` 中。

## 致谢

界面气质参考 [odysseus](https://github.com/odysseus-dev/odysseus) 的深色工作台；语音、对齐、语法与卡片能力分别建立在 Kokoro、faster-whisper、Praat、Vale、AnkiConnect 之上。
