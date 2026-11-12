# 算邻坊 AI 能力（Dify 插件）

为 Dify 工作流与 Agent 提供语音识别、语音合成、图片文字识别与类型化智能决策，
基于[算邻坊](https://suanlinfang.cn) API。一个提供者、十一个工具，
需要您自己的算邻坊 API Key。

源码仓库：<https://github.com/wujian123/suanlinfang-dify-plugin>

## 连接要求

- 算邻坊账户与 API Key（在
  [suanlinfang.cn](https://suanlinfang.cn/consume-web/api-keys.html) 创建；
  新注册账户赠送 ¥10 体验金）。
- Dify 插件运行时可访问 `https://suanlinfang.cn`（全部 API 调用）与
  运行时签发的 `*.aliyuncs.com` 对象存储地址（大文件上传与结果下载）。

## 功能

- **语音识别**：短音频（≤3 分钟 / 20MB）同步返回；长音频任务最长 2 小时 /
  500MB，按 180 秒自动切段转写并拼接全文。普通话/英语/22 种中文方言自动检测，
  热词纠错专有名词。
- **语音合成**：多音色；短文本（约 1000 汉字）同步返回；长文本任务最长 20 万字。
- **图片文字识别**：单图（png/jpg/webp/bmp）标准/精准双档；精准档支持自定义
  识别指令（如「只提取表格金额列」）；PDF 文档任务最长 500 页。
- **类型化智能决策**：1-32 题（单选 / 是否 / 有序等级）对业务状态作结构化判断，
  返回校准概率，不生成文本、无对话记忆。

## 配置

1. 在 [suanlinfang.cn](https://suanlinfang.cn) 注册（新账户赠送 ¥10 体验金），
   到 [API Keys 页面](https://suanlinfang.cn/consume-web/api-keys.html) 创建 Key。
2. 在 Dify 安装本插件，把 Key（`nk-` 开头）粘贴到插件凭据中。保存时用只读
   请求（`GET /v1/tts/voices`）校验，不计费。

## 用法

每个工具都返回 JSON 产物，便于工作流节点串联。

- 同步工具（`transcribe_audio`、`synthesize_speech`、`recognize_image`、
  `list_tts_voices`、`decide`）直接返回结果。
- 任务工具（`submit_*` / `get_*` 成对）返回 `taskNo`；用对应的 `get_*`
  工具每 10-30 秒轮询，直到 `status` 为 `success` / `failed`。

## 计费

按用量计入算邻坊账户：语音识别约 0.5 元/小时音频；语音合成约 2 元/万字符；
文字识别约 0.005~0.015 元/页；决策约 2 元/百万输入 token。失败不计费。

## 隐私

见 [PRIVACY.md](../PRIVACY.md)。本插件仅把各工具所需输入
（音频/图片/PDF URL、文本、问题集）发送到 `suanlinfang.cn`；
API Key 只保存在你的 Dify 工作区内，不会写入日志。
