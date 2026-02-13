# RA_FBシステム

RA（リクルティングアドバイザー）の初回架電の文字起こしからフィードバックを生成し、Slack `#dk_ra_初回架電fb` に投稿するシステム。

---

## クイックスタート

### 1. セットアップ（初回のみ）

```bash
cd /Users/ikeobook15/RA_FBシステム
./setup.sh
source venv/bin/activate
cp .env.example .env
# .env を編集して SLACK_WEBHOOK_URL を設定
```

### 2. 使い方

| 方法 | 手順 |
|------|------|
| **Cursor** | 架電記録を開いた状態で `/rafb` と入力 |
| **コマンドライン** | `python scripts/generate_feedback.py references/long_calls/茂野/xxx.md` |
| **Slack App** | `python scripts/slack_app_server.py` でサーバー起動後、Slack で `/rafb` |

---

## ディレクトリ構成

```
RA_FBシステム/
├── setup.sh                 # セットアップ（venv 作成・依存関係インストール）
├── requirements.txt
├── .env                     # 環境変数（gitignore）
├── .env.example
├── .cursor/commands/
│   └── rafb.md              # Cursor 用 /rafb コマンド定義
├── scripts/
│   ├── generate_feedback.py  # フィードバック生成＋Slack投稿
│   ├── post_to_slack.py     # Slack投稿のみ
│   ├── slack_app_server.py  # Slack /rafb サーバー（Socket Mode・ngrok不要）
│   └── README.md
├── docs/
│   ├── Slack_App実装ガイド.md
│   └── ローカルSlack連携の手順.md
└── references/
    ├── manual/              # 営業マニュアル、PSS
    │   ├── 営業新規架電マニュアル.md
    │   └── PSS_プロフェッショナルセリングスキル.md
    ├── long_calls/          # 架電記録（重野・茂野・小山田）
    ├── 初回面談_確認チェックリスト.md
    └── 法人面談議事録/
```

---

## セットアップ詳細

### 環境変数（.env）

| 変数 | 必須 | 説明 |
|------|------|------|
| `SLACK_WEBHOOK_URL` | ○ | #dk_ra_初回架電fb の Incoming Webhook URL |
| `SLACK_BOT_TOKEN` | Slack App 利用時 | Bot User OAuth Token（xoxb-） |
| `SLACK_APP_TOKEN` | Slack App 利用時 | App-Level Token（xapp-） |
| `ANTHROPIC_API_KEY` | オプション | AI フィードバック用（未設定時はテンプレート） |

### 仮想環境について

macOS などで `pip install` が使えない場合、`./setup.sh` で venv を作成します。

```bash
./setup.sh
source venv/bin/activate
# 以降、python / pip は venv 内のものが使われる
```

---

## 詳細ドキュメント

- [docs/メンバー向けセットアップガイド.md](docs/メンバー向けセットアップガイド.md) … **他メンバーが使えるようにする手順**
- [scripts/README.md](scripts/README.md) … スクリプトの使い方
- [docs/Slack_App実装ガイド.md](docs/Slack_App実装ガイド.md) … Slack で /rafb を使う手順
- [docs/ローカルSlack連携の手順.md](docs/ローカルSlack連携の手順.md) … ローカル環境の構築
