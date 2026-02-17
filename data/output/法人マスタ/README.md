# 法人マスタ

FB 生成時に文字起こしから抽出した法人情報を格納。**都道府県×セグメント**で比較・差別化に活用。

## マスタ項目一覧

→ **[マスタ項目一覧.md](マスタ項目一覧.md)** を参照

## 比較の軸

- **都道府県**: 愛知、岐阜、東京、大阪 等
- **セグメント**: 電気系、土木、建築、管工事、DC、再エネ、物流、工場、オフィス、公共、住宅

## ファイル形式

- `{会社名}.md` … 1社1ファイル
- 先頭に YAML frontmatter（都道府県・セグメント）必須
- FB を出すたびに自動で抽出・更新

## 構造（v2・重複排除）

- **企業情報**: 基本情報・事業リサーチ・企業スナップショットを1セクションに統合
- **候補者別訴求**: 資格・経験軸と前職規模軸を1テーブルに統合
- **差別化メモ**: 他社との違いに特化（企業の一般論は書かない）

## 比較コマンド

```bash
python scripts/compare_companies.py 愛知 電気系
python scripts/compare_companies.py 東京 DC
```

## 過去データの一括取り込み

再アップロード不要。既存の文字起こしから法人マスタを一括生成。**事業リサーチ（Web検索）** も自動で実行される。

```bash
# 仮想環境を有効化（推奨）
source .venv/bin/activate   # または venv/bin/activate

python scripts/bulk_import_company.py --dry-run   # 予覧
python scripts/bulk_import_company.py              # 実行（全46件、リサーチ付き）
python scripts/bulk_import_company.py --no-research # リサーチをスキップして高速実行
```

- `.env` に `ANTHROPIC_API_KEY` を設定すること
- `duckduckgo-search` が未インストールの場合は `pip install -r requirements.txt`

## 不足項目の補完

FBにない項目（企業スナップショット、前職規模別USP等）をWeb検索で補完。

```bash
python scripts/supplement_company_research.py              # 全件補完
python scripts/supplement_company_research.py 会社名       # 指定会社のみ
python scripts/supplement_company_research.py --dry-run    # 補完対象のみ表示
```

## 候補者タイプ

1. 電気工事士もち、電気施工管理未経験
2. 施工管理資格もち、マネジメント（現場監督）経験なし
3. 施工管理資格もち、マネジメント（現場監督）経験あり
