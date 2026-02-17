# Scripts

## メイン

| スクリプト | 用途 |
|------------|------|
| `slack_server.py` | Slack /rafb, /fb, ファイルアップロード。**通常はこれを起動** |
| `webhook_server.py` | Notta × Zapier Webhook 受信 |
| `cli.py` | RA/CA FB 生成 CLI。`ra <ファイル>` / `ca <ファイル>` |

## 後方互換

| スクリプト | 実体 |
|------------|------|
| `generate_feedback.py` | cli.py ra のエイリアス |
| `slack_app_server.py` | slack_server.py のエイリアス |

## 起動例

```bash
python scripts/slack_server.py
python scripts/cli.py ra references/long_calls/茂野/TOKAI_EC_茂野_016.md
```
