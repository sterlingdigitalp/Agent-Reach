# Twitter 高级功能配置指南（twitter-cli）

Twitter 基础阅读通过 Jina Reader 免费可用，无需配置。

高级功能需要 twitter-cli（@public-clis/twitter-cli）：

- 搜索推文（`twitter search`）
- 读取完整推文和对话链（`twitter tweet`、`twitter thread`）
- 用户时间线（`twitter timeline`）
- 长文阅读（`twitter article`）

twitter-cli 是免费开源工具（pipx 安装），但需要你的 Twitter 账号 cookie。

## 快速配置

1. 检查 twitter-cli 是否安装：

```bash
which twitter && echo "installed" || echo "not installed"
```

2. 安装 twitter-cli：

```bash
pipx install "twitter-cli==REVIEWED_VERSION"
```

3. 测试是否配置好：

```bash
twitter search "test" -n 1
```

## 获取 Cookie（Cookie-Editor 方式，推荐）

1. 安装 [Cookie-Editor](https://cookie-editor.com/) 浏览器扩展
2. 登录 x.com
3. 点击 Cookie-Editor 图标 → Export → 复制全部
4. 不要把导出内容发到聊天。在本机运行隐藏提示：

```bash
agent-reach configure twitter-cookies
```

这会提取 `auth_token` 和 `ct0`，以 0600 原子写入 Agent Reach 配置，并仅在
健康探测子进程中注入。直接调用 twitter-cli 时仍需从受保护的环境注入
`TWITTER_AUTH_TOKEN`/`TWITTER_CT0`。

## 手动设置 Cookie

如果你已经知道 `auth_token` 和 `ct0`：

1. 审阅上游发布后安装固定版本：`pipx install "twitter-cli==REVIEWED_VERSION"`

2. 设置环境变量：

```bash
printf '%s' "$TWITTER_COOKIE_HEADER" | agent-reach configure twitter-cookies --stdin
```

3. 测试：

```bash
twitter search "test" -n 1
```

## 代理配置

> twitter-cli 支持标准代理环境变量。含凭据的代理 URL 必须由系统凭据管理器
> 注入 `HTTP_PROXY`/`HTTPS_PROXY`，不要放进命令参数、聊天或文档。

也可以使用全局代理工具：

```bash
proxychains twitter search "test" -n 1
```

## Fallback：bird CLI

如果你已经安装了 bird CLI，Agent Reach 会把它作为存量兼容后端。不要由
fetch-only skill 安装或升级它；版本选择属于单独、明确授权的维护流程。
