# Slack /rafb と /fb コマンドの設定

## 概要

| コマンド | 用途 | 投稿先 |
|----------|------|--------|
| **/rafb** | 初回架電FB（RA） | #dk_ra_初回架電fb |
| **/fb** | 法人面談FB（CA） | SLACK_WEBHOOK_URL_CA のチャンネル |

## Slack App に /fb を追加する

1. [Slack API](https://api.slack.com/apps) で対象アプリを開く
2. **Slash Commands** → **Create New Command**
3. 以下を設定:
   - **Command**: `/fb`
   - **Request URL**: （Socket Mode の場合は空でOK。Socket Mode で自動処理）
   - **Short Description**: `法人面談FBを生成`
   - **Usage Hint**: `文字起こしを貼り付けてCA向けFBを生成`

4. **Save**

※ /rafb が既に登録済みであれば、同様に /fb を追加するだけです。

## .env の設定

CA 用に別チャンネルへ投稿する場合:

```
SLACK_WEBHOOK_URL_CA=https://hooks.slack.com/services/xxx/yyy/zzz
```

未設定の場合は SLACK_WEBHOOK_URL（RA 用）に投稿されます。
