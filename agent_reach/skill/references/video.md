# 视频/播客

YouTube、B站、小宇宙播客的字幕和转录。

## YouTube (yt-dlp)

### 获取视频元数据

```bash
yt-dlp --dump-json "URL"
```

### 下载字幕

```bash
# 下载字幕 (不下载视频)
yt-dlp --write-sub --write-auto-sub --sub-lang "zh-Hans,zh,en" --skip-download -o "/tmp/%(id)s" "URL"

# 然后读取 .vtt 文件
cat /tmp/VIDEO_ID.*.vtt
```

### 获取评论

```bash
# 提取评论（best-effort，不保证完整）
yt-dlp --write-comments --skip-download --write-info-json \
  --extractor-args "youtube:max_comments=20" \
  -o "/tmp/%(id)s" "URL"
# 评论在 .info.json 的 comments 字段中
```

### 搜索视频

```bash
yt-dlp --dump-json "ytsearch5:query"
```

> **字幕注意**: 手动上传的字幕提取可靠；自动生成字幕可能存在行间重复，需后处理。
> **评论注意**: `--write-comments` 基于网页抓取（非 YouTube Data API），部分评论可能丢失。

### 无字幕兜底：Whisper 音频转写

```bash
# 视频没有字幕时的兜底：下载音频并用 Whisper 转写（Groq 免费 key 即可）
agent-reach transcribe "https://www.youtube.com/watch?v=VIDEO_ID"
agent-reach transcribe ./local_audio.mp3 -o /tmp/transcript.txt
```

> 需要先安全配置 key：`printf '%s' "$GROQ_API_KEY" | agent-reach configure
> groq-key --stdin`（免费，console.groq.com），或用 `OPENAI_API_KEY` 配置
> `openai-key --stdin`。不得把 key 写进命令参数、聊天或日志。

## B站 / Bilibili（bili-cli 为主，OpenCLI 补字幕）

> ⚠️ **不要用 yt-dlp 读 B站**：B站风控已全面 412 拦截 yt-dlp（实测最新版、直连/代理/带 Cookie 全部无效）。yt-dlp 只用于 YouTube。

### 视频详情/搜索/热门/排行 (bili-cli，只读无需登录)

```bash
# 视频详情（标题/UP主/时长/播放互动数据/字幕可用性）
bili video BVxxx

# 搜索视频
bili search "query" --type video -n 5

# 热门视频 / 排行榜
bili hot -n 10
bili rank -n 10

# 下载音频并切分为 ASR-ready WAV（无字幕时配合 agent-reach transcribe 转写）
bili audio BVxxx
```

### 字幕 (OpenCLI，需要桌面 Chrome)

```bash
# 字幕逐句带时间轴
opencli bilibili subtitle BVxxx

# OpenCLI 也能搜索/读视频元数据（备选）
opencli bilibili search "query" -f yaml
opencli bilibili video BVxxx -f yaml
```

### 零配置兜底：搜索 API 直连

```bash
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
cookie_jar=$(mktemp "${TMPDIR:-/tmp}/agent-reach-bili.XXXXXX")
chmod 600 "$cookie_jar"
trap 'rm -f "$cookie_jar"' EXIT
curl --silent --show-error --max-time 30 --proto '=https' \
  -c "$cookie_jar" -o /dev/null -A "$UA" "https://www.bilibili.com/"
curl --silent --show-error --max-time 30 --max-filesize 1048576 --proto '=https' \
  -b "$cookie_jar" -A "$UA" -e "https://www.bilibili.com/" \
  "https://api.bilibili.com/x/web-interface/search/all/v2?keyword=QUERY&page=1"
```

> bili-cli 是存量兼容后端。本 fetch-only skill 不安装工具、不扫码登录，也不读取
> 动态/收藏等个人状态；只有 doctor 已报告后端可用时才调用只读命令。

## 小宇宙播客 / Xiaoyuzhou Podcast

### 转录单集播客

```bash
# 输出到 /tmp/
~/.agent-reach/tools/xiaoyuzhou/transcribe.sh \
  "https://www.xiaoyuzhoufm.com/episode/EPISODE_ID" /tmp/transcript.txt
```

> 隐私：音频会发送给已配置的 Groq/OpenAI 转录服务。默认临时音频在完成或失败后删除。

### 前置要求

1. **ffmpeg**: 需要已由用户通过单独、明确授权的系统维护流程安装
2. **Groq API Key** (免费): https://console.groq.com/keys
3. **配置 Key**: `printf '%s' "$GROQ_API_KEY" | agent-reach configure groq-key --stdin`
4. **首次运行**: 用户确认后运行 `agent-reach install --yes --channels=xiaoyuzhou`

### 检查状态

```bash
agent-reach doctor
```

> 输出 Markdown 文件默认保存到 `/tmp/`。

## 选择指南

| 场景 | 推荐工具 |
|-----|---------|
| YouTube 字幕 | yt-dlp |
| B站视频详情/搜索 | bili-cli |
| B站字幕 | opencli bilibili subtitle |
| 播客转录 | 小宇宙 transcribe.sh |
| 无字幕音视频 | agent-reach transcribe（B站音频先 `bili audio`） |
