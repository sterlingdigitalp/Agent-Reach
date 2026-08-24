# Exa Search 配置指南

## 功能说明
Exa 是一个 AI 语义搜索引擎。通过 MCP 接入，**免费、无需 API Key**。配置后解锁：
- 全网语义搜索
- Reddit 搜索（通过 site:reddit.com）
- Twitter 搜索（通过 site:x.com）

## Explicit setup

先预览；只有明确同意后才允许用户级 npm 安装和 mcporter 配置：

```bash
agent-reach install --env=auto --dry-run
agent-reach install --env=auto --yes
```

### 1. 安装 mcporter
```bash
npm install -g mcporter@REVIEWED_VERSION
```

### 2. 注册 Exa MCP
```bash
mcporter config add exa https://mcp.exa.ai/mcp
```

### 3. 验证
```bash
agent-reach doctor | grep "Search"
mcporter call 'exa.web_search_exa(query: "test", numResults: 1)'
```

## 需要用户手动做的步骤

**无凭据步骤。** Exa 通过 MCP 接入，无需 API Key。安装和配置仍然是写操作，
必须由用户审阅并显式同意。

如果 `agent-reach install` 因为网络问题没有自动配置 Exa，手动运行上面两条命令即可。

## 常见问题

**Q: 有搜索次数限制吗？**
A: 不承诺无限制。端点的配额、条款和可用性由上游决定。

**Q: mcporter 是什么？**
A: MCP 协议的命令行桥接工具，用来调用 MCP Server。Agent Reach 用它来连接 Exa 和小红书。
