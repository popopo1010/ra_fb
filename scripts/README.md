# 初回架電フィードバック → Slack 投稿

初回架電の文字起こしからフィードバックを生成し、Slack `#dk_ra_初回架電fb` に投稿するスクリプトです。

**Cursor では `/rafb` コマンドで実行できます。** 架電記録ファイルを開いた状態で `/rafb` と入力してください。

---

## セットアップ

### 1. 環境変数の設定

```bash
cp .env.example .env
# .env を編集して SLACK_WEBHOOK_URL を設定
```

※ Webhook URL は Slack > チャンネル設定 > 連携 > Incoming Webhook で取得

### 2. 依存関係のインストール

```bash
# プロジェクトルートで実行
./setup.sh
source venv/bin/activate
```

`setup.sh` は venv を作成し、`requirements.txt` の依存関係をインストールします。  
macOS で `pip install` が使えない場合に推奨です。

---

## 使い方

### フィードバック生成 + Slack投稿

```bash
python scripts/generate_feedback.py references/long_calls/茂野/TOKAI_EC_茂野_016.md
```

- 文字起こしを読み込み
- リファレンス（マニュアル・チェックリスト・課題整理）に基づいてAIがフィードバックを生成
- `#dk_ra_初回架電fb` に投稿

### オプション

| オプション | 説明 |
|----------|------|
| `--no-slack` | Slackに送らず、標準出力にのみ表示 |
| `--no-ai` | AIを使わずテンプレートのみ（ANTHROPIC_API_KEYなしでも動作） |

### テキストを直接Slackに投稿するだけ

```bash
# ファイルの内容を投稿
python scripts/post_to_slack.py feedback.txt

# 標準入力から投稿
echo "フィードバック内容" | python scripts/post_to_slack.py
```

---

## Slack App（/rafb を Slack で使う）

Slack 上で `/rafb` コマンドを使うには、Socket Mode 版サーバーを起動します。**ngrok は不要**です。

```bash
source venv/bin/activate
python scripts/slack_app_server.py
```

`.env` に `SLACK_BOT_TOKEN`、`SLACK_APP_TOKEN`、`SLACK_WEBHOOK_URL` を設定してください。

詳細は [docs/Slack_App実装ガイド.md](../docs/Slack_App実装ガイド.md) を参照。

---

## AIフィードバックのため（オプション）

`ANTHROPIC_API_KEY` を .env に設定すると、Claude（claude-sonnet-4）で詳細なフィードバックを自動生成します。

```
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

未設定の場合はテンプレート形式のフィードバックになります。
