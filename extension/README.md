# Prism 划词扩展

在任意网页选中英文 → 弹出本机 ECDICT 释义 → 一键把「词 + 原句 + 链接」送进 Prism 的划词收件箱 → 由 Prism 写成 Anki 卡片。
浏览器只和 `127.0.0.1:7317` 通信，页面内容不会离开这台机器。

## 装（约 30 秒）

1. 先确认词典已装：打开 Prism → **Vocab** → 若右上角写着「词典未装」，点 **安装本地词典（约 66 MB）**，等进度条走完。
2. 地址栏打开 `chrome://extensions`（Edge 用 `edge://extensions`），右上角打开 **开发者模式**。
3. 点 **加载已解压的扩展程序**，选中这个文件夹：`E:\LumenSuite\Prism\extension`。
4. 把扩展图标钉到工具栏（拼图图标 → Prism 划词 → 图钉）。

装好后在任何英文页面划一下鼠标，释义卡片就出现了。

## 用

| 操作 | 结果 |
| --- | --- |
| 选中一个词或短语 | 弹出音标、释义、考试标签、词形变化 |
| 卡片里的 **存到 Anki** | 写入 Prism 收件箱（`data/clips.jsonl`），带原句和来源链接 |
| Prism 没开着时保存 | 先存在扩展自己的队列里，Prism 一起床（最长 1 分钟）自动补交 |
| 点扩展图标 | 看在线状态、待写卡数、排队数；可关掉划词弹窗；可手动补交 |
| 回到 Prism → Vocab | 勾选条目 → **勾选的写入 Anki**，卡片进 `Prism::Vocab` |

图标上的角标数字 = 收件箱里还没写卡的条数；`+N` 表示 Prism 不在、扩展替你压了 N 条；`!` 表示 Prism 没开且队列为空。

## 只读了什么

- 你**主动选中**的那段文字，以及它所在的那一句（最多 600 字符）和页面标题、URL。
- 不会扫描整页，不读取输入框、密码、Cookie，不发任何第三方请求。
- `host_permissions` 只写了 `http://127.0.0.1:7317/*`，也就是本机 Prism 自己。

## 出问题

| 现象 | 处理 |
| --- | --- |
| 卡片写着「Prism 没开」 | 双击 `E:\LumenSuite\Prism\Prism.bat`，回来再划一次 |
| 卡片写着「本机词典还没装」 | Prism → Vocab → 安装本地词典 |
| 划词没反应 | 点扩展图标，确认「在网页里划词时显示释义」勾上了；改完后刷新那个网页 |
| 装完扩展才开的 Prism | 正常，扩展每秒都能连；不行就在 `chrome://extensions` 点一次重新加载 |
| 别的浏览器 | Chrome / Edge / Brave / Vivaldi 都能用同一个文件夹加载；Firefox 需把 `manifest.json` 的 `background.service_worker` 改成 `"scripts": ["background.js"]` |

## 文件

```
manifest.json     MV3 清单：权限只有 storage、alarms 和本机 7317
background.js     唯一发网络请求的地方；离线队列与自动补交
content.js        划词检测、释义卡片（Shadow DOM，不污染页面样式）
popup.html/js/css 工具栏弹窗：状态、开关、手动补交
prism-*.png       图标
```
