# 社交媒体 & 社区

Twitter/X、V2EX、Reddit、B站（公开搜索）。

## Twitter/X (twitter-cli)

### 稳定命令

```bash
# 首页时间线（最稳定）
twitter feed -n 20

# 读取单条推文（含回复）
twitter tweet URL_OR_ID

# 读取长文 / X Article
twitter article URL_OR_ID

# 用户时间线
twitter user-posts @username -n 20

# 用户资料
twitter user @username
```

### 可能不稳定的命令

```bash
# 搜索推文（Twitter 频繁改 GraphQL 端点，可能 404）
twitter search "query" -n 10

# likes（2024 年后只能看自己的，平台限制）
twitter likes
```

### search 失败时的重试链（按序执行，成功即停）

1. 直接重试一次（偶发失败常见）：`twitter search "query" -n 10`
2. 换 OpenCLI 备选（桌面，复用浏览器登录态）：`opencli twitter search "query" -f yaml`
3. 都不行就改用 `twitter feed` / `twitter user-posts @somebody` 等稳定命令绕路。
   不得在 fetch-only 工作流中自动升级工具。

### 重要注意事项

> 本 skill 不安装或升级工具。doctor 必须已报告 twitter-cli 后端可用；
> 版本选择属于单独、明确授权的维护流程。
>
> **认证**: 推荐用 Cookie-Editor 导出后设置环境变量 `TWITTER_AUTH_TOKEN` + `TWITTER_CT0`。自动提取在 SSH/Docker/无头环境不可用。
>
> **IP 风控**: 不要在 VPS/数据中心 IP 上频繁调用，尤其是 followers/following，有封号风险。使用住宅代理或本地环境。
>
> **OpenCLI 备选**: 桌面装了 OpenCLI 的话，`opencli twitter search/article/user-posts -f yaml` 全套可用（浏览器登录态，无需 cookie 环境变量）。
>
> **输出格式**: 建议用 `--yaml` 或 `--json` 获得结构化输出，对 AI agent 更友好。

## B站 / Bilibili（公开搜索 API，无凭据）

本 fork 只保留 B站的公开搜索 API（无登录态、无 Cookie）。bili-cli（上游停更）
与 OpenCLI 浏览器会话后端已移除。

```bash
# 公开搜索（无需任何配置）
curl --silent --show-error --max-time 30 --max-filesize 1048576 \
  --proto '=https' \
  "https://api.bilibili.com/x/web-interface/search/all/v2?keyword=QUERY&page=1" \
  -H "User-Agent: Mozilla/5.0"
```

> 只读搜索。视频详情/字幕/音频不在本 fork 范围内；不要用 yt-dlp 读 B站
> （风控 412 拦截）。

## V2EX (公开 API)

无需认证，直接调用公开 API。

### 热门主题

```bash
curl --silent --show-error --max-time 30 --max-filesize 1048576 --proto '=https' \
  "https://www.v2ex.com/api/topics/hot.json" -H "User-Agent: agent-reach/1.0"
```

### 节点主题

```bash
# node_name 如: python, tech, jobs, qna, programmers
curl --silent --show-error --max-time 30 --max-filesize 1048576 --proto '=https' \
  "https://www.v2ex.com/api/topics/show.json?node_name=python&page=1" \
  -H "User-Agent: agent-reach/1.0"
```

### 主题详情

```bash
# topic_id 从 URL 获取，如 https://www.v2ex.com/t/1234567
curl --silent --show-error --max-time 30 --max-filesize 1048576 --proto '=https' \
  "https://www.v2ex.com/api/topics/show.json?id=TOPIC_ID" \
  -H "User-Agent: agent-reach/1.0"
```

### 主题回复

```bash
curl --silent --show-error --max-time 30 --max-filesize 1048576 --proto '=https' \
  "https://www.v2ex.com/api/replies/show.json?topic_id=TOPIC_ID&page=1" \
  -H "User-Agent: agent-reach/1.0"
```

### 用户信息

```bash
curl --silent --show-error --max-time 30 --max-filesize 1048576 --proto '=https' \
  "https://www.v2ex.com/api/members/show.json?username=USERNAME" \
  -H "User-Agent: agent-reach/1.0"
```

> **节点列表**: https://www.v2ex.com/planes

## Reddit（多后端，必须登录态）

**Reddit 没有零配置路径**：匿名 `.json` 端点已被封（403），官方 API 自 2025-11 起人工审批基本不批。两个后端都靠登录态，先跑 `agent-reach doctor --json` 看 reddit 的 `active_backend`。中国大陆访问需代理。

### 后端 A：OpenCLI（桌面首选，复用浏览器登录态）

```bash
# 搜索帖子
opencli reddit search "query" -f yaml

# 读帖子全文 + 评论
opencli reddit read POST_ID -f yaml

# 浏览 subreddit / 热门 / Popular
opencli reddit subreddit LocalLLaMA -f yaml
opencli reddit hot -f yaml
opencli reddit popular -f yaml

# subreddit 元信息（订阅数、简介）
opencli reddit subreddit-info LocalLLaMA -f yaml
```

> 要求 Chrome 打开且浏览器里登录过 reddit.com。

### 后端 B：rdt-cli（存量/服务器备选，上游 2026-03 起停更）

```bash
rdt search "query" --limit 10   # 搜索帖子
rdt read POST_ID                # 读帖子全文 + 评论
rdt sub python --limit 20       # 浏览 subreddit
rdt popular --limit 10          # 浏览热门
rdt all --limit 10              # 浏览 /r/all
```

> 本 skill 不安装工具或改变登录状态。只有 doctor 已报告 rdt-cli 后端可用时
> 才调用它；安装和登录属于单独、明确授权的维护流程。
> 建议使用 `--yaml` 输出，对 AI agent 更友好。

### 高级选项：官方 API + PRAW（仅限已有凭证的用户）

2025-11 前注册过 Reddit script app（持有 client_id/client_secret）的用户可以用 PRAW 走官方 API（100 QPM 免费）。新申请需人工审批且个人项目基本不批，**不要推荐新用户走这条路**。
