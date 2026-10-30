# 口语线：示范音 → 跟读 → 录音复盘

这条线解决三个不同问题，不要混在一起：

1. **这个词怎么读**：Kokoro 给你可控的示范音，YouGlish 给你真人语境。
2. **我这段讲得怎么样**：Buzz 快速转写，`speak.py check` 给出可重复的声学指标，Praat 用来看曲线。
3. **大佬怎么组织一段学术表达**：mpvacious 把报告里的句子连声音带画面送进 Anki。

---

## 文件地图

```
speaking/
├── speak.py                 # tts / links / check 三个子命令
├── pronunciation.json       # 术语与符号的读法替换表
├── praat_analysis.praat     # 独立 Praat 脚本：音高、强度、停顿
├── buzz-and-praat.md        # Buzz 转写 + Praat 分析的具体流程
├── mpvacious.md             # 从学术报告挖表达
├── samples/
│   ├── sample_talk.md       # 3 分钟示例稿（基于 Novoselov 2004，含 [[...]] 标记）
│   └── youglish.md          # 由 sample_talk.md 生成的跟读清单
└── README.md
```

---

## 1. 一次性安装

### Kokoro 与 faster-whisper

在项目根目录：

```powershell
.\setup_env.ps1
```

脚本会建 `.venv`（优先 Python 3.12）并安装 `requirements.txt`。Kokoro 处理生词时需要 **espeak-ng**，Windows 装 MSI：

<https://github.com/espeak-ng/espeak-ng/releases>

装完重开终端，确认：

```powershell
.\.venv\Scripts\python -c "import kokoro, faster_whisper, parselmouth; print('ok')"
```

### Buzz（可选，GUI 快速转写）

