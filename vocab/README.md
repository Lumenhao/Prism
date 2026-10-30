# 词汇线：Zotero / Yomitan → Anki

这条线解决一个问题：**读论文时查过的词，不要停在 Zotero 的注释里，要变成每天会提醒你复习的卡片。**

## 数据流

```
Zotero PDF 标注（带翻译注释） ──┐
                                ├─→ Anki「Prism::Vocab」→ 每日复习提醒
Yomitan 网页划词 ───────────────┘
```

## 一次性设置

1. **安装 Anki**（[apps.ankiweb.net](https://apps.ankiweb.net/)）。
2. **安装 AnkiConnect**：Anki → 工具 → 插件 → 获取插件 → 输入 `2055492159` → 重启。
3. **建牌组和笔记类型**：
   ```powershell
   python vocab/anki_setup.py
   ```
   会创建：
   - `Prism::Vocab`（词汇）
   - `Prism::Phrases`（学术句型，含 40 张种子卡）
   - `Prism::Listening`（报告/字幕听力卡）
   - 笔记类型：`AE Vocab`、`AE Phrase`、`AE Subs`
4. **配置 Zotero PDF Translate**：
   - 安装 [zotero-pdf-translate](https://github.com/windingwind/zotero-pdf-translate)；
   - 设置里打开 **Automatically Translate Annotation**，让翻译写进标注注释；
   - 目标语言选中文；翻译服务按你的网络情况选。
5. **配置 Yomitan**：见 [yomitan_setup.md](yomitan_setup.md)。
6. **配置提醒**：见下方“每日提醒”。

## Zotero → Anki

先预览（不会写 Anki）：

```powershell
python vocab/zotero_to_anki.py --dry-run
```

确认无误后正式导入：

```powershell
python vocab/zotero_to_anki.py
```

常用参数：

| 参数 | 作用 |
|---|---|
| `--since 2026-10-01` | 只导出该日期之后的标注 |
| `--include-untranslated` | 没有翻译注释的标注也导出（Translation 为空，打 `needs_translation` 标签） |
| `--tsv out.tsv` | 同时写一份 TSV，可手动导入 Anki |
| `--offline` | 不连 Anki，只统计待写入；配合 `--tsv out.tsv` 导出 |
| `--update` | 更新已导出卡片的字段（Zotero 里改了翻译后重跑） |
| `--limit 20` | 只处理 20 条，调试用 |

脚本读取的是 `zotero.sqlite` 的临时快照，Zotero 可以保持打开；它**不会修改** Zotero 数据。

**卡片长什么样**

- `Word`：你划的原文（词、短语或整句）
- `Translation`：Zotero 标注注释里的翻译
- `Source`：论文标题 + 页码
- `Link`：`zotero://select/library/items/<key>`，点击可跳回 Zotero
- `Added`：标注日期

## Yomitan → Anki

按 [yomitan_setup.md](yomitan_setup.md) 配置好后，网页划词 → 点 + → 自动进 Anki。标签 `yomitan web`。

## 每日提醒

`remind.ps1` 会检查三个牌组的到期数量，并用 Windows 通知提醒；如果 Anki 没开，会尝试启动它。

先手动测一次：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\vocab\remind.ps1
```

一键注册每天 20:30 的提醒（右键 PowerShell → 以当前用户运行即可，不需要管理员）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\vocab\install_reminder.ps1
```

常用参数：

| 参数 | 作用 |
|---|---|
| `-Time "07:30"` | 改提醒时间 |
| `-TaskName "Prism Review"` | 改计划任务名 |
| `-OpenAnki` | 提醒时顺便打开 Anki |
| `-Uninstall` | 删除计划任务 |

脚本会把当前仓库的绝对路径写进任务，移动目录后重新运行一次即可。

等价的手动命令：

```powershell
schtasks /Create /SC DAILY /TN "Prism Review" ^
  /TR "powershell -NoProfile -ExecutionPolicy Bypass -File \"<repo>\vocab\remind.ps1\"" ^
  /ST 20:30
schtasks /Delete /TN "Prism Review" /F
```

## 复习节奏（建议）

- **每天 10–15 分钟**：先复习到期卡片，再学 5–10 张新卡。
- **新卡上限**：Anki 牌组 Options → New cards/day = 10；Reviews/day = 100。不要一开始设 50，第二周会崩。
- **一个卡片只测一个决定**：正面看到词/原句，回忆“在这个语境里它是什么意思/怎么用”；不要正面就给中文答案。
- **每周复盘**：把连续答错的卡单独打标签 `leech`，回到原文看整段，而不是硬背。

## 常见问题

**Q: 提示无法连接 AnkiConnect。**
打开 Anki；浏览器访问 `http://127.0.0.1:8765` 应显示版本信息。若端口被占用，改 AnkiConnect 配置和 `config.json` 里的 `anki.url`。

**Q: 没有导出任何标注。**
Zotero 里大部分标注只有原文、没有翻译注释。打开 PDF Translate 的自动翻译，或先加 `--include-untranslated` 导出原文，之后在 Anki 里补翻译。

**Q: 同一篇论文重复导入。**
脚本用 `data/zotero_export_state.json` 记住已导出的 annotation ID；删除这个文件会导致重复检查退化为 Anki 的首字段判重。一般不要删。

**Q: 想换牌组名。**
改 `config.json` 里的 `anki.decks`，重新运行 `anki_setup.py` 建新牌组；旧卡片不会自动迁移。
