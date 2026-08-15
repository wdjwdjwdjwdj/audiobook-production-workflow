# 有声书生产工作流

一个平台无关的有声书生产工作流 MVP。当前已提供可运行的 Streamlit 工作台，主链路是：

```text
上传原文和音频 → /画本 → ASR → /审听 → 对轨结果和审听报告
```

同时保留四个 Slash Command 作为可迁移的工作流规范：

- `/画本`：把原文拆成旁白、角色和特殊文本，并补充配音属性。
- `/审听`：比较原文、ASR 转写和音频质量，输出带时间码的问题清单。
- `/对轨`：把多个 MP3 与原文段落建立稳定对应关系，生成音频时间轴。
- `/后期`：根据文本和场景属性检索 BGM/音效资源，生成后期 cue 表。

## 设计原则

AI 负责语义理解、分类、检索和建议；确定性工具负责转写、时间戳、波形分析、切分和导出。四个命令通过稳定的 `segment_id` 串联，避免每一步重新猜测上下文。

本项目不绑定 Codex、Claude Code 或某个 LLM 平台。`commands/` 下的文件可以转换成目标平台的 Slash Command；`audiobook/` 则提供本地 Python 执行引擎。

## 项目结构

```text
有声书生产工作流/
├── commands/                 # 四个 Slash Command 模板
├── audiobook/                # MVP 执行引擎和外部工具适配器
├── schemas/                  # 跨命令共享的 JSON 数据契约
├── examples/                 # 最小可运行示例数据
├── scripts/                  # 本地校验脚本
├── tests/                    # 单元测试
├── app.py                    # Streamlit Web 入口
├── Dockerfile                # CPU 部署镜像
├── project.json              # 项目配置示例
└── README.md
```

## 快速开始

### 本地运行

需要 Python 3.11、完整 FFmpeg 和可用的 `pip`：

```powershell
py -m pip install -e ".[dev]"
Copy-Item .env.example .env
py -m streamlit run app.py
```

首次运行会下载 faster-whisper 模型。没有配置 `LLM_API_KEY` 时，`/画本` 会使用规则降级模式；配置 OpenAI-compatible endpoint 后会进行 AI 角色和情绪标注。

### Docker 运行

```powershell
docker build -t audiobook-production-workflow .
docker run --rm -p 8501:8501 --env-file .env audiobook-production-workflow
```

### 测试和校验

```powershell
py -m pytest -q
py scripts/validate_project.py .
```

### 工作台操作

1. 上传 TXT/Markdown 原文。
2. 上传一段一个 MP3，或上传一个章节长音频。
3. 选择“自动判断”或明确指定音频组织方式。
4. 点击“运行画本与审听”。
5. 在“画本结果”“审听结果”“对轨结果”中复核。
6. 下载 JSON、CSV、Markdown 或完整 ZIP 项目包。

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

MVP 已接入以下类型的工具：

- `ffmpeg`：格式转换、响度分析、切分、混音和导出。
- `faster-whisper`：生成带 segment/word timestamps 的中文转写。
- OpenAI-compatible LLM：生成 AI 画本；无 Key 时使用规则降级模式。
- 字符级顺序匹配：实现长音频的句子级对轨。

Qwen3 ForcedAligner、Charsiu、WhisperX 和本地资源库检索暂时保留为后续适配点。

工具名称只是实现建议，命令模板本身不依赖某个供应商。

## 校验

```powershell
python scripts/validate_project.py .
```

校验脚本只检查结构、JSON 格式、必需字段和 `segment_id` 引用，不会读取或修改音频文件。

## 当前版本边界

当前版本已完成画本、ASR、审听、句子级对轨和导出 MVP；尚未实现 BGM 自动检索、复杂 DAW 时间轴、账号系统、任务队列和长期音频存储。

上传文件只写入当前 Streamlit 会话的临时目录。请不要把真实 MP3、原文或 `.env` 提交到公开仓库。