从 [Releases](https://github.com/chidiwilliams/buzz/releases) 下载 Windows 安装包。它和 `check` 用的是同一类 Whisper 模型；Buzz 适合“我想马上看到文字”，`check` 适合“我想每周用同一把尺子量”。完整流程见 [buzz-and-praat.md](buzz-and-praat.md)。

### Praat

从 <https://www.praat.org> 下载 Windows 版，解压即用。看曲线：打开 wav → `View & Edit`；跑脚本见下文。

### 录音

手机自带录音即可。安静房间、麦克风离嘴 15-20 cm、不要开降噪以外的美化。每次录 **60-90 秒**，同一段话录两遍比录十段不同的话有用。

---

## 2. 三个命令

### `tts`：生成示范音

```powershell
.\.venv\Scripts\python speaking\speak.py tts speaking\samples\sample_talk.md `
  --out speaking\samples\sample_talk.wav --chunks
```

- 默认 voice `af_heart`、speed `0.95`；英音用 `--lang b`。
- 首次运行会从 Hugging Face 下载 Kokoro 模型；之后可离线使用。
- `--chunks` 额外输出逐段音频（`sample_talk-01.wav`…），方便一段一段跟读。
- `--dry-run` 只打印替换后的文本，用来检查术语有没有被读成字母串。
- 术语读法在 `pronunciation.json` 里改；键按整词匹配，`F4-TCNQ` 会读成 “F four T C N Q”。

先听示范音，再跟读。**不要用示范音当背景音乐循环**：它只负责给你一个可模仿的目标，不负责让你记住。

### `links`：生成 YouGlish 清单

```powershell
.\.venv\Scripts\python speaking\speak.py links speaking\samples\sample_talk.md `
  --out speaking\samples\youglish.md
```

- 默认只取 `[[...]]` 标记；加 `--all` 会把长词、缩写、带数字/连字符的词也加进来。
- `--accent us|uk|aus` 只是检索条件，不是质量等级。
- 每个词听 3 个片段：跟读 1 个、只听节奏 1 个、关页面复述 1 个。

### `check`：录音复盘

```powershell
.\.venv\Scripts\python speaking\speak.py check speaking\samples\take1.wav `
  --script speaking\samples\sample_talk.md --textgrid
```

输出 `reports/check-take1.md`，包括：

- WER、内容词错误率、替换/缺失/多出的对齐表；
- 发声语速、停顿次数、最长停顿、音高 p10-p90、强度；
- 填充词计数、ASR 低置信词；
- 三条“优先修”的建议。

`--textgrid` 会同时保存停顿标注，可拖进 Praat 和波形对齐看。

**怎么读这份报告**

| 看到什么 | 先别下结论 | 下一步 |
|---|---|---|
| WER 高 | ASR 对术语、数字、口音本来就会错 | 看对齐表里是不是实词；是实词再回听 |
| 某个术语总被识别成别的 | 可能 ASR 词表没有它 | 人耳确认；若你读得对，忽略 |
| 语速 > 175 wpm | 可能只是这段材料短 | 看长停顿和听众反馈；快而清楚不是罪 |
| 停顿很多 | 可能是思考，也可能是没背熟 | 把长句拆短，标换气点 |
| 音高跨度小 | 录音设备也会压平 | 换设备复测；再让真人听是否单调 |
| 填充词多 | ASR 会漏记，数值是下限 | 每句开头先停 0.3 s 再开口 |

报告末尾的“术语复核”不要跳过：ASR 把 `F4-TCNQ` 写成 `f 4 t c n q` 是常态，不是你的发音错误。

没有稿子的自由讲述，先用 Buzz 转写，再**人工改一遍**作为参考文本；直接拿 Buzz 的输出当脚本，等于让同一个模型给自己打分，WER 没有意义。

---

## 3. Praat 独立脚本

```powershell
New-Item -ItemType Directory -Force reports\take1 | Out-Null
& "C:\Program Files\Praat\Praat.exe" --run speaking\praat_analysis.praat `
  speaking\samples\take1.wav reports\take1
```

输出：

- `praat_report.txt`：时长、发声时长、音高均值/最小/最大、强度、停顿次数与总时长、每分钟停顿率、最长停顿；
- `silences.TextGrid`：`silent` / `sounding` 区间，可直接在 Praat 里叠加到波形。

默认静音阈值 `-25 dB`、最短静音 `0.3 s`、最短发声 `0.1 s`。房间噪声大时，阈值调到 `-20` 左右再比较；**同一批录音要用同一组参数**，否则数字不可比。

---

## 4. 三次过稿法

一段 90 秒的讲述，至少过三遍，每遍只做一件事。

### 第一遍：读顺（不看听众）

- 用 Kokoro 示范音听 2 遍，标出重读词和换气点；
- 跟读 3 遍，最后一遍 **关掉示范音**，自己读；
- 目标不是背下来，是“句子在嘴里不打架”。

### 第二遍：讲给一个人（不看稿）

- 只留关键词卡片，抬头讲；
- 录音；
- 讲完立刻用一句话复述自己讲了什么——如果复述不出来，结构有问题，不是发音问题。

### 第三遍：复盘（只看两条）

- 跑 `check`，只挑 **两条** 最影响理解的；
- 重录同一段，比较是否改善；
- 不要一次改五个毛病；改多了，不知道是哪一条起了作用。

---

## 5. 每周 60 分钟

| 时间 | 动作 | 产出 |
|---|---|---|
| 周一 10 min | 选一段 60-90 秒的讲述；标 5 个术语；跑 `links` | `youglish.md` |
| 周二 15 min | Kokoro 示范音 + 跟读 + 录 take1 | `take1.wav` |
| 周三 10 min | 跑 `check`；选两条问题 | `check-take1.md` |
| 周四 15 min | 针对两条问题重录 take2；对比 | `take2.wav` |
| 周五 10 min | 从一场报告挖 3 张卡（`mpvacious.md`），并用进新的 60 秒 | 3 张 `AE Subs` |
| 周末 | 轻量泛听；不复盘 | — |

四周换四个主题：① 介绍自己的装置/方法；② 解释一张图；③ 回应一个质疑；④ 给非本领域的人讲同一件事。第四个主题最能暴露“术语依赖”。

---

## 6. 评分表（每周一次，0-2 分）

| 维度 | 0 | 1 | 2 |
|---|---|---|---|
| 任务完成 | 听完不知道你要做什么 | 主旨清楚，下一步含糊 | 听众能复述主旨、依据和下一步 |
| 可理解度 | 多处需要重复 | 偶尔卡住，能靠上下文恢复 | 一次听懂，数字/责任/条件不被误解 |
| 节奏与重音 | 平或赶，听不出重点 | 有重读，但停顿位置不稳定 | 关键句前后有停顿，重音落在对比处 |
| 互动修复 | 被追问后崩掉 | 能说 “Sorry?” 但修不回来 | 能确认、改写、拆分问题并继续 |
| 语言准确 | 错误阻断理解 | 有错但不阻断 | 错误不干扰，词块调用自然 |

≥8 分且连续两周，才考虑换更难的听众或主题。分数只描述这一次任务，不是等级证书。

---

## 7. 14 天怎么判断有变化

第 1 天和第 14 天录**同一段 90 秒**，条件尽量一致（同一房间、同一设备、同一稿）。看四件事：

1. 同样的内容，停顿是否更少、更长或更短得更有意图；
2. `check` 里缺失的实词是否减少（排除 ASR 术语误判）；
3. 一位**没听过你讲**的人，能否一次复述主旨和一个细节；
4. 被追问时，你是否还能留在对话里，而不是退回稿子。

四项里有两项稳定改善，就已经是能力变化。WER 下降但听众仍然听不懂，说明你优化的是转写器，不是沟通。

---

## 8. 隐私与版权

- 录音里不要出现客户、同事、学生、患者或未公开项目信息；需要举例时用虚构数据。
- 上传到 Buzz、在线转写或 AI 工具前，确认资料允许上传；否则用本地模型。
- 报告音频与截图只用于个人学习；不要把含他人画面/声音的 deck 公开发布。
- YouGlish 上的视频属于原发布者；它只用于听音，不用于再分发。
