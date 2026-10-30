# Yomitan → Anki 配置

目标：在网页（arXiv HTML、博客、新闻、文档）上划词，一键把**词/短语 + 释义 + 原句 + 来源链接**送进 Anki 的 `PaperToTalk::Vocab`，并自动进入复习。

## 1. 前置

1. Anki 已安装，AnkiConnect 已安装（插件代码 `2055492159`），Anki 保持运行。
2. 已运行 `python vocab/anki_setup.py`，确认 `AE Vocab` 笔记类型和牌组存在。
3. 浏览器安装 [Yomitan](https://github.com/yomidevs/yomitan)（Chrome / Firefox / Edge 扩展商店均可）。

## 2. 安装词典

Yomitan 本身不带词典。打开 Yomitan 设置 → Dictionaries → Import，导入你有权使用的词典，例如：

- 英汉词典（ECDICT 衍生的 Yomitan 版本）；
- 牛津/朗文等**你已购买或有授权**的词典（不要从来源不明的站点下载盗版）。

学术阅读更推荐“英英 + 英汉”各一本：英英看搭配和语域，英汉快速确认义项。

## 3. 开启 Anki 集成

Yomitan 设置 → Anki：

- **Enable Anki integration**：开
- **AnkiConnect server**：`http://127.0.0.1:8765`
- **Deck**：`PaperToTalk::Vocab`
- **Model**：`AE Vocab`
- **Tags**：`yomitan web`

字段映射（Yomitan 的 marker 写在字段值里）：

| Anki 字段 | Yomitan 值 |
|---|---|
| Word | `{expression}` |
| Translation | `{glossary}` |
| Context | `{sentence}` |
| Source | `{document-title}` |
| Link | `{url}` |
| Audio | `{audio}` |
| Added | 留空（由脚本/Zotero 填） |

如果 `{audio}` 没有声音，检查 Yomitan 的 Audio sources 是否配置；没有也可以留空。

## 4. 使用方式

1. 打开一篇英文网页（例如 arXiv 的 HTML 版：`https://arxiv.org/html/...`，或 `https://ar5iv.org/abs/...`）。
2. 鼠标悬停在词上，Yomitan 弹出释义。
3. 点弹窗里的 **+**（Add to Anki）。卡片进入 `PaperToTalk::Vocab`，标签 `yomitan web`。
4. 当天晚上或第二天在 Anki 里复习；看到 `Context` 里的原句，回忆词义和搭配。

## 5. 和 Zotero 的分工

- **Zotero**：PDF 精读、论文标注、带页码和文献来源的卡片。
- **Yomitan**：网页泛读、arXiv HTML、博客、文档；轻量、快速。
- 两者都进同一个 `PaperToTalk::Vocab` 牌组，用标签区分：`zotero` / `yomitan`。

## 6. 常见问题

**Q: 点 + 没反应？**
先确认 Anki 正在运行，浏览器能打开 `http://127.0.0.1:8765`。如果页面显示 AnkiConnect 的版本信息，说明服务正常；否则重装/重启 AnkiConnect。

**Q: 卡片没有原句？**
Yomitan 只能抓取网页上的句子。PDF 内置阅读器通常抓不到，改用 arXiv HTML 或 Zotero。

**Q: 释义太长？**
Yomitan 设置 → Anki → 可以只映射第一个义项（例如 `{glossary-first}`，具体 marker 以你安装的版本为准），或在 Anki 里手动删减。

**Q: 同一个词重复添加？**
AnkiConnect 默认按首字段判重；我们的脚本也设置了 `allowDuplicate: false`。如果仍想保留不同语境，可以在 Anki 里把 `Word` 改成 `word · context` 再添加。
