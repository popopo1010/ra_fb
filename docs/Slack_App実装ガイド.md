# Slack App 実装ガイド（/rafb を Slack で使う）

Slack App として `/rafb` を実装する場合の手順です。**Socket Mode** を使用するため、**ngrok は不要**です。

---

## 実装方式の比較

| 方式 | ファイルの渡し方 | 必要な環境 | 難易度 |
|------|------------------|------------|--------|
| **A. ローカル + Socket Mode** | ファイルパス or 文字起こし貼り付け | PC、venv、slack_bolt | ★☆☆ |
| **B. クラウド（Cloud Run等）** | 文字起こしを貼り付け | GCP アカウント、デプロイ | ★★★ |

※Socket Mode は **ngrok 不要**。アプリが Slack に WebSocket で接続するため、公開 URL の設定が不要です。

---

## 方式A: ローカル + Socket Mode（推奨・ngrok 不要）

### 前提

- 架電記録がローカル（`references/long_calls/`）にある
- 実行時は PC を起動したままにする

### 手順

#### 1. Slack App を作成

1. [api.slack.com/apps](https://api.slack.com/apps) にアクセス
2. **Create New App** → **From scratch**
3. **App Name**: `RA初回架電FB`
4. **Workspace**: 使用するワークスペースを選択
5. **Create App** をクリック

#### 2. App Home でボット名を設定（重要）

※「インストールするボットユーザーがありません」エラーを防ぐため、**必ず実施**してください。

1. 左メニュー **App Home**
2. **App Display Name** の横の **Edit** をクリック
3. 以下を設定：
   - **Display Name (Bot Name)**: `RA初回架電FB` など（日本語可）
   - **Default username**: `ra-fb` など（半角英数字のみ）
4. **Save** をクリック

#### 3. Socket Mode を有効化

1. 左メニュー **Settings** → **Socket Mode**
2. **Enable Socket Mode** を ON にする

#### 4. App-Level Token を発行

1. **Basic Information** を開き、下にスクロールして **App-Level Tokens** を探す  
   （または Socket Mode ページの下部）
2. **Generate Token and Scopes** をクリック
3. **Token Name**: `ra-fb-socket` など任意
4. **Scope** に `connections:write` を追加
5. **Generate** をクリック
6. 表示された **xapp-** で始まるトークンをコピー（後で `.env` に設定）

#### 5. Slash コマンドを追加

1. 左メニュー **Slash Commands** → **Create New Command**
2. 以下を入力：

| 項目 | 入力値 |
|------|--------|
| Command | `/rafb` |
| Request URL | （Socket Mode では不要・空欄のままでも可） |
| Short Description | 初回架電フィードバックを生成して #dk_ra_初回架電fb に投稿 |
| Usage Hint | （空欄でOK。モーダルが開きます） |

3. **Save** をクリック

#### 6. 権限（OAuth Scopes）を設定

1. 左メニュー **OAuth & Permissions**
2. **Scopes** の **Bot Token Scopes** に以下を追加：
   - `commands`（Slash コマンド用、通常は自動付与）
   - `chat:write`（モーダル送信後の「処理中」メッセージ用）
3. **Install to Workspace** をクリックしてワークスペースにインストール
4. 表示された **xoxb-** で始まる **Bot User OAuth Token** をコピー（後で `.env` に設定）

#### 7. .env にトークンを設定

`.env` に以下を追加：

```
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx（Bot User OAuth Token）
SLACK_APP_TOKEN=xapp-xxxxxxxxxxxx（App-Level Token）
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx（#dk_ra_初回架電fb の Incoming Webhook）
```

#### 8. ローカル環境の準備

```bash
cd /Users/ikeobook15/RA_FBシステム
./setup.sh              # 初回のみ（venv 作成）
source venv/bin/activate
```

#### 9. サーバーを起動

```bash
python scripts/slack_app_server.py
```

**これだけです。ngrok は不要です。**

#### 10. 使い方

Slack で `/rafb` を入力すると、**モーダル（入力スペース）**が開きます。

1. `/rafb` と入力して Enter
2. モーダルに文字起こしを貼り付け
3. **送信** をクリック

→ 処理後、#dk_ra_初回架電fb に投稿されます。

---

## 方式A：文字起こし貼り付けのみ

`/rafb` 実行時にモーダルが開き、文字起こしを貼り付けて送信する形式です。

---

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| `slack_bolt がインストールされていません` | `./setup.sh` 実行後、`source venv/bin/activate` |
| `dispatch_failed` | サーバーが起動しているか確認。`python scripts/slack_app_server.py` |
| `インストールするボットユーザーがありません` | **App Home** で Display Name と Default username を設定 |
| Bot User OAuth Token が見つからない | **OAuth & Permissions** の上部。先に **Install to Workspace** を実行 |
| App-Level Token が見つからない | **Basic Information** を開き、下にスクロールして **App-Level Tokens** を探す |

---

## チェックリスト

### Slack App 作成時

- [ ] api.slack.com/apps で App 作成
- [ ] **App Home** でボット名を設定
- [ ] Socket Mode を有効化
- [ ] App-Level Token を発行（`connections:write`）
- [ ] Slash Commands で `/rafb` を追加
- [ ] Install to Workspace でインストール

### ローカル起動時

- [ ] `./setup.sh` で venv 作成
- [ ] `source venv/bin/activate` で有効化
- [ ] `.env` に `SLACK_BOT_TOKEN`、`SLACK_APP_TOKEN`、`SLACK_WEBHOOK_URL` を設定
- [ ] `python scripts/slack_app_server.py` でサーバー起動
