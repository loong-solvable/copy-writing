# Style Mimic

一个面向 Claude Code / Codex 类 skill 系统的写作风格学习工具，通过积累你的写作样本，逐步学习并模仿你的写作风格。

## 它解决什么问题

AI 生成的文本有明显的"AI 味"，即使用了去 AI 味的工具，输出的文字也只是"不像 AI 写的"，而不是"像你写的"。

Style Mimic 的目标不同：**让 AI 的输出读起来像你本人写的。**

它通过持续积累你的真实写作样本，构建你的个人风格画像，让 AI 在每次输出时都参考你的真实作品和风格特征。用得越久，模仿得越准。

## 公开版状态

这个仓库是已经初始化过的干净版本：不包含任何个人写作样本、风格画像或 changelog。安装后第一次使用时，skill 会在本地生成属于你的 `samples/`、`profiles/` 和 `changelog.md` 数据。

这些个人数据默认不会被提交到 git，适合直接分享、二次修改或作为自己的写作风格库起点。

## 核心设计理念

### 示例优先，画像辅助

研究一致表明，few-shot 示例比规则描述更能捕捉写作风格。因为示例中包含大量"隐性知识"——那些你自己都说不清但确实在用的写作习惯。

所以 Style Mimic 的主角始终是你的**原文样本**，风格画像只是辅助参考。

### 概率性描述，拒绝绝对化

人的写作风格有自然的随机变化。风格画像中不会出现"绝不""必须""禁止"这样的绝对措辞，只用"倾向于""经常""偶尔""很少"等概率性描述。

避免 AI 死板地遵守每一条规则，产生另一种机器感。

### 越用越准的迭代机制

风格画像不是一次生成就固定的。每次新增样本都会触发增量更新，每积累 10 篇触发全量审视，用户随时可以手动修正。三层更新机制确保画像持续逼近你的真实风格。

## 六种使用模式

### 1. 投喂样本（learn）

把你写的文章丢进来，skill 存入样本库并分析风格特征。

```
/style-mimic learn

# 然后粘贴你的文章
```

### 2. 对照改写 — 整篇（write）

AI 先按你的风格写一篇，你拿走用自己的笔法修改，改完贴回来。AI 会对比两个版本，分析你改了什么、怎么改的，从 diff 中学习你的风格偏好。

```
/style-mimic write 写一篇关于远程办公效率的文章
```

这个模式的学习效果比直接投喂更好，因为 diff 能精确捕捉"你会把 AI 的什么表达换成什么"。

### 3. 对照改写 — 逐段（write-part）

和整篇模式类似，但一段一段来。AI 写一段你改一段，AI 实时学习，写到后面会越来越接近你的风格，你需要改的地方也越来越少。

```
/style-mimic write-part 聊聊我对 AI 编程工具的看法
```

### 4. 风格改写（apply）

积累了足够样本后（至少 3 篇），可以用你的风格改写任意文本。

```
/style-mimic apply [粘贴需要改写的文本]
```

### 5. 样本管理（manage）

查看、浏览或删除已经积累的样本。

```
/style-mimic manage list
/style-mimic manage view 001
/style-mimic manage delete 001
```

### 6. 查看状态（status）

看看当前有多少样本、画像是第几版、各项特征的置信度。

```
/style-mimic status
```

## 用 wx-cli 补微信样本

如果你平时很多表达都在微信里，`wx-cli` 很适合拿来给 `style-mimic` 补真实语料，尤其是私聊和群聊里你自己发出去的文本。

这个仓库现在带了一个导入脚本：

```bash
python3 scripts/import_wx_cli_json.py <wx-json-file>
```

推荐工作流：

```bash
# 1. 用 wx-cli 导出聊天 JSON
wx history "某个聊天" --json > /tmp/wx-history.json

# 2. 导入到 style-mimic 的 samples/
cd ~/.agents/skills/style-mimic
python3 scripts/import_wx_cli_json.py /tmp/wx-history.json --topic 微信聊天
```

也可以直接吃 `export` 的 JSON：

```bash
wx export "某个聊天" --format json -o /tmp/wx-export.json
cd ~/.agents/skills/style-mimic
python3 scripts/import_wx_cli_json.py /tmp/wx-export.json
```

