# Cookie handling

Cookies are account-equivalent secrets. Do not paste them into agent chat,
command arguments, shell history, tickets, logs, or screenshots.

Prefer an upstream tool's own browser-session/login flow:

- Twitter desktop: OpenCLI, or export only `auth_token` and `ct0` locally.
- XiaoHongShu: OpenCLI on desktop or xiaohongshu-mcp's QR flow on a server.
- Bilibili: bili-cli/OpenCLI login flow.
- Xueqiu: local `configure --from-browser` on the machine that owns the browser.

For Twitter automation, pass the exported header over stdin:

```bash
printf '%s' "$TWITTER_COOKIE_HEADER" | \
  agent-reach configure twitter-cookies --stdin
```

For a local file, restrict its permissions first:

```bash
chmod 600 /secure/path/twitter-cookie.txt
agent-reach configure twitter-cookies --file /secure/path/twitter-cookie.txt
```

Delete the export after configuration. Agent Reach intentionally does not
persist XiaoHongShu or Bilibili browser cookies because current upstream
backends do not consume those config keys.
