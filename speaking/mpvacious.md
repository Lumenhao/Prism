# 用 mpvacious 从学术报告里挖表达

目标不是“把整场报告做成卡片”，而是把讲者反复使用的**学术动作**（引出问题、定义、 hedging、转折、答问）连声音带画面存下来，之后能在自己的讲述里调用。

mpvacious 是 mpv 的用户脚本：暂停在字幕上，按一下键，就把「字幕 + 音频片段 + 画面」送进 Anki。它补的是 Kokoro 给不了的东西：真实语速、停顿、重音、会场语气，以及讲者怎么处理追问。

---

## 1. 安装

需要三样东西：

1. **Anki** 与 **AnkiConnect**：Anki 里 `工具 → 插件 → 获取插件`，代码 `2055492159`，重启 Anki。
2. **mpv 0.41+**：Windows 用 [shinchiro 构建](https://sourceforge.net/projects/mpv-player-windows/files/)，解压后把 `mpv.exe` 所在目录加入 `PATH`，命令行能运行 `mpv --version`。
3. **mpvacious**：官方 PowerShell 安装脚本
   ```powershell
   irm https://raw.githubusercontent.com/Ajatt-Tools/mpvacious/HEAD/scripts/install.ps1 | iex
   ```
   如果不想直接执行远程脚本，就从 [Releases](https://github.com/Ajatt-Tools/mpvacious/releases) 下载，把整个 `mpvacious` 文件夹解压到：
   ```
   %APPDATA%\mpv\scripts\mpvacious\
   ```
   目录里应当能看到 `main.lua`。

验证：`mpv 任意视频.mp4`，按 `a` 能弹出 mpvacious 菜单即安装成功。

> 音频/截图生成失败时，安装 [FFmpeg](https://www.gyan.dev/ffmpeg/builds/) 并把 `bin` 加入 `PATH`，然后在配置里设 `use_ffmpeg=yes`。远程流（如直接播 YouTube 链接）不能走 FFmpeg，先下载到本地。

---

## 2. 配置

新建 `%APPDATA%\mpv\script-opts\subs2srs.conf`。**`=` 两边不要留空格**。

```ini
deck_name=Prism::Listening
model_name=AE Subs
sentence_field=Expression
secondary_field=Meaning
audio_field=Audio
image_field=Image
note_tag=mpvacious academic-talk
ankiconnect_url=127.0.0.1:8765
create_deck=yes
use_ffmpeg=yes
audio_format=mp3
snapshot_format=jpg
```

字段对应本项目的 `AE Subs` 笔记类型：

| mpvacious 设置 | AE Subs 字段 | 内容 |
|---|---|---|
| `sentence_field` | `Expression` | 字幕原文 |
| `secondary_field` | `Meaning` | 双语字幕或你的改写；没有就留空，之后补 |
| `audio_field` | `Audio` | 该句音频 |
| `image_field` | `Image` | 该句画面 |
| — | `Source` | 讲者 / 会议 / 链接，制卡后补 |

`note_tag` 用空格分隔多个标签。`allow_duplicates` 默认是 `yes`，同一句重复制卡不会报错，但会堆积；挖卡时留意。

先用 `vocab/anki_setup.py --check` 确认 `AE Subs` 存在，再开始制卡。

---

## 3. 准备字幕

优先用会议或期刊提供的官方字幕。没有时，对自己有权访问的报告可以下载后生成：

```bash
yt-dlp --write-subs --sub-langs en --convert-subs srt -o "%(title)s.%(ext)s" "<URL>"
```

自动字幕用 `--write-auto-subs`，但断句和术语错误更多，制卡前要改。

播放：

```bash
mpv --sub-file="talk.en.srt" talk.mp4
```

字幕与视频同名（`talk.en.srt`）时 mpv 会自动加载。

---

## 4. 制卡流程

默认键位（以仓库 README 为准）：

| 键 | 作用 |
|---|---|
| `a` | 打开 mpvacious 菜单 |
| `g` | 快速制卡菜单 |
| `Ctrl+n` | 导出当前字幕为 Anki 卡片 |
| `Ctrl+m` | 更新上一张卡 |
| `H` / `L` | 按字幕前后跳 |
| `Ctrl+h` / `Ctrl+H` | 重播当前句 / 回到句首 |
| `Ctrl+v` | 切换第二字幕 |

推荐流程：

1. **先完整看 5 分钟**，不要暂停。记下 3-5 个“如果是我会怎么说”的位置。
2. 回到这些位置，`Ctrl+H` 反复听，确认自己听清的是意思而不只是词。
3. 按 `g` 或 `Ctrl+n` 制卡，只改 `Meaning`：用一句自己的英文改写，或写中文功能提示（如“先承认对方合理，再分开两件事”）。
4. 一场 20 分钟的报告，控制在 **8-12 张**。超过 15 张通常说明在抄字幕，不是在学表达。
5. 当天在 Anki 里把这批卡过一遍；周五从里面挑 3 张，用进自己的 2 分钟讲述。

### 值得挖什么

| 学术动作 | 讲者可能怎么说 | 为什么值得留 |
|---|---|---|
| 引出问题 | “I want to start with a simple question…” | 开场不靠“Today I will introduce…” |
| 定义 | “By flat band, I mean…” | 把术语转成听者能接住的话 |
| 方法过渡 | “Let me walk you through the device.” | 从动机切到装置，听众不会掉线 |
| 证据限定 | “Our data suggest, but do not prove…” | 学术分寸，比 “prove” 安全 |
| 转折 | “That said, there are two limitations.” | 主动交底，反而增加可信度 |
| 答问修复 | “That's a fair point. Let me separate two things.” | 被追问时不慌，先拆问题 |
| 收束 | “The takeaway is this.” | 让听众带走一句话 |

不要挖：纯事实名词、一次性数字、你永远不会说的口头禅。

---

## 5. 卡片怎么复习

`AE Subs` 正面是 `Expression + Audio`，背面是 `Meaning + Image + Source`。

复习时：

1. **先听音频，不看字**，说出这句话在做什么（定义？让步？修复？）；
2. 看字幕，跟读一遍，模仿停顿和重音；
3. **翻面前**，用同一个句型造一句与你研究相关的话；
4. 翻面核对 `Meaning`；如果造不出来，这张卡还没学会。

只在“能造新句”时点 Good。只听懂了、觉得眼熟，点 Again 或 Hard。

---

## 6. 和另外两个工具的分工

| 工具 | 给你什么 | 不给你什么 |
|---|---|---|
| Kokoro | 标准、可控、可反复的示范音 | 真实语速、口音、会场互动 |
| YouGlish | 同一个词在多种真人语境里的发音 | 整段论证结构 |
| mpvacious | 真实讲者的节奏、重音、答问方式 | 系统纠音；它不判断你读得对不对 |
| Buzz + Praat | 你自己的声学证据：语速、停顿、音高 | 表达是否得体 |

顺序建议：先用 mpvacious 找到“想学的说法”，再用 Kokoro 把自己的稿子读顺，录音后用 Buzz/Praat 复盘，最后回到报告里听讲者怎么处理同一类场面。

---

## 7. 版权与隐私

- 只处理你有权访问的报告；卡片里的音频、画面仅用于个人学习，不公开发布整套 deck。
- 会议报告可能包含未发表数据、合作方信息或可识别人物；截图前确认可以留存。
- 不要把涉密报告、客户材料或未公开稿件上传到任何在线服务。

---

## 8. 常见问题

**AnkiConnect 连不上**
Anki 必须开着；浏览器打开 `http://127.0.0.1:8765` 应返回版本号。端口被占用时，在 AnkiConnect 设置里改 `webBindAddress`，并同步改 `ankiconnect_url`。

**没有音频 / 没有截图**
先装 FFmpeg 并设 `use_ffmpeg=yes`；远程流先下载到本地。仍失败时，在 mpv 控制台看报错，通常是编码器或路径问题。

**提示 model 不存在**
Anki 里的笔记类型名必须与 `model_name` 完全一致（`AE Subs`）。运行 `python vocab/anki_setup.py --check` 查看。

**卡片第一个字段为空**
mpvacious 要求首字段非空。确认 `AE Subs` 的 `Expression` 排在第一位，且字幕确实被选中。

**字幕对不上**
用 `H` / `L` 按字幕跳，不要按时间轴硬拖；必要时在配置里加 `audio_padding=0.1`，给音频前后留一点余量。

**想改键位**
在 `%APPDATA%\mpv\input.conf` 里覆盖，例如 `g script-binding mpvacious-quick-card-menu-open`。改完重启 mpv。
