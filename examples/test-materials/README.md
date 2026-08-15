# MVP 测试素材

这套素材用于快速验证“画本 → 审听 → 对轨 → 导出”。

## 文件

- `chapter-01.txt`：与示例音频内容匹配，预期不会出现文本差异。
- `chapter-01-mismatch.txt`：将“几乎”改成“完全”，预期检测到 `replacement`。
- `roles.txt`：可复制到页面的已知角色说明。
- `scene-notes.txt`：可复制到页面的场景说明。
- `audio/qwen-asr-zh.wav`：公开中文语音示例。

## 测试步骤

1. 启动应用：`py -m streamlit run app.py`。
2. 上传 `chapter-01.txt`。
3. 上传 `audio/qwen-asr-zh.wav`。
4. 音频组织方式选择“一章长音频”。
5. 点击“运行画本与审听”。
6. 下载 `review.json` 和 Markdown 报告。
7. 再用 `chapter-01-mismatch.txt` 重复一次，观察错读/替换问题。

## 预期结果

匹配原文应能得到接近：

```text
甚至出现交易几乎停滞的情况。
```

故意改错的原文应出现：

```text
issue_type: replacement
```

音频来源：Qwen3-ASR 官方 GitHub 示例中使用的中文 forced-alignment 样例；原文和下载地址见 [官方示例](https://github.com/QwenLM/Qwen3-ASR/blob/main/examples/example_qwen3_forced_aligner.py)。

## 注意

- 该音频是 WAV，不是 MP3；MVP 同时支持 WAV 和 MP3，便于先验证流程。
- 第一次运行会下载 ASR 模型，CPU 可能需要一些时间。
- 如果本机 FFmpeg 是精简版，音频质量检查可能报告工具缺失；Dockerfile 中安装的是完整 FFmpeg。
