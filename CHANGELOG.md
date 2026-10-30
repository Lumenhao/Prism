# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Planned

- macOS / Linux 的 shell 等价脚本；
- 可选的语音依赖 CI job。

## [0.4.0] - 2026-10-30

### Added

- **浏览器划词 → Anki**：`extension/` 是自带极简 MV3 扩展（约 30 秒装载），在任意网页选中英文即弹出音标、中文释义、考试标签与词形变化；点「存到 Anki」把词、原句、页面链接送进收件箱，在 **Vocab → 划词收件箱** 勾选后写成 `Prism::Vocab` 卡片。
- **本机英汉词典**：`scripts/get_dict.py` 下载 ECDICT（66 MB）并索引成 770,611 条的 SQLite（约 11 秒，101 MB），存放在 `E:\LumenSuite\models\ecdict`；`app/services/lexicon.py` 只读查询，毫秒级返回，之后完全离线。`setup_env.ps1` 会自动跑一次，失败也不影响安装。
- **离线补交**：Prism 没开时扩展把条目暂存在 `chrome.storage.local`，`chrome.alarms` 每分钟重试一次；角标显示待写卡数、排队数（`+N`）与离线（`!`）。
- 新接口：`GET /api/dict`、`POST /api/dict/install`、`GET/POST /api/clips`、`POST /api/clips/import`、`POST /api/clips/delete`。
- Vocab 页新增第 5 张统计卡与「划词收件箱」面板（勾选、写卡、删除、安装词典、进度条）；Overview 的 Next move 在有待写条目时多一项直达；命令面板新增 `Install local dictionary`。
- `tests/test_lexicon.py`：13 个用例覆盖归一化、查词（大小写 / 缺失 / 未装词典）、收件箱读写、损坏行容错、卡片字段映射与 AnkiConnect 调用序列；总数 38 → 51。
- `scripts/validate.py` 新增 `check_extension()`：扩展的 `host_permissions` 只能是本机 7317、权限只能是 storage/alarms、清单引用的文件必须存在。

### Changed

- 划词导入前先确认牌组与笔记类型：牌组缺失时自动 `createDeck`，笔记类型缺失时报「先在 Vocab 页点『初始化牌组』」——否则 AnkiConnect 的 `canAddNotes` 会把所有条目判成「重复」。
- `get_dict.py build()` 在索引比 csv 新时直接复用，重复运行不再每次重建。
- Vocab 副标题改为「Zotero 标注与浏览器划词 → Anki 复习」；README 中英两版新增「在浏览器里划词」章节，NOTICE / PRIVACY 补 ECDICT 与扩展的数据流向。
- 文档与主页：新增划词截图 `assets/screenshots/clip.png`，主页标题改成「六个工作区，外加一个浏览器扩展」并补一张划词卡，启动步骤加到 4 步，FAQ 补「扩展会不会把网页发出去」。
- 版本号统一到 0.4.0。

### Fixed

- `lexicon.lookup()` 用 `with conn` 只提交不关闭连接，改为 `contextlib.closing`。
- `scripts/shots.py` 现在也能拍扩展浮层：headless Edge 会把 Shadow DOM 里的卡片排好版却不合成进 `--screenshot`，所以布景页 `scripts/clip-preview.html` 调用真实的 `content.js`，再把标记与样式平铺回 light DOM 拍给文档用。

## [0.3.1] - 2026-10-30

### Added

- **README 中英双语**：`README.md`（英文默认）与 `README.zh-CN.md`（简体中文）互链，两版结构一致；`scripts/validate.py` 把中文版列入必需文件。
- **主题化窗口图标**：`scripts/make_icons.py` 按深浅两套配色重绘 `prism-dark.ico` / `prism-light.ico`，标题栏与任务栏图标随主题一起换。

### Changed

- 仓库描述只保留一句：`A local-first workbench for academic English. 学术英语工作台，一切尽在本机。`
- 项目主页不再叙述「系列的第几件作品」，只介绍 Prism 本身。
- 主页截图改为深浅成对（`assets/*.webp` 与 `*-light.webp`），页面主题与截图主题始终一致；主题对照区显式标注「深色 / 浅色」。
- 版本号统一到 0.3.1（`pyproject.toml`、FastAPI、Settings 页）。

### Fixed

- 浅色主题下原生标题栏仍是白色、图标仍是深色版：改为按进程 ID 认领自己的窗口（`Prism.bat` 的控制台窗口同名，会被误填色），并接管 pywebview 的 `update_title_bar_theme`、关闭 DWM backdrop，标题栏颜色真正跟随主题。
- 主页浅色模式下按钮文字、背景光晕与阴影仍沿用深色硬编码值；新增 `--on-accent` / `--accent-soft` / `--glow-*` / `--shadow` 等按主题取值的令牌。
- `scripts/shots.py` 深浅两轮写到同一文件名，浅色把深色覆盖；现在浅色输出带 `-light` 后缀。
- `webview.start()` 默认隐私模式导致主题选择跨启动丢失；改为持久化到 `E:\LumenSuite\data\webview`。
- CI 的 Linux job 解析 Zotero `prefs.js` 时把 Windows 反斜杠留在文件名里，`test_parses_escaped_windows_path` 失败；`parse_zotero_data_dir` 现在统一按 `/` 分隔。

