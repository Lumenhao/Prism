# 隐私说明

Prism 的设计原则是**本地优先**：默认不要求账号，不上传论文、标注、录音或卡片。但“本地优先”不等于“完全离线”，下面把数据流向写清楚。

## 数据在哪里

| 数据 | 默认位置 | 是否进仓库 |
|---|---|---|
| Zotero 数据库 | `~/Zotero/zotero.sqlite`（只读快照） | 否 |
| 导出状态 | `data/zotero_export_state.json` | 否（`.gitignore`） |
| Anki 卡片与复习记录 | Anki 自己的配置目录 | 否 |
| 句型采集与段落实验 | `writing/log/` | 默认在仓库内；提交前自行脱敏 |
| 录音 | `speaking/samples/*.wav` 等 | 否（`.gitignore`） |
| 口语报告与 TextGrid | `reports/` | 否（`.gitignore`） |
| 浏览器划词收件箱 | `data/clips.jsonl`（词、原句、URL、释义） | 否（`.gitignore`） |
| 本机词典 | `E:\LumenSuite\models\ecdict\`（ECDICT csv + sqlite） | 否 |
| 配置 | `config.json` | 是；不要写入密钥或私人路径 |

`zotero_to_anki.py` 只读取数据库的临时快照，脚本结束即删除；它不会修改 Zotero 数据。

## 什么会离开本机

以下动作会发起网络请求，是否使用由你决定：

- **首次运行 Kokoro / faster-whisper**：从 Hugging Face 下载模型权重。之后可离线使用。
- **安装本机词典**：从 GitHub 上的 ECDICT 仓库下载一次 `ecdict.csv`（约 66 MB）。之后查词完全离线，你查询的词不会被发往任何地方。
- **划词扩展**：只与 `http://127.0.0.1:7317` 通信（这是它唯一的 `host_permissions`）。Prism 没开时，条目暂存在浏览器自己的 `chrome.storage.local` 里，不经过任何服务器。
- **Yomitan 词典与音频**：取决于你安装的词典和音频源；部分词典/发音源会在线查询。
- **YouGlish**：`speak.py links` 只生成链接，不抓取页面；你点击链接时，查询词会发给 youglish.com。
- **Anki 同步**：只有你在 Anki 里配置并开启 AnkiWeb 同步时才上传集合。
- **Zotero 同步**：由 Zotero 自身配置决定，本项目不触发。
- **Buzz**：默认使用本地模型；如果你手动选择在线服务，音频会上传。
- **GitHub**：你 push 的内容会上传；`.gitignore` 已排除本地数据，但**无法阻止你手动 `git add -f`**。

Vale、LTeX+、Praat、mpvacious、FFmpeg 在本项目默认配置下均为本地运行。

## 不要提交的内容

- 论文全文、出版社 PDF、未公开稿件；
- Zotero 数据库、标注导出、含他人批注的截图；
- 组会/报告录音、含他人画面或声音的视频；
- 客户、同事、学生、患者、合同、未公开项目的信息；
- API key、token、带用户名的绝对路径。

提交 PR 前跑一次：

```powershell
git status
git diff --cached
```

## 共享电脑

- `data/` 与 `reports/` 用完可删；
- Anki 集合若含敏感例句，退出前确认是否需要锁定屏幕；
- 录音文件不要留在公共目录。

## 删除本地数据

```powershell
Remove-Item -Recurse -Force data\*
Remove-Item -Recurse -Force reports\*
Remove-Item speaking\samples\*.wav, speaking\samples\*.m4a -ErrorAction SilentlyContinue
```

删除 `data/zotero_export_state.json` 会让下次导出失去“已导出去重”记录，可能产生重复卡；一般只在确定要重建时删除。

删除 `data/clips.jsonl` 会清空划词收件箱；已经写进 Anki 的卡片要在 Anki 里删。词典本体在 `E:\LumenSuite\models\ecdict\`，删掉即彻底移除。

## 儿童与第三方

本项目面向成年研究者。不要用他人的录音、论文或数据做练习素材，除非你已获得许可。
