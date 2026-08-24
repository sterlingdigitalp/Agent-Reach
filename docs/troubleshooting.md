# 常见问题排查

## 雪球 / Xueqiu: API 返回 400

**症状：** `agent-reach doctor` 显示雪球 ⚠️，报 `HTTP Error 400`

**原因：** 雪球 API 需要登录 Cookie，无法通过匿名访问获取。

**解决方案：** 在 Chrome 里登录 xueqiu.com，然后运行：

```bash
agent-reach configure --from-browser chrome
```

再次运行 `agent-reach doctor` 确认恢复 ✅。Cookie 过期后重新运行即可。

---

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
