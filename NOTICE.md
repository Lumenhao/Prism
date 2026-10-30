# NOTICE

Prism 包含原创脚本、原创说明与受第三方启发的训练材料。以下归属仅用于说明来源，不代表原作者为本项目背书。

## 方法论与模板来源

- **byoungd/up** — <https://github.com/byoungd/up>
  - 英语学习方法、诊断模板与证据卡的结构参考了该项目。
  - 原项目文本与翻译：© byoungd and contributors，**CC BY-NC 4.0**；代码：MIT。
  - 本仓库**不复制**原书正文，只在 README 与训练计划中概括方法并链接上游。若你在本地保留了提取版 `byoungd-up/`，那是独立目录，不随本仓库分发。

## 句型分类参考

- **Academic Phrasebank** — University of Manchester，<https://www.phrasebank.manchester.ac.uk/>
  - `writing/phrasebank/phrasebank_seed.csv` 的**功能分类**参考其公开框架；所有英文例句为本项目自写，用于二维材料/石墨烯器件语境。
  - 本项目不再分发 Phrasebank 原文；如需引用原句，请遵守其使用条款。

## 工具与软件

本项目调用或指导安装以下开源/免费工具，它们各自遵循自己的许可证：

| 工具 | 许可证/来源 |
|---|---|
| Anki | AGPL-3.0，<https://apps.ankiweb.net/> |
| AnkiConnect | AGPL-3.0，<https://github.com/FooSoft/anki-connect>（由 Anki 插件分发） |
| Zotero | AGPL-3.0，<https://www.zotero.org/> |
| Zotero PDF Translate | AGPL-3.0，<https://github.com/windingwind/zotero-pdf-translate> |
| ECDICT | MIT，<https://github.com/skywind3000/ECDICT>（本机英汉词典，由 `scripts/get_dict.py` 下载并建索引） |
| Yomitan | GPL-3.0，<https://github.com/yomidevs/yomitan> |
| LTeX+ | MIT，<https://github.com/ltex-plus/ltex-ls-plus> |
| Vale | MIT，<https://github.com/vale-cli/vale> |
| Kokoro | Apache-2.0，<https://github.com/hexgrad/kokoro> |
| faster-whisper | MIT，<https://github.com/SYSTRAN/faster-whisper> |
| Praat | GPL-3.0，<https://www.praat.org/> |
| mpvacious | GPL-3.0，<https://github.com/Ajatt-Tools/mpvacious> |
| mpv | GPL-2.0+，<https://mpv.io/> |
| Buzz | MIT，<https://github.com/chidiwilliams/buzz> |
| espeak-ng | GPL-3.0，<https://github.com/espeak-ng/espeak-ng> |
| FFmpeg | LGPL/GPL，<https://ffmpeg.org/> |
| YouGlish | 商业网站，<https://youglish.com/>，仅链接，不抓取 |

具体版本与条款以各项目页面为准。

`extension/` 是本项目自写的极简划词扩展（MIT，随本仓库同许可），不复制任何第三方扩展的代码；它只在运行时读取你主动选中的文字，并把它发给本机的 Prism。

## 内容与数据

- 示例稿 `speaking/samples/sample_talk.md` 是对 Novoselov et al., *Electric Field Effect in Atomically Thin Carbon Films*, Science **306**, 666–669 (2004), DOI [10.1126/science.1102896](https://doi.org/10.1126/science.1102896) 的**口语化复述**，其中的数值来自该论文正文与图注；正式使用前请回到原文核对。论文文本与图片版权归 AAAS 所有，本仓库不复制原文或插图。
- 学术报告的音频、截图、字幕归原报告人/出版方所有；本项目只提供制卡方法，不附带任何报告素材。
- 用户生成的 `data/`、`reports/`、录音、Zotero 导出与 Anki 卡片属于用户本地数据，不在本仓库内分发。

## 商标

Anki、Zotero、Praat、Kokoro、Whisper、YouTube 等名称与标识归各自权利人所有。本项目与上述组织无隶属关系。
