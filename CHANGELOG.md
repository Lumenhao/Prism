# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Planned

- macOS / Linux 的 shell 等价脚本；
- 可选的语音依赖 CI job。

## [0.2.0] - 2026-10-30

### Added

- **Prism 工作台**：FastAPI 本地服务 + 原生 HTML/CSS/JS 单页界面，六个工作区（Overview / Library / Speak / Write / Vocab / Settings），`Prism.bat` 一键启动；Edge 应用窗口，失败时回退 pywebview。
- **Library**：只读读取 Zotero 快照（`_DB_LOCK` 原子替换），论文列表、摘要、附件、标注、打开 PDF / 定位 Zotero、一键生成讲述稿。
- **Speak**：Kokoro TTS 生成示范音频（af_heart，CPU）、YouGlish 语境链接、录音上传 → faster-whisper 转写 → Praat 波形/音高/停顿 → WER、内容词 WER、差异表、练习建议；报告与音频留存本地。
- **Write**：句型库检索、LTeX+ / Vale 检查入口、段落改写工作区。
- **Vocab**：AnkiConnect 状态、牌组初始化、Zotero 标注导出为 `PaperToTalk::*` 卡片、到期数提醒。
- **E 盘套件**：`E:\LumenSuite\{Prism,tools,models,cache,data}`；`HF_HOME` / `HF_ENDPOINT` / `UV_CACHE_DIR` / `UV_PYTHON_INSTALL_DIR` 等全部指向 E 盘；HuggingFace 走 `hf-mirror.com` 并禁用 Xet。
- **本地模型**：Kokoro 权重、faster-whisper `base.en`（145 MB）落在 `E:\LumenSuite\models`，离线加载。

### Changed

- 前端路由支持深链接（如 `#/speak/analyze` 直接打开复盘）；异步页面渲染与图标尺寸修复。
- 语音分析在转写失败时不再给出虚假 WER，改为显式提示并保留声学指标。
- `av` 固定 16.0.1：PyAV 19 移除了 `metadata_errors`，与 faster-whisper 1.2 不兼容。
- `setup_env.ps1` 从 E 盘安装 Python / 依赖与缓存。

### Verified

- Zotero 341 篇文献读取，目标论文 Novoselov 2004 可打开并生成讲述稿；
- Kokoro TTS 生成 177.75 s 音频；faster-whisper + Praat 复盘产出 WER 16.2%、内容词 WER 25.6%、波形 320 点、音高 260 点；
- AnkiConnect 连接、三套牌组与 40 张句型卡导入；38 项单元测试与 `scripts/validate.py` 通过。

## [0.1.0] - 2026-10-30

### Added

- **词汇线**：`anki_setup.py` 创建 `PaperToTalk::*` 牌组与 `AE Vocab` / `AE Phrase` / `AE Subs` 笔记类型，导入 40 条句型种子卡；`zotero_to_anki.py` 以只读快照导出 Zotero 标注与翻译；`remind.ps1` 提供到期提醒；`install_reminder.ps1` 一键注册/删除每日计划任务；Yomitan 配置说明。
- **写作线**：三层检查（Phrasebank / LTeX+ / Vale）；40 条功能化句型；4 周训练计划；段落实验室模板；6 条保守 Vale 规则与领域词表。
- **口语线**：`speak.py` 的 `tts` / `links` / `check`；术语读法表；YouGlish 清单生成；Whisper 对齐与 Praat 指标；独立 Praat 脚本；Buzz + Praat 流程；mpvacious 制卡说明；3 分钟示例稿。
- **工程**：`scripts/validate.py` 仓库自检；标准库 `unittest` 测试；GitHub Actions（Ubuntu + Windows，Python 3.12）；Dependabot；issue / PR 模板；README banner 与 1280×640 社交预览图。
- **文档**：品牌化 README、路线图、隐私说明、贡献指南、MIT + CC BY-NC 4.0 分离许可、第三方归属。

### Changed

- 牌组前缀从 `Academic English::*` 改为 `PaperToTalk::*`。未开始使用 Anki 的用户不受影响；已有旧牌组的用户改 `config.json` 后需手动迁移卡片。
- `config.json` 的 Zotero 路径改为 `~/Zotero/zotero.sqlite`，支持 `~` 与环境变量。

### Known limitations

- Anki / Kokoro / faster-whisper / Praat / mpvacious / Buzz 尚未在本机端到端验证；
- 语音依赖仅支持 Python 3.12 及以下的预编译轮子；
- 提醒与安装脚本仅支持 Windows。
