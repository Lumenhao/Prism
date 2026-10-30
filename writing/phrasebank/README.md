# Phrasebank 数据说明

## 文件

- `phrasebank_seed.csv`：40 条种子句型，按 `section` 分为 Introduction / Methods / Results / Discussion / Speaking。
- `training_plan.md`：4 周训练方案。
- `paragraph_lab.md`：每段写作的记录模板。

## CSV 字段

| 字段 | 含义 |
|---|---|
| `section` | 论文小节或口语场景 |
| `function` | 这句话的论证功能（英文短标签） |
| `chinese_cue` | 卡片正面的中文意图 |
| `template` | 去掉具体内容后的槽位化模板 |
| `example` | 本领域例句（二维材料/石墨烯器件） |
| `source` | 来源：`Phrasebank (adapted)` / `Own` |

## 如何添加自己的句型

1. 在范本论文里找到一句“完成某个论证动作”的句子。
2. 保留原句和来源，填入 `phrasebank_seed.csv`，或直接加到 Anki 的 `AE Phrase` 笔记类型。
3. `template` 必须槽位化：把具体材料、数值、条件换成 `[X]`、`[value]`、`[condition]`。
4. `chinese_cue` 写“你要表达什么意图”，不要写“翻译原句”。
5. 重新运行 `python vocab/anki_setup.py`，新行会自动导入（重复项会跳过）。

## 注意

- 种子句型的例句是**示例**，不是事实；写进论文前必须用自己的数据和文献核对。
- `Phrasebank (adapted)` 表示句型结构参考了曼彻斯特大学 Academic Phrasebank，例句为本项目自写。
- 这些句型是“骨架”，不是“高级词汇”。段落是否成立，取决于论证和证据，不取决于句型数量。
