# Slack 個別連携（RA別チャンネル投稿）

## 概要

RA ごとに専用チャンネルへ FB を投稿できます。共通チャンネル（#dk_ra_初回架電fb）と個別チャンネルの**両方**に投稿されます。

## 設定方法

`.env` に RA 名に対応する Webhook URL を追加:

```
# 共通（必須）
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/yyy/zzz

# 個別（任意）
SLACK_WEBHOOK_URL_小山田=https://hooks.slack.com/services/aaa/bbb/ccc
SLACK_WEBHOOK_URL_茂野=https://hooks.slack.com/services/ddd/eee/fff
# ※ 茂野・重野・大城は同一人物。茂野に統一
```

## RA 名の指定方法

| 入力方法 | RA の指定 |
|----------|------------|
| **/rafb モーダル** | モーダルの「RA」プルダウンで選択 |
| **ファイルアップロード** | ファイル名に RA 名を含める（例: `ZENITAKA_小山田_002.md`） |
| **CLI** | ファイルパスに RA 名を含める（例: `references/long_calls/小山田/xxx.md`） |

## 動作

- `SLACK_WEBHOOK_URL_<RA名>` が設定されている場合、その RA の FB は共通チャンネル＋個別チャンネルに投稿
- 未設定の RA は共通チャンネルのみに投稿
