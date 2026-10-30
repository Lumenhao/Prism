# Buzz + Praat：短报告的自检流程

> 目标：每次 60–90 秒的讲述，都能回答三个问题——
> 1. 我实际说了什么（转写）；
> 2. 哪里卡了、哪里太快（声学指标）；
> 3. 下一次只改哪一条（复盘）。

Buzz 和 Praat 不替代 `speak.py check`，三者分工如下：

| 工具 | 强项 | 弱项 | 什么时候用 |
|---|---|---|---|
| **Buzz** | GUI、即时转写、可直接改字幕、支持 live 录音 | 不做对齐评分、不做声学统计 | 想马上看到文字；自由讲述没有稿子 |
| **`speak.py check`** | 与稿子对齐、WER、填充词、音高/强度/停顿汇总 | 需要稿子；依赖 Python 环境 | 每周固定测量，做前后对比 |
| **Praat** | 看音高/强度曲线、手动核对停顿边界 | 全手动、不可批量 | 报告里数字异常，或想亲眼确认某一句 |

---

## 1. 安装

### Buzz

从 [chidiwilliams/buzz Releases](https://github.com/chidiwilliams/buzz/releases) 下载 Windows 安装包（`.exe`），安装后打开。

首次使用会在 `Preferences → Models` 里下载模型。建议：

- 英文短报告：`base.en` 或 `small.en`；
- 术语多、口音重：`medium.en`（更慢，但少一些术语误判）；
- 只想知道大意：`tiny.en`。

模型越大不等于评分越准。`check` 的 WER 只和“你实际说了什么”有关，转写错了要人工改。

### Praat

从 <https://www.praat.org> 下载 Windows 版，解压到固定目录，例如 `C:\Program Files\Praat\`。

确认命令行可用：

```powershell
& "C:\Program Files\Praat\Praat.exe" --version
```

### FFmpeg（可选）

如果 Buzz 或 mpvacious 提示缺少 FFmpeg，从 [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) 下载 `ffmpeg-release-essentials.zip`，解压后把 `bin` 加入 `PATH`。

---

## 2. 流程 A：有稿子的讲述（推荐）

适合组会片段、会议报告、答辩预演。

### 第 1 步：录 take1

手机或电脑录音，60–90 秒；安静房间，麦克风离嘴 15–20 cm；不要开美化/降噪以外的效果。

保存为 `speaking/samples/take1.wav`（或 `.m4a`，`check` 会自动调用 ffmpeg 解码）。

### 第 2 步：用 `check` 对齐稿子

```powershell
.\.venv\Scripts\python speaking\speak.py check speaking\samples\take1.wav `
  --script speaking\samples\sample_talk.md --textgrid
```

得到 `reports/check-take1.md`：

- WER、内容词错误率；
- 替换 / 缺失 / 多出的词；
- 语速、停顿次数、最长停顿；
- 音高 p10–p90、强度；
- 填充词与 ASR 低置信词。

### 第 3 步：用 Buzz 复核转写

把 `take1.wav` 拖进 Buzz → 选模型 → `Transcribe`。

重点不是看 Buzz 和 `check` 的数字是否一致，而是：

1. 找出 `check` 标为“缺失/替换”的实词，听原音确认；
2. 若是 ASR 把术语写错（`F4-TCNQ` → `f 4 t c n q`），在报告里标注“ASR 误判”，不算你的错误；
3. 若确实漏词、改词，记下是“没背熟”还是“临场改表达”。

### 第 4 步：用 Praat 看异常句

当报告里出现以下任一情况，再打开 Praat，不必每次都看：

- 音高曲线突然断掉或长时间平坦；
- 停顿次数与你的主观感受不一致；
- 某一句话听众反馈“没听清”。

打开方式：Praat → `Open → Read from file` → 选 wav → `View & Edit`。

看三样东西：

| 看什么 | 在哪 | 判断 |
|---|---|---|
| 音高 | 蓝色 Pitch 轨 | 句末是否自然下降；强调词是否有局部抬升 |
| 强度 | 绿色 Intensity 轨 | 句尾是否掉到听不见；填充词是否比实词更响 |
| 停顿 | 波形空白 + TextGrid | 停顿是否落在从句边界，而不是词组中间 |

### 第 5 步：只改一条，录 take2

从报告里选**一条**最影响理解的：

- 术语读法 → 改 `speaking/pronunciation.json`，重新生成 Kokoro 示范音；
- 语速过快 → 在稿子上标 3 个换气点；
- 填充词多 → 每句开头先停 0.3 秒；
- 重音平 → 每段只标 2 个对比重音。

重录同一段，再跑一次 `check`。比较两次的同一指标，不要换指标。

---

## 3. 流程 B：自由讲述（没有稿子）

适合即兴回答、Q&A 练习、组会临时发言。

1. **先录**：60 秒，不写稿，不重来。
2. **Buzz 转写**：导出 `.txt`。
3. **人工改一遍**：把 Buzz 的错词、术语、标点改对，存为 `reports/free-talk-script.md`。
   - 改的时候不要“顺手把句子写漂亮”，只还原你实际说出口的内容。
4. **用改好的文本当脚本**：

```powershell
.\.venv\Scripts\python speaking\speak.py check speaking\samples\free-talk.wav `
  --script reports\free-talk-script.md
```

5. **看结构，不只看发音**：自由讲述最常见的问题不是音，而是“没有路标”——没有 *first / because / what this means*。在转写稿上标出逻辑连接词，缺哪一类就补哪一类。

> 不要直接拿 Buzz 原始输出当脚本。那等于让同一个模型给自己打分，WER 会虚低。

---

## 4. 流程 C：用 Praat 批量看停顿

`speaking/praat_analysis.praat` 会一次输出汇总指标和 TextGrid：

```powershell
New-Item -ItemType Directory -Force reports\take1 | Out-Null
& "C:\Program Files\Praat\Praat.exe" --run speaking\praat_analysis.praat `
  speaking\samples\take1.wav reports\take1
```

输出：

- `praat_report.txt`：时长、发声时长、音高均值/最小/最大、强度、停顿次数与总时长、每分钟停顿率、最长停顿；
- `silences.TextGrid`：`silent` / `sounding` 区间。

默认参数：静音阈值 `-25 dB`、最短静音 `0.3 s`、最短发声 `0.1 s`。

**同一批录音必须用同一组参数**，否则数字不可比。房间噪声大时整体调到 `-20 dB`，然后固定下来。

在 Praat 里叠加：

1. `Open → Read from file` 打开 wav；
2. `Open → Read from file` 打开 `silences.TextGrid`；
3. 选中两者 → `View & Edit`；
4. 看 `silent` 区间是否落在你预期的换气点。

---

## 5. 一周怎么排

| 时间 | 动作 | 产出 |
|---|---|---|
| 周一 | 选 60–90 秒材料；标 5 个术语；跑 `speak.py links` | `youglish.md` |
| 周二 | Kokoro 示范音 → 跟读 → 录 take1 | `take1.wav` |
| 周三 | `check` + Buzz 复核；选一条问题 | `check-take1.md` |
| 周四 | 针对一条问题重录 take2 | `take2.wav` |
| 周五 | 只看 take1/take2 的同一指标；写 3 行复盘 | 复盘记录 |
| 周末 | 轻量泛听，不测量 | — |

Praat 不必每周都用。只有当 `check` 的数字和你的听感冲突时，才打开它做人工裁决。

---

## 6. 常见问题

**Q: Buzz 转写很慢。**
换小模型（`base.en`）；关闭其他占用 GPU/CPU 的程序；长音频先切成 90 秒片段。

**Q: Buzz 把术语全写错。**
正常。Whisper 的词表不含你的领域术语。把术语加进 `speaking/pronunciation.json` 只影响 Kokoro，不影响 Buzz；Buzz 的错词靠人工改，或在 Buzz 里使用带 initial prompt 的版本（若你的版本支持）。

**Q: `check` 的 WER 很高，但我觉得自己读得没错。**
先看对齐表里错的是不是实词。若是术语/数字/缩写，大概率是 ASR 误判；若确实是漏词、换词，再回听原音。

**Q: Praat 的停顿比我感觉的多。**
默认 `-25 dB` 会把呼吸、咂嘴也算成发声或静音。看 TextGrid 边界，必要时调整阈值后重跑；不要为了“数字好看”反复调参。

**Q: 录音里有过长的空白。**
可能是软件没录上，也可能是真的卡住。用 Praat 看波形：如果波形是一条直线，是录音问题；如果有微弱噪声，是停顿。

---

## 7. 隐私

- 录音里不要出现客户、同事、学生、患者或未公开项目信息；举例用虚构数据。
- Buzz 默认本地转写；如果你切换到在线模型/服务，先确认资料允许上传。
- 报告音频、截图、TextGrid 只用于个人学习，不公开发布含他人画面/声音的材料。
