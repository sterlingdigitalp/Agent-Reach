# 开发工具

GitHub CLI 

## GitHub (gh CLI)

本 fetch-only skill 只使用 GitHub CLI 的读取与搜索命令。

```bash
# 查看认证状态（只读）
gh auth status

# 搜索
gh search repos "query" --sort stars --limit 10
gh search code "query" --language python

# 仓库（只读）
gh repo view owner/repo

# Issues（只读）
gh issue list -R owner/repo --state open
gh issue view 123 -R owner/repo

# Pull Requests（只读）
gh pr list -R owner/repo --state open
gh pr view 123 -R owner/repo
gh pr checks 123 --repo owner/repo

# Actions / CI
gh run list --repo owner/repo --limit 10
gh run view <run-id> --repo owner/repo
gh run view <run-id> --repo owner/repo --log-failed
gh workflow list --repo owner/repo

# Releases
gh release list -R owner/repo

# API
gh api /user
gh api repos/owner/repo

# JSON 输出
gh issue list --repo owner/repo --json number,title --jq '.[] | "\(.number): \(.title)"'
```

> 创建/修改仓库、Issue、PR、Release 等写操作不属于 Agent Reach。只有用户明确授权后，
> 才能切换到独立的 GitHub 写操作工作流。

## 选择指南

| 工具 | 来源 | 用途 |
|-----|------|------|
| gh CLI | agent-reach | Git 操作 |
| zread | my-mcp-tools | 读仓库内容 |
| context7 | my-mcp-tools | 查技术文档 |
