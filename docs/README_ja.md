# Agent Reach

Agent Reach は、13 のインターネットサービス向け上流ツールをインストール・設定・
診断する capability layer です。統一 `read`/`search` ラッパーではありません。
`agent-reach doctor --json` が選んだ `active_backend` をエージェントが直接呼びます。

対応: GitHub、Twitter/X、YouTube、Reddit、Bilibili、XiaoHongShu、
LinkedIn、Xiaoyuzhou、V2EX、Xueqiu、RSS、Exa Search、Web。
Exa は mcporter 経由で API key 不要です。Reddit はログインが必須です。

## 安全なインストール

```bash
python -m pip install "agent-reach==1.5.0"
agent-reach install --env=auto                 # 読み取り専用プラン
agent-reach install --env=auto --dry-run       # 書き込みゼロ
agent-reach install --env=auto --yes            # レビュー後に実行
```

Agent Reach は sudo、OS パッケージマネージャー、ダウンロードした setup script を
自動実行しません。`doctor` も完全に読み取り専用です。

秘密情報を argv、シェル履歴、チャット、ログに入れないでください。

```bash
agent-reach configure groq-key
printf '%s' "$GROQ_API_KEY" | agent-reach configure groq-key --stdin
```

資格情報ファイルは既存ファイルも含め owner-only に安全に置換されます。GitHub
token は `gh` 自身が保存し、Agent Reach はコピーを保持しません。

## 診断とスキル

```bash
agent-reach doctor --json
agent-reach skill --install
```

既存のカスタム skill は `--force` なしでは上書きされません。skill は fetch-only
で、取得コンテンツを信頼せず、厳密な host 検証・出力量制限・秘密保護を行います。
書き込み操作には別の明示的な承認が必要です。

詳細は [英語 README](README_en.md)、[インストールガイド](install.md)、
[更新ガイド](update.md) を参照してください。
