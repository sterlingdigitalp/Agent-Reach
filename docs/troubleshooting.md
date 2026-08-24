# 常见问题排查

## doctor 默认不显示 Web/Exa/Bilibili/V2EX/LinkedIn 的真实状态

**症状：** `agent-reach doctor` 里这几个渠道显示 `skipped`。

**原因：** 这些探测会发起出站网络请求，`doctor` 默认离线运行，避免每次体检都
泄露访问记录。

**解决方案：** 需要真实探测联网渠道时运行：

```bash
agent-reach doctor --live
```

## Twitter/X: twitter-cli 连接失败

**症状：** `twitter search` 或其他命令返回错误

**原因：** twitter-cli 需要 `TWITTER_AUTH_TOKEN` 和 `TWITTER_CT0`。
如果网络环境需要代理，代理凭据也应由系统凭据管理器注入。

**解决方案：**

### 方案 1：设置环境变量代理

在当前进程中从系统凭据管理器设置 `HTTP_PROXY`/`HTTPS_PROXY`，再运行
`twitter search "test" -n 1`。不要把含用户名或密码的代理 URL 放进命令行、
聊天或文档。

### 方案 2：使用全局代理工具

让代理工具接管所有网络流量，这样 twitter-cli 的请求也会走代理：

```bash
# macOS — ClashX / Surge 开启"增强模式"
# Linux — proxychains 或 tun2socks
proxychains twitter search "test" -n 1
```

### 方案 3：不用 twitter-cli，用 Exa 搜索替代

twitter-cli 不可用时，可以直接用 Exa 搜索 Twitter 内容：

```bash
mcporter call 'exa.web_search_exa(query: "site:x.com 搜索词", numResults: 5)'
```

### 方案 4：检查认证

```bash
twitter status
```

> 如果返回 `not_authenticated`，请用受保护的环境注入
> `TWITTER_AUTH_TOKEN` 和 `TWITTER_CT0`，或运行
> `agent-reach configure twitter-cookies` 使用隐藏提示。
>
> **Fallback：** 如果已经安装 bird CLI，Agent Reach 会自动检测。安装或升级
> 外部工具属于单独的、需要审阅固定版本并明确授权的维护流程。
