# Slack /rafb 全体の流れと漏れチェック

---

## 全体の流れ（図解）

```
【Slack 側】                    【あなたのPC】                 【Slack 側】
                                
1. ユーザーが /rafb を入力  →  2. サーバーがコマンドを受信  →  3. #dk_ra_初回架電fb に投稿
    （Slack）                     （slack_app_server.py）         （Webhook）
                                       ↓
                                 4. フィードバック生成
                                    （generate_feedback.py）
```

**重要**: 2のサーバーが動いていないと、1のコマンドは届かない（dispatch_failed）

---

## やること一覧（順番に）

### フェーズ1: Slack App の設定（api.slack.com）

| # | やること | 場所 | 漏れやすい |
|---|----------|------|------------|
| 1 | アプリ作成 | Create New App → From scratch | - |
| 2 | **ボット名を設定** | **App Home** → Edit | ❌ 忘れると「インストールするボットユーザーがありません」 |
| 3 | Socket Mode を ON | Settings → Socket Mode | - |
| 4 | App-Level Token 発行 | Basic Information の下、App-Level Tokens | ❌ 画面の下にスクロールしないと見つからない |
| 5 | Slash コマンド追加 | Slash Commands → /rafb | - |
| 6 | **Install to Workspace** | **OAuth & Permissions** | ❌ 忘れると Bot Token が表示されない |
| 7 | Bot User OAuth Token をコピー | OAuth & Permissions の上部 | ❌ Install しないと出てこない |

### フェーズ2: .env の設定

| # | 変数 | どこで取る | 状態 |
|---|------|------------|------|
| 1 | SLACK_WEBHOOK_URL | #dk_ra_初回架電fb チャンネル → 連携 → Incoming Webhook | ✅ 済 |
| 2 | SLACK_APP_TOKEN | api.slack.com → Basic Information → App-Level Tokens（xapp-） | ✅ 済 |
| 3 | SLACK_BOT_TOKEN | api.slack.com → OAuth & Permissions → Bot User OAuth Token（xoxb-） | ❌ **未設定** |

### フェーズ3: チャンネルにアプリを追加

| # | やること | 漏れやすい |
|---|----------|------------|
| 1 | /rafb を使うチャンネルにアプリを追加 | ❌ インストールしただけでは使えない。チャンネルごとに追加が必要 |

**やり方**: チャンネルで `/invite @RA初回架電FB` または チャンネル設定 → アプリを追加

### フェーズ4: サーバー起動

| # | やること |
|---|----------|
| 1 | ターミナルで `source venv/bin/activate` |
| 2 | `python scripts/slack_app_server.py` を実行 |
| 3 | **ターミナルを閉じない**（閉じるとサーバーが止まる） |

---

## 漏れやすいところ（チェックリスト）

### Slack App 側（api.slack.com）

- [ ] **App Home** で Display Name と Default username を設定したか
- [ ] **Install to Workspace** を実行したか（しないと Bot Token が取れない）
- [ ] **OAuth & Permissions** の**ページ上部**で Bot User OAuth Token をコピーしたか
- [ ] App-Level Token は **Basic Information** の下にスクロールして見つけたか

### .env 側

- [ ] SLACK_BOT_TOKEN（xoxb-）を追加したか ← **いまここが未設定**
- [ ] トークンの前後に余計なスペースや改行がないか
- [ ] 値が「"」で囲まれていないか（正: `xoxb-xxx` / 誤: `"xoxb-xxx"`）

### Slack チャンネル側

- [ ] /rafb を使うチャンネルにアプリを追加したか
- [ ] #dk_ra_初回架電fb に Incoming Webhook が設定されているか（投稿先）

### ローカル側

- [ ] `source venv/bin/activate` で venv を有効化したか
- [ ] **サーバー起動中に /rafb を実行したか**（サーバーが止まっていると dispatch_failed）
- [ ] ターミナルを閉じていないか（閉じるとサーバーが止まる）

---

## dispatch_failed が出る場合

**ほぼ確実にサーバーが動いていません。**

1. ターミナルを開く
2. `cd /Users/ikeobook15/RA_FBシステム`
3. `source venv/bin/activate`
4. `python scripts/slack_app_server.py`
5. **このターミナルを閉じずに起動したまま**にする
6. Slack で `/rafb` を試す

---

## いまやること（SLACK_BOT_TOKEN が未設定の場合）

**SLACK_BOT_TOKEN を .env に追加する**

1. [api.slack.com/apps](https://api.slack.com/apps) を開く
2. 対象アプリをクリック
3. 左メニュー **OAuth & Permissions**
4. ページ**上部**の **OAuth Tokens for Your Workspace**
5. **Bot User OAuth Token** の **Copy** をクリック
6. `.env` を開き、次の行を追加（ペーストした値に置き換え）:
   ```
   SLACK_BOT_TOKEN=xoxb-ここにペースト
   ```
7. 保存

その後、ターミナルで:

```bash
cd /Users/ikeobook15/RA_FBシステム
source venv/bin/activate
python scripts/slack_app_server.py
```

サーバーが起動したら、Slack で `/rafb references/long_calls/小山田/SANKEI_BLDG_小山田_001.md` を試す。
