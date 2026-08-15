# 有声书生产工作流

一个平台无关的有声书后期生产命令包，围绕四个 Slash Command 组织工作：

- `/画本`：把原文拆成旁白、角色和特殊文本，并补充配音属性。
- `/审听`：比较原文、ASR 转写和音频质量，输出带时间码的问题清单。
- `/对轨`：把多个 MP3 与原文段落建立稳定对应关系，生成音频时间轴。
- `/后期`：根据文本和场景属性检索 BGM/音效资源，生成后期 cue 表。

## 设计原则

AI 负责语义理解、分类、检索和建议；确定性工具负责转写、时间戳、波形分析、切分和导出。四个命令通过稳定的 `segment_id` 串联，避免每一步重新猜测上下文。

本项目是工作流规范和命令模板，不绑定 Codex、Claude Code 或某个 Web 平台。可以把 `commands/` 下的文件转换成目标平台的 Slash Command，也可以由本地 CLI、n8n 或 Web Agent 调用。

## 项目结构

```text
有声书生产工作流/
├── commands/                 # 四个 Slash Command 模板
├── schemas/                  # 跨命令共享的 JSON 数据契约
├── examples/                 # 最小可运行示例数据
├── scripts/                  # 本地校验脚本
├── project.json              # 项目配置示例
└── README.md
```

## 快速开始

1. 复制 `project.json`，填写项目名称、章节和目录。
2. 准备原文，并运行 `/画本` 生成带 `segment_id` 的结构化稿件。
3. 将多个 MP3 和 ASR 结果放入项目目录，运行 `/审听` 检查内容和音质。
4. 运行 `/对轨` 生成文本到音频的对应表和时间轴。
5. 维护 `audio-assets.json` 资源索引，运行 `/后期` 生成 BGM/音效 cue 表。
6. 用 `python scripts/validate_project.py .` 检查结构和跨文件引用。

## 推荐的数据流

```text
原始文本
  └─ /画本
       └─ annotated script
            ├─ /审听 ← MP3 + ASR
            └─ /对轨 ← 多个 MP3
                    └─ timeline
                         └─ /后期 ← 音频资源索引
                              └─ BGM / SFX cue sheet
```

## 四个命令的边界

### `/画本`

只负责文本理解和配音标注，不假装知道未提供的音频事实。角色归属不确定时必须输出 `review_required`，不能静默猜测。

### `/审听`

至少需要原文、ASR 文本和时间戳。只有文本时可以做初步 diff，但必须明确标记为“未完成音频审听”。问题要包含原文、听到的文本、时间码、严重程度和置信度。

### `/对轨`

优先使用 ASR word/segment timestamps 或 forced alignment。纯字符串相似度只能作为候选匹配，不能把低置信度结果直接视为最终对轨。

### `/后期`

只能推荐资源库中存在且授权状态明确的素材。对于情绪、场景和 BGM 强度的匹配，要给出理由；对话密集段要设置 ducking 建议。

## 典型工具边界

可由目标平台接入以下类型的工具：

- `ffmpeg`：格式转换、响度分析、切分、混音和导出。
- ASR 引擎：生成带 segment/word timestamps 的转写。
- forced alignment：在已有原文时提升文本—音频时间定位精度。
- SQLite/JSON 索引：检索本地 BGM、音效和授权信息。

工具名称只是实现建议，命令模板本身不依赖某个供应商。

## 校验

```powershell
python scripts/validate_project.py .
```

校验脚本只检查结构、JSON 格式、必需字段和 `segment_id` 引用，不会读取或修改音频文件。

## 当前版本边界

当前版本提供工作流契约、命令模板和示例数据；尚未绑定具体 ASR、forced alignment 或 DAW 导出适配器。这样可以先确认项目的生产规则，再根据实际音频样本选择工具链。
