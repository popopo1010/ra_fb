# RA FB システム

初回架電・法人面談の文字起こしからフィードバックを生成し、Slack に投稿するシステム。

## 機能

| 種別 | 説明 | コマンド/入力 |
|------|------|---------------|
| **RA** | 初回架電FB | `/rafb`、ファイルアップロード、CLI、Webhook |
| **CA** | 法人面談FB | `/fb`、CLI、Webhook |

※ 茂野・重野・大城は同一人物。架電記録は `references/long_calls/茂野/` に統合。

## クイックスタート

```bash
# 1. 依存関係
pip install -r requirements.txt

# 2. 環境変数（.env）
# ANTHROPIC_API_KEY, SLACK_WEBHOOK_URL, SLACK_BOT_TOKEN, SLACK_APP_TOKEN 等

# 3. CLI で FB 生成（Slack に投稿）
python scripts/cli.py ra references/long_calls/茂野/TOKAI_EC_茂野_016.md

# 4. Slack サーバー起動（/rafb, /fb が使える）
python scripts/slack_server.py
```

## ディレクトリ構成

```
RA_FBシステム/
├── ra_fb/                 # コアパッケージ
│   ├── config.py
│   ├── utils.py
│   ├── feedback.py       # FB 生成ロジック
│   └── slack.py          # Slack 投稿
├── scripts/
│   ├── cli.py            # コマンドライン（ra/ca）
│   ├── slack_server.py   # Slack /rafb /fb
│   └── webhook_server.py # Notta × Zapier
├── references/           # リファレンス（マニュアル・課題整理等）
│   ├── manual/
│   ├── candidate_attract/  # 候補者アトラクト（会社の魅力の伝え方）
│   ├── long_calls/
│   └── 法人面談議事録/
├── docs/                 # 詳細ドキュメント
└── requirements.txt
```

## 環境変数

| 変数 | 必須 | 説明 |
|------|------|------|
| ANTHROPIC_API_KEY | ○ | Claude API キー |
| SLACK_WEBHOOK_URL | ○ | RA FB 投稿先（#dk_ra_初回架電fb） |
| SLACK_BOT_TOKEN | ○（Slack 使用時） | Slack Bot Token |
| SLACK_APP_TOKEN | ○（Slack 使用時） | Slack App-Level Token |
| SLACK_WEBHOOK_URL_CA | 任意 | CA FB 投稿先 |
| SLACK_WEBHOOK_URL_茂野 | 任意 | 茂野個別チャンネル |
| SLACK_WEBHOOK_URL_小山田 | 任意 | 小山田個別チャンネル |
| WEBHOOK_SECRET | 任意 | Notta Webhook 認証 |
| SALES_FB_AGENT_PATH | 任意 | sales-fb-agent のパス（候補者アトラクト参照。未設定時は references/candidate_attract/ を使用） |

## 入力方法

1. **Slack /rafb, /fb** … モーダルに文字起こしを貼り付け
2. **Slack ファイルアップロード** … .txt/.md をチャンネルにドロップ（RA のみ）
3. **CLI** … `python scripts/cli.py ra/ca <ファイルパス>`
4. **Notta × Zapier** … Webhook に POST（`python scripts/webhook_server.py` + ngrok）

## ドキュメント

- [Slack 設定](docs/Slack_テキストファイルアップロード設定.md)
- [Notta × Zapier 連携](docs/Notta_Zapier_連携設定.md)
- [個別 Slack 連携](docs/Slack_個別連携設定.md)
