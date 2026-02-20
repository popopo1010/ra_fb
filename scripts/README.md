# Scripts

## メイン

| スクリプト | 用途 |
|------------|------|
| `slack_server.py` | Slack /rafb_call, /rafb_mtg, ファイルアップロード。**通常はこれを起動** |
| `webhook_server.py` | Notta × Zapier Webhook 受信 |
| `cli.py` | RA/CA FB 生成 CLI。`ra <ファイル>` / `ca <ファイル>` |
| `compare_companies.py` | 都道府県×セグメントで法人比較。`愛知 電気系` 等 |
| `bulk_import_company.py` | 過去の文字起こしから法人マスタを一括生成 |
| `update_playbook.py` | 法人マスタからマーケット成長性・事業戦略を抽出し、アトラクトプレイブックに追記 |
| `supplement_company_research.py` | 法人マスタの不足項目（企業スナップショット等）をWeb検索で補完 |
| `migrate_company_master.py` | 既存法人マスタを新構造（企業情報統合、候補者別訴求統合）に移行 |

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
python scripts/update_playbook.py                  # 法人マスタ→プレイブック「法人別事例」セクション更新
python scripts/supplement_company_research.py      # 法人マスタの不足項目をWeb検索で補完
python scripts/migrate_company_master.py          # 既存法人マスタを新構造に移行（過去データの一括更新）
```
