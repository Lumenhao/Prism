# 写作线：Phrasebank + LTeX+ + Vale

这条线的目标不是“让工具把句子改顺”，而是让你**在写 paper 时能主动调用学术句型，并且知道为什么这样写**。

## 三层分工

| 层 | 工具 | 管什么 | 不管什么 |
|---|---|---|---|
| 论证动作 | Academic Phrasebank / 本目录 `phrasebank_seed.csv` | 这一段要完成什么功能（指空白、描述方法、报告趋势、承认局限） | 具体内容、数据、引用 |
| 语法 | LTeX+（LanguageTool） | 冠词、介词、主谓一致、拼写、LaTeX 命令干扰 | 论证是否成立、术语是否统一 |
| 文风/术语 | Vale | 模糊词、无依据断言、数值与单位、术语写法一致性 | 语法细节、领域事实 |

三者不能互相替代：LTeX+ 不会告诉你“这段缺少 research gap”，Vale 也不会替你补实验。

## 一次性配置

### 1. LTeX+（VS Code / Neovim / Emacs）

1. 在 VS Code 扩展商店搜索 **LTeX+**（作者 ltex-plus），安装。
2. 按提示安装 Java 17（LTeX+ 依赖 Java）。
3. 把 `writing/ltex-settings.json` 的内容合并进 VS Code `settings.json`：
   - 命令面板 → `Preferences: Open User Settings (JSON)`；
   - 把 JSON 里的键合并进去（不要整个覆盖）。
4. 打开一个 `.tex` 或 `.md` 文件，右下角出现 LTeX+ 状态即可。

关键配置说明：

- `ltex.dictionary`：你的领域词，避免被当成拼写错误。
- `ltex.latex.commands`：告诉 LTeX+ `\cite{}`、`\ref{}` 里的内容不是正文。
- `ltex.additionalRules.enablePickyRules`：打开更严格的规则；会多一些提示，按需忽略。

### 2. Vale（文风 linter）

1. 安装 Vale CLI：从 [Vale Releases](https://github.com/vale-cli/vale/releases) 下载 `vale.exe`，放到 PATH；或 `scoop install vale`。
2. 在项目根目录运行（`StylesPath` 相对 `.vale.ini`）：
   ```powershell
   vale --config=writing/.vale.ini "path\to\your-draft.md"
   ```
3. 可选：VS Code 安装 **Vale** 扩展，指向 `writing/.vale.ini`。

现有规则：

| 规则 | 级别 | 作用 |
|---|---|---|
| `Weasel` | warning | very / really / a lot of 等模糊词 |
| `UnsupportedClaim` | warning | obviously / clearly / it is well known that |
| `Novelty` | suggestion | novel / for the first time / unprecedented |
| `NumberUnit` | warning | `100nm` → `100 nm`（SI 空格） |
| `Contractions` | suggestion | don't / it's 等口语缩略 |
| `Terminology` | error | h-BN → hBN、F4TCNQ → F4-TCNQ 等 |

这些规则是**保守的起点**，不是法律。学术写作里被动语态、hedging（may/might）、`novel` 有时是合理的；Vale 报错时先判断，再决定改不改。

### 3. Phrasebank 种子卡

`phrasebank/phrasebank_seed.csv` 有 40 条按功能分类的句型；运行 `python vocab/anki_setup.py` 后会导入 `Prism::Phrases`（重复项会跳过）。

卡片正面是**中文意图 + 功能标签**，背面是句型模板和领域例句。复习时要做的不是“认得这个句型”，而是**看到中文意图，10 秒内说出/写出一个结构正确的英文句子**。

## 写作流程（建议固定下来）

1. **任务卡**：写清读者、段落功能、完成标准、不能越过的边界。
2. **中文提纲**：3–5 条，每条对应一个段落功能。
3. **选句型**：从 Anki/`phrasebank_seed.csv` 选 3–5 个，不追求多。
4. **限时初稿**：15–25 分钟，不查整句翻译，不让 AI 代写。
5. **LTeX+**：先修语法/拼写/介词；一次只处理 1–3 类。
6. **Vale**：再修文风/术语/单位；术语错误优先。
7. **人工复读**：读出声，检查逻辑连接和“这段话到底在做什么”。
8. **记录修订**：用 `phrasebank/paragraph_lab.md` 保存初稿、工具反馈、修订稿和复盘。

## 4 周训练

见 [`phrasebank/training_plan.md`](phrasebank/training_plan.md)。四周分别练 Introduction、Methods、Results、Discussion；每周产出 1 段 100–150 词的段落，并做一次“无提示重写”。

## 常见问题

**Q: LTeX+ 把 LaTeX 命令报错。**
把自定义命令加进 `ltex.latex.commands`；环境加进 `ltex.latex.environments`。

**Q: Vale 对 `.tex` 报很多命令相关的错。**
先用 Markdown 写草稿跑 Vale，定稿后再放进 LaTeX；或者在 `.vale.ini` 里暂时移除 `[*.tex]`。

**Q: 句型卡背得很熟，写作时还是想不起来。**
说明你练的是“识别”而不是“产出”。把卡片正面改成中文意图，背面只留模板；每天 3 张，必须开口或手写，不能只在脑子里“觉得会”。

**Q: 一段里能不能多用几个句型？**
不要。一段 3 个左右足够；堆模板会让段落像拼贴。先保证功能清楚，再考虑句式变化。
