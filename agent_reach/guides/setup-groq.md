# Groq Whisper 配置指南

## 功能说明
当 YouTube/Bilibili 视频没有字幕时，用 Groq 的 Whisper API 进行语音转文字。Groq 提供免费额度。

## 安全配置

1. 检查是否已配置：
```bash
agent-reach doctor | grep -i "groq\|whisper"
```

2. 让用户在本机隐藏提示中输入。不要让用户把 key 发到聊天：

```bash
agent-reach configure groq-key
```

自动化应从受保护的环境通过 stdin 传入：

```bash
printf '%s' "$GROQ_API_KEY" | agent-reach configure groq-key --stdin
```

## 需要用户手动做的步骤

请告诉用户：

> 视频语音转文字需要一个 Groq API Key（免费）。
>
> 步骤：
> 1. 打开 https://console.groq.com
> 2. 用 Google 账号或邮箱注册
> 3. 点击左侧 "API Keys"
> 4. 点击 "Create API Key"
> 5. 在本机运行 `agent-reach configure groq-key`，通过隐藏提示粘贴
>
> Groq 提供免费额度，日常使用完全够用。

Agent 不应接收、回显或测试用户的原始 key。`agent-reach transcribe` 会在上传前
显示隐私提示；音频将发送给 Groq，默认临时文件在成功或失败后删除。
