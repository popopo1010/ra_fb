# RA FB システム

初回架電・法人面談の文字起こしからフィードバックを生成し、Slack に投稿するシステム。

## 機能

| 種別 | 説明 | コマンド/入力 |
|------|------|---------------|
| **RA** | 初回架電FB | `/rafb`、ファイルアップロード、CLI、Webhook |
| **CA** | 法人面談FB | `/fb`、CLI、Webhook |

※ 茂野・重野・大城は同一人物。架電記録は `data/input/ra/茂野/` に統合。

## クイックスタート

```bash
# 1. 依存関係
pip install -r requirements.txt

# 2. 環境変数（.env）
# ANTHROPIC_API_KEY, SLACK_WEBHOOK_URL, SLACK_BOT_TOKEN, SLACK_APP_TOKEN 等

# 3. CLI で FB 生成（Slack に投稿）
python scripts/cli.py ra data/input/ra/茂野/TOKAI_EC_茂野_016.md

# 4. Slack サーバー起動（/rafb, /fb が使える）
python scripts/slack_server.py
```

## ディレクトリ構成

```
RA_FBシステム/
├── ra_fb/                    # コアパッケージ
│   ├── config.py             # 設定・パス定数
│   ├── utils.py
│   ├── feedback.py           # FB 生成ロジック
│   ├── slack.py              # Slack 投稿
│   └── company.py            # 法人情報抽出・事業リサーチ・比較
├── scripts/
│   ├── slack_server.py       # Slack /rafb /fb（メイン起動）
│   ├── webhook_server.py     # Notta × Zapier
│   ├── cli.py                # コマンドライン（ra/ca）
│   ├── compare_companies.py  # 都道府県×セグメントで法人比較
│   └── bulk_import_company.py # 過去文字起こしから法人マスタ一括生成
├── data/
│   ├── input/                # 入力データ
│   │   ├── ra/               # 初回架電（RA）文字起こし
│   │   └── ca/               # 法人面談（CA）議事録
│   └── output/
│       └── 法人マスタ/        # FB生成時に自動抽出・格納（事業リサーチ含む）
├── references/
│   ├── manual/               # 架電マニュアル・PSS・チェックリスト
│   └── candidate_attract/    # 候補者アトラクト
├── docs/
├── pyproject.toml
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

## 法人情報の自動格納・比較（都道府県×セグメント）

FB を出すたびに、文字起こしから法人情報を抽出し `data/output/法人マスタ/{会社名}.md` に保存。**都道府県×セグメント**で比較可能。

- **マスタ項目**: [data/output/法人マスタ/マスタ項目一覧.md](data/output/法人マスタ/マスタ項目一覧.md)

```bash
# 比較（例: 愛知 × 電気系）
python scripts/compare_companies.py 愛知 電気系
```

CLI で `--no-company` を付けると法人情報の保存を無効化。

```bash
# 過去の文字起こしから法人マスタを一括生成（再アップロード不要）
python scripts/bulk_import_company.py --dry-run   # 予覧
python scripts/bulk_import_company.py             # 実行
```

## 入力方法

1. **Slack /rafb, /fb** … モーダルに文字起こしを貼り付け
2. **Slack ファイルアップロード** … .txt/.md をチャンネルにドロップ（RA のみ）
3. **CLI** … `python scripts/cli.py ra/ca <ファイルパス>`
4. **Notta × Zapier** … Webhook に POST（`python scripts/webhook_server.py` + ngrok）

## ドキュメント

- [プロジェクト構成](docs/プロジェクト構成.md) … 全体像・機能一覧・法人マスタ20項目
- [起動ガイド](docs/起動ガイド.md) … ikeobook15 / kazushi の起動手順
- [Slack 設定](docs/Slack_テキストファイルアップロード設定.md)
- [Notta × Zapier 連携](docs/Notta_Zapier_連携設定.md)
- [個別 Slack 連携](docs/Slack_個別連携設定.md)
