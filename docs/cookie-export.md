# Cookie handling

Cookies are account-equivalent secrets. Do not paste them into agent chat,
command arguments, shell history, tickets, logs, or screenshots.

Prefer an upstream tool's own browser-session/login flow:

- Twitter desktop: OpenCLI, or export only `auth_token` and `ct0` locally.
- Reddit: OpenCLI or rdt-cli login flow.

`agent-reach configure --from-browser` extracts Twitter's `auth_token` and
`ct0` only. It does not read or persist cookies for any other channel;
Bilibili's channel uses a public search API and needs no cookies.

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

Delete the export after configuration. The Twitter health probe never
executes `twitter-cli` unless `TWITTER_AUTH_TOKEN` and `TWITTER_CT0` are both
configured, so running `agent-reach doctor` cannot trigger the macOS Keychain
prompt on its own.
