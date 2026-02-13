# ローカルで Slack /rafb を動かす手順（ngrok 不要）

---

## 1. 前提

- Python 3 がインストールされていること
- Slack App を作成済み（未作成の場合は [Slack App 作成手順](#2-slack-app-の作成) を参照）

---

## 2. Slack App の作成

### 2-1. アプリ作成

1. [api.slack.com/apps](https://api.slack.com/apps) にアクセス
2. **Create New App** → **From scratch**
3. App Name: `RA初回架電FB`、Workspace を選択

### 2-2. App Home でボット名を設定（必須）

「インストールするボットユーザーがありません」を防ぐため、**必ず実施**してください。

1. 左メニュー **App Home**
2. **App Display Name** の横の **Edit** をクリック
3. **Display Name**: `RA初回架電FB` など
4. **Default username**: `ra-fb` など（半角英数字のみ）
5. **Save**

### 2-3. Socket Mode を有効化

1. 左メニュー **Settings** → **Socket Mode**
2. **Enable Socket Mode** を ON にする
3. **Basic Information** を開き、下にスクロールして **App-Level Tokens** を探す
4. **Generate Token and Scopes** をクリック
5. Token Name: `ra-fb-socket`、Scope: `connections:write` を追加
6. **Generate** をクリックし、**xapp-** で始まるトークンをコピー

### 2-4. Slash コマンドを追加

1. 左メニュー **Slash Commands** → **Create New Command**
2. Command: `/rafb`、Request URL: 空欄で OK
3. Short Description: `初回架電フィードバックを生成`
4. Usage Hint: `references/long_calls/茂野/xxx.md`
5. **Save**

### 2-5. ワークスペースにインストール

1. 左メニュー **OAuth & Permissions** → **Install to Workspace**
2. **xoxb-** で始まる **Bot User OAuth Token** をコピー

---

## 3. ローカル環境の準備

### 3-1. セットアップ（初回のみ）

```bash
cd /Users/ikeobook15/RA_FBシステム
./setup.sh
```

`setup.sh` は venv を作成し、依存関係をインストールします。  
macOS で `pip install` が使えない場合に有効です。

### 3-2. .env にトークンを設定

`.env` に以下を追加：

```
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx（Bot User OAuth Token）
SLACK_APP_TOKEN=xapp-xxxxxxxxxxxx（App-Level Token）
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx（#dk_ra_初回架電fb の Incoming Webhook）
```

---

## 4. 起動手順

```bash
cd /Users/ikeobook15/RA_FBシステム
source venv/bin/activate
python scripts/slack_app_server.py
```

表示例：
```
==================================================
RA FB サーバー起動（Socket Mode = ngrok 不要）
Slack で /rafb が使えます
==================================================
```

---

## 5. 使い方

### Slack で実行

```
/rafb references/long_calls/茂野/TOKAI_EC_茂野_016.md
```

または、文字起こしを直接貼り付け（長文をそのまま入力）→ 処理後、#dk_ra_初回架電fb に投稿されます。

---

## 6. トラブルシューティング

| 症状 | 対処 |
|------|------|
| `slack_bolt がインストールされていません` | `./setup.sh` 実行後、`source venv/bin/activate` |
| `dispatch_failed` | サーバーが起動しているか確認 |
| `インストールするボットユーザーがありません` | **App Home** で Display Name と Default username を設定 |
| Bot User OAuth Token が見つからない | **OAuth & Permissions** の上部。先に **Install to Workspace** を実行 |
| App-Level Token が見つからない | **Basic Information** を開き、下にスクロールして **App-Level Tokens** を探す |