## [0.3.0] - 2026-10-30

### Added

- **浅色主题**：顶栏一键切换、Settings → Appearance、`Ctrl+Shift+L` 与命令面板均可切换；选择写入 `localStorage`，启动前内联脚本先应用，避免闪白。
- **原生窗口外观**：标题栏颜色随主题变化（DWM caption / text / border），窗口图标改为 Prism，任务栏不再显示 Python 图标；Windows 进程 AppUserModelID 固定为 `Lumenhao.Prism`。
- **一键启动**：`Prism.bat` 在缺少 `.venv` 时自动调用 `setup_env.ps1` 完成安装后直接开窗；`setup_env.ps1` 在没有 E 盘时回退到 `%LOCALAPPDATA%\LumenSuite`，并支持 `LUMEN_SUITE` 覆盖。
- **项目主页**：`site/` 静态站（痛点、工作区导览、上手路径、FAQ）与 GitHub Pages 工作流。
- **配置分层**：`config.json` 保持可移植默认值，机器相关路径写入未跟踪的 `config.local.json`。

### Changed

- Anki 牌组统一为 `Prism::Vocab` / `Prism::Phrases` / `Prism::Listening`；初始化牌组时自动把旧 `PaperToTalk::*` 牌组的卡片迁入并删除空壳。
- README 重写为面向使用者的上手文档：痛点、一键开始、每个工作区的用法、FAQ。
- 窗口初始尺寸按屏幕逻辑分辨率计算并居中，小屏不再超出可用区域。

### Fixed

- 全局图标样式选择器误伤环图与图表，导致 Overview 环图和 Speak 波形/音高图显示不全。
- Library 左栏在较矮窗口下被裁切；长标题、摘要、路径与提示条溢出；Analyze 差异表按字母断行。
- 脚本 YAML front matter 被当成朗读与对齐内容，导致 WER 虚高（同一录音 16.2% → **9.8%**，内容词 WER 25.6% → **15.7%**）。
- 首次启动时 `Prism.bat` 仅提示安装而未实际执行。

## [0.2.0] - 2026-10-30

### Added

- **Prism 工作台**：FastAPI 本地服务 + 原生 HTML/CSS/JS 单页界面，六个工作区（Overview / Library / Speak / Write / Vocab / Settings），`Prism.bat` 一键启动；Edge 应用窗口，失败时回退 pywebview。
- **Library**：只读读取 Zotero 快照（`_DB_LOCK` 原子替换），论文列表、摘要、附件、标注、打开 PDF / 定位 Zotero、一键生成讲述稿。
- **Speak**：Kokoro TTS 生成示范音频（af_heart，CPU）、YouGlish 语境链接、录音上传 → faster-whisper 转写 → Praat 波形/音高/停顿 → WER、内容词 WER、差异表、练习建议；报告与音频留存本地。
- **Write**：句型库检索、LTeX+ / Vale 检查入口、段落改写工作区。
- **Vocab**：AnkiConnect 状态、牌组初始化、Zotero 标注导出为 `Prism::*` 卡片、到期数提醒。
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

- **词汇线**：`anki_setup.py` 创建 `Prism::*` 牌组与 `AE Vocab` / `AE Phrase` / `AE Subs` 笔记类型，导入 40 条句型种子卡；`zotero_to_anki.py` 以只读快照导出 Zotero 标注与翻译；`remind.ps1` 提供到期提醒；`install_reminder.ps1` 一键注册/删除每日计划任务；Yomitan 配置说明。
- **写作线**：三层检查（Phrasebank / LTeX+ / Vale）；40 条功能化句型；4 周训练计划；段落实验室模板；6 条保守 Vale 规则与领域词表。
- **口语线**：`speak.py` 的 `tts` / `links` / `check`；术语读法表；YouGlish 清单生成；Whisper 对齐与 Praat 指标；独立 Praat 脚本；Buzz + Praat 流程；mpvacious 制卡说明；3 分钟示例稿。
- **工程**：`scripts/validate.py` 仓库自检；标准库 `unittest` 测试；GitHub Actions（Ubuntu + Windows，Python 3.12）；Dependabot；issue / PR 模板；README banner 与 1280×640 社交预览图。
- **文档**：品牌化 README、路线图、隐私说明、贡献指南、MIT + CC BY-NC 4.0 分离许可、第三方归属。

### Changed

- 牌组前缀从 `Academic English::*` 改为 `Prism::*`。未开始使用 Anki 的用户不受影响；已有旧牌组的用户改 `config.json` 后需手动迁移卡片。
- `config.json` 的 Zotero 路径改为 `~/Zotero/zotero.sqlite`，支持 `~` 与环境变量。

### Known limitations

- Anki / Kokoro / faster-whisper / Praat / mpvacious / Buzz 尚未在本机端到端验证；
- 语音依赖仅支持 Python 3.12 及以下的预编译轮子；
- 提醒与安装脚本仅支持 Windows。
