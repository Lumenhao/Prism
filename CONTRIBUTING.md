# 贡献指南

感谢你愿意改进 Prism。这个项目的目标不是“收集更多工具”，而是让每条学习线**可执行、可测量、可复盘**。提交前请先确认改动服务于这个目标。

## 开发环境

```powershell
git clone https://github.com/Lumenhao/Prism.git
cd Prism
python -m pip install -r requirements-dev.txt
python scripts/validate.py
python -m unittest discover -s tests -v
```

- 运行时只依赖标准库（`vocab/`、`scripts/`、`tests/`）；
- `speaking/speak.py` 的 `tts` / `check` 需要 `requirements.txt` 里的语音依赖，CI 不安装它们；
- 推荐 Python 3.12。

## 改动前

1. 先开 issue 描述真实任务与预期行为；小的文档修正可以直接提 PR。
2. 改脚本时，同步更新对应模块 README 的命令示例。
3. 新增第三方工具时，在 `NOTICE.md` 补一行来源与许可证。
4. 不提交任何个人数据：论文全文、Zotero 数据库或标注、录音、报告视频、Anki 集合、含他人信息的截图。

## 代码约定

- Python 只用标准库（`vocab/`、`scripts/`、`tests/`），避免为了一个小功能引入依赖。
- 面向用户的输出用中文；日志与异常信息保留可检索的英文关键词。
- 文件路径从 `config.json` 读取，并支持 `~` 与环境变量展开；不要在代码里写死用户名。
- 新增配置项时给出默认值，并更新 `config.json` 与 README。
- PowerShell 脚本需兼容 Windows PowerShell 5.1，避免仅 PowerShell 7 可用的语法。

## 测试

- 单元测试放在 `tests/`，使用 `unittest`，不依赖网络、Anki、Zotero 或音频文件。
- 需要外部程序的行为，用临时目录和伪造数据测试纯函数；端到端步骤写进 README，不放进 CI。
- 提交前至少运行：

```powershell
python scripts/validate.py
python -m unittest discover -s tests -v
ruff check .
```

## 文档约定

- 中文为主，英文术语首次出现时保留原文。
- 命令必须可复制；路径用相对路径或 `<repo>` 占位。
- 不承诺未验证的能力；没跑通的部分明确写“尚未端到端验证”。

## 许可证

- 代码贡献按 [MIT](LICENSE) 授权；
- 文档、训练材料、句型表的贡献按 [CC BY-NC 4.0](LICENSE-CONTENT.md) 授权；
- 提交即表示你有权按上述许可证分发该内容。

## 提交信息

用一句话说明“为什么改”，而不是“改了哪个文件”。例如：

```text
fix: close Zotero snapshot connection before fallback copy
docs: clarify that phrase cards are imported by anki_setup.py
```

## 行为准则

讨论对事不对人。涉及口音、母语、写作水平的反馈，描述可观察的行为与改进路径，不做人身评价。
