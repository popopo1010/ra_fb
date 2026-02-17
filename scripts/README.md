# Scripts

## メイン

| スクリプト | 用途 |
|------------|------|
| `slack_server.py` | Slack /rafb, /fb, ファイルアップロード。**通常はこれを起動** |
| `webhook_server.py` | Notta × Zapier Webhook 受信 |
| `cli.py` | RA/CA FB 生成 CLI。`ra <ファイル>` / `ca <ファイル>` |
| `compare_companies.py` | 都道府県×セグメントで法人比較。`愛知 電気系` 等 |
| `bulk_import_company.py` | 過去の文字起こしから法人マスタを一括生成 |

## 後方互換

| スクリプト | 実体 |
|------------|------|
| `generate_feedback.py` | cli.py ra のエイリアス |
| `slack_app_server.py` | slack_server.py のエイリアス |

## 起動例

```bash
python scripts/slack_server.py
python scripts/cli.py ra data/input/ra/茂野/TOKAI_EC_茂野_016.md
python scripts/compare_companies.py 愛知 電気系
python scripts/bulk_import_company.py --dry-run   # 過去文字起こしから法人マスタ一括生成（予覧）
python scripts/bulk_import_company.py             # 実行
```
