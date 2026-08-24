# 小红书配置指南

## 功能说明
读取和搜索小红书笔记。桌面优先使用 OpenCLI 复用现有浏览器登录态；服务器
使用用户审阅并自行运行的 xiaohongshu-mcp。存量 xhs-cli 仅作兼容后端。

## 前置条件
- 桌面 Chrome + OpenCLI，或用户自行管理的 MCP 服务
- 浏览器已登录 xiaohongshu.com（用于导出 Cookie）

## Agent 可自动完成的步骤

### 1. 预览并批准桌面后端安装
```bash
agent-reach install --channels=xiaohongshu --dry-run
agent-reach install --channels=xiaohongshu --yes
```

### 2. 登录

在 Chrome 中由用户登录 xiaohongshu.com 并安装 OpenCLI 扩展。Agent Reach
不会自动改变登录状态。

### 3. 验证
```bash
agent-reach doctor
```

应该看到小红书显示为 ✅。

## 需要用户手动做的步骤

如果 `xhs login` 自动提取失败，需要手动导入 cookies：

> **推荐方式：Cookie-Editor 浏览器导出（最可靠）**
>
> 1. 在 Chrome 中安装 [Cookie-Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) 扩展
> 2. 浏览器登录 xiaohongshu.com
> 3. 点击 Cookie-Editor 图标 → Export → Header String
> 4. 不要把导出内容发给 Agent。在本机运行
>    `agent-reach configure xhs-cookies` 的隐藏提示，或用 `--stdin`。
>
> **注意**：不要依赖 QR 扫码登录，Cookie-Editor 导出方式最简单可靠。

## 使用示例

搜索笔记：
```bash
xhs search "关键词"
```

阅读笔记详情：
```bash
xhs read NOTE_ID
```

查看评论：
```bash
xhs comments NOTE_ID
```

## 常见问题

**Q: Cookie 过期了？**
A: 在浏览器重新登录。仅对用户自行管理的 Docker MCP，重新安全导入 Cookie。

**Q: 小红书提示 IP 风险？**
A: 如确有需要，用系统凭据管理器注入代理环境变量，勿在 argv 或聊天中暴露。

**Q: 存量 xhs-cli 还能用吗？**
A: doctor 会继续识别，但它不是新安装的默认后端。

## 备选方案：Docker MCP

如果你已经在使用 [xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp) Docker 方案，它也能正常工作：

从上游 release 页面审阅固定版本/摘要后自行部署，再显式执行：

```bash
mcporter config add xiaohongshu http://localhost:18060/mcp
```

Agent Reach 不拉取浮动镜像，也不管理长驻容器。