导入脚本会自动：

- 只保留你自己发出的 `文本` 消息
- 丢掉对方发言、图片、语音、系统消息等噪音
- 按时间正序拼接内容
- 自动分配下一个样本编号，写入 `samples/{编号}_direct.md`
- 追加 `source_tool`、`source_kind`、`source_file`、`message_count` 元数据，方便追溯来源

这一步很重要：不要把整段聊天原样塞进样本库。`style-mimic` 学的是你的表达习惯，不是整个群的混合语气。先筛干净，再入库，效果会稳很多。

## 风格画像是怎么运作的

### 三层更新机制

**第一层：增量补丁（每次新增样本）**

每加一篇样本，skill 会和现有画像对比：发现新特征就添加（低置信度），印证已有特征就升级置信度，发现矛盾就标注分歧（不急着改）。

**第二层：全量审视（每 10 篇样本触发一次）**

读取画像和最近 20 篇样本，全面重新评估。处理积累的分歧、清理长期未被印证的低置信条目、重写整体印象。

**第三层：用户修正（随时）**

你可以直接告诉 skill "我其实也会用这个词"或"这个判断不对"。用户修正是最高权重，不会被自动更新覆盖。

### 置信度体系

- **低**：仅 1 篇样本支持
- **中**：2-3 篇样本支持，或 1 次对照改写 diff 支持
- **高**：4 篇以上样本支持，或 2 次以上对照 diff，或用户确认

对照改写的 diff 信号权重更高：1 次 diff = 2 篇直接投喂的证据。

### 长期可持续性

随着样本增多，context window 装不下所有样本。skill 会自动调整策略：

| 阶段 | 样本数 | 策略 |
|------|--------|------|
| 冷启动 | 1-5 | 全部读取 |
| 成长期 | 6-20 | 画像 + 3 篇 few-shot |
| 成熟期 | 21-50 | 画像为主 + 2 篇 few-shot |
| 稳定期 | 50+ | 画像为主 + 1-2 篇最新 |

前两周样本少，画像是辅助；两个月后样本读不完，画像就是主力。

## 安装

### 方法一：克隆到中央 skills 库（推荐）

```bash
git clone https://github.com/loong-solvable/style-mimic.git ~/.agents/skills/style-mimic
```

### 方法二：手动安装

1. 下载本仓库
2. 将整个 `style-mimic` 文件夹复制到你的 skills 目录（通常是 `~/.agents/skills/` 或 `~/.claude/skills/`）
3. 确保目录结构包含 `SKILL.md`、`profiles/`、`samples/`

如果 Claude Code / Codex 走的是 bridge 目录，只要它们链接到中央库即可正常使用。

## 文件结构

```
style-mimic/
├── SKILL.md              # Skill 主逻辑
├── README.md             # 本文件
├── LICENSE               # MIT License
├── profiles/
│   └── default.md        # 默认风格画像（自动生成）
├── samples/              # 写作样本（自动积累）
│   └── .gitkeep
└── changelog.md          # 画像变更记录（自动维护）
```

`profiles/` 和 `samples/` 目录下的内容是你的个人写作数据，建议不要提交到公开仓库。`.gitignore` 已配置忽略这些文件。

## 设计参考

本 skill 的设计参考了以下研究和实践：

- [Wikipedia: Signs of AI Writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) — AI 写作特征分类
- [Stylometry](https://en.wikipedia.org/wiki/Stylometry) — 计算文体学的特征维度
- [How To Make LLMs Write Stylishly](https://pub.towardsai.net/how-to-make-llms-write-stylishly-6691be12b970) — few-shot 与规则描述的效果对比
- [Rules vs Few-Shot](https://softwaredoug.com/blog/2025/09/05/rules-vs-few-shot.html) — 规则与示例的实验对比
- Ben Tossell 的 Claude 风格克隆 prompt 流程 — BEGIN/CONTINUE 多样本喂入法
- [CAT-LLM](https://github.com/TaoZhen1110/CAT-LLM) — 中文文章风格迁移框架

核心结论：**混合方案最优** — 用多篇示例让 LLM 获得隐性风格认知，用结构化画像做可调的显式参考。

## License

MIT
