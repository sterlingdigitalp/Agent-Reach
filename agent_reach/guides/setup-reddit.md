# Reddit 配置指南

## 功能说明

Reddit 封锁了几乎所有非浏览器的直接访问（包括数据中心和 ISP 代理 IP），JSON API 返回 403。

Agent Reach 通过 **rdt-cli** 实现 Reddit 的搜索和阅读功能：
- **搜索**：`rdt search "关键词"`
- **阅读完整帖子+评论**：`rdt read POST_ID`

免费，无需代理，无需 API Key。需要登录认证（`rdt login`，自动从浏览器提取 Cookie）。

## Agent 可自动完成的步骤

1. 检查 rdt-cli 是否可用：
```bash
which rdt && echo "installed" || echo "not installed"
```

2. 如果用户明确批准，安装经过固定提交审阅的版本：
```bash
pipx install 'git+https://github.com/public-clis/rdt-cli.git@5e4fb3720d5c174e976cd425ccc3b879d52cac66'
```

或一键安装：
```bash
agent-reach install --env=auto --channels=reddit --dry-run
agent-reach install --env=auto --channels=reddit --yes
```

## 使用示例

搜索 Reddit 内容：
```bash
rdt search "python best practices" -n 5
```

阅读完整帖子和评论：
```bash
rdt read POST_ID
```

## 需要用户手动做的步骤

登录是显式用户操作。桌面 OpenCLI 复用浏览器登录态；rdt-cli 需要用户运行
`rdt login`。Agent Reach 不代替用户改变登录状态。

## Fallback：Exa 搜索

如果你已经配置了 Exa（通过 mcporter），也可以通过 Exa 搜索 Reddit 内容：

```bash
mcporter call 'exa.web_search_exa(query: "python best practices", numResults: 5, includeDomains: ["reddit.com"])'
```

rdt-cli 是当前推荐方案，无需额外配置即可使用。
