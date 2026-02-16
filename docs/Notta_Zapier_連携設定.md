# Notta × Zapier × RAFB 連携設定

Notta で録音・文字起こし → Zapier で自動トリガー → RAFB が FB 生成 → Slack に投稿

---

## 1. 全体フロー

```
Notta（録音・文字起こし完了）
    ↓ トリガー
Zapier
    ↓ Webhook POST（type=ra または type=ca）
RAFB Webhook サーバー（/webhook/notta）
    ↓ type で分岐
    ├─ RA (type=ra) → 初回架電FB → #dk_ra_初回架電fb
    └─ CA (type=ca) → 法人面談FB → SLACK_WEBHOOK_URL_CA のチャンネル
```

---

## 2. RAFB Webhook サーバーの起動

### ローカルで起動

```bash
cd RA_FBシステム
source venv/bin/activate  # または python -m venv venv && source venv/bin/activate
pip install flask
python scripts/webhook_server.py
```

→ `http://localhost:5000` で待ち受け

### 公開する（Zapier から叩けるようにする）

**ngrok を使う場合:**

```bash
ngrok http 5000
```

→ `https://xxxx.ngrok.io` のような URL が発行される

**本番運用:** AWS / GCP / Heroku 等にデプロイし、常時起動させる

---

## 3. Zapier の設定

### Step 1: Zap を作成

1. [Zapier](https://zapier.com) にログイン
2. **Create Zap** をクリック

### Step 2: トリガー（Notta）

1. **Trigger**: Notta を検索して選択
2. トリガー例:
   - **New AI Notes**（AI ノート生成時）
   - **New Recording**（録音完了時）
   - 利用可能なトリガーは Notta 連携画面で確認
3. Notta アカウントを接続
4. テストして、文字起こしテキストが取得できることを確認

### Step 3: アクション（Webhooks by Zapier）

1. **Action**: **Webhooks by Zapier** を選択
2. **Action Event**: **POST**
3. **URL**: `https://あなたのURL/webhook/notta`
   - 例: `https://xxxx.ngrok.io/webhook/notta`
4. **Payload Type**: JSON
5. **Data** に以下をマッピング:

| Key | Value（Zapier のフィールド） | 必須 |
|-----|------------------------------|------|
| **type** | `ra` または `ca` | **必須** |
| transcript | Notta の「文字起こしテキスト」や「Transcript」など | 必須 |
| company_name | 固定値 or 手動入力（任意） | 任意 |
| ra_name | 固定値 or 手動入力（type=ra 時、任意: 小山田, 大城, 茂野, 重野） | 任意 |

**type の分岐:**
- **ra** → 初回架電FB（/rafb）。#dk_ra_初回架電fb に投稿
- **ca** → 法人面談FB（/fb）。SLACK_WEBHOOK_URL_CA のチャンネルに投稿

**Zapier で RA/CA を分ける方法:**
- **方法A**: Zap を2つ作る（RA 用・CA 用）。それぞれ type を固定値に設定
- **方法B**: Notta のフォルダやワークスペースで分けている場合、Zapier のフィルターで type を切り替え
- **方法C**: 1つの Zap で、フォームで「RA/CA」を選択して type にマッピング

※ Notta の出力フィールド名は Zapier のテスト実行で確認してください。

### Step 4: 認証（任意）

`.env` に `WEBHOOK_SECRET=あなたの秘密の文字列` を設定した場合:

- Zapier の **Headers** に追加:
  - Key: `X-Webhook-Secret`
  - Value: `あなたの秘密の文字列`

---

## 4. Webhook が受け取る JSON 形式

```json
{
  "type": "ra",
  "transcript": "文字起こしの全文（必須）",
  "company_name": "TOKAI_EC（任意）",
  "ra_name": "小山田（任意、type=ra 時）"
}
```

| type | 処理 | 投稿先 |
|------|------|--------|
| ra | 初回架電FB | SLACK_WEBHOOK_URL（#dk_ra_初回架電fb） |
| ca | 法人面談FB | SLACK_WEBHOOK_URL_CA（未設定時は SLACK_WEBHOOK_URL） |

**.env に CA 用の Webhook を追加する場合:**
```
SLACK_WEBHOOK_URL_CA=https://hooks.slack.com/services/xxx/yyy/zzz
```

Notta / Zapier のフィールド名が異なる場合、`webhook_server.py` で `text` や `content` などにも対応しています。

---

## 5. トラブルシュート

| 現象 | 確認すること |
|------|--------------|
| Zapier から 404 | URL が `/webhook/notta` で終わっているか |
| 401 Unauthorized | WEBHOOK_SECRET と Zapier の Header が一致しているか |
| transcript が空 | Zapier のテストで Notta のどのフィールドに文字起こしが入っているか確認 |
| Slack に投稿されない | .env の SLACK_WEBHOOK_URL（RA） / SLACK_WEBHOOK_URL_CA（CA）を確認 |
| RA なのに CA が動く | Zapier の Data で type が `ra` になっているか確認 |

---

## 6. 更新履歴

| 日付 | 内容 |
|------|------|
| 2025-02-13 | 初版。Webhook サーバー・Zapier 設定手順 |
