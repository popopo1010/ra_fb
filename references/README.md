# 参照資料

RA/CA FB 生成で参照するマニュアル・ガイドを格納。

## ディレクトリ構成

```
references/
├── manual/                    # 架電マニュアル・PSS・チェックリスト・商談前リサーチ
│   ├── 営業新規架電マニュアル.md
│   ├── 事前商談前リサーチ.md
│   ├── PSS_プロフェッショナルセリングスキル.md
│   └── 初回面談_確認チェックリスト.md
└── candidate_attract/         # 候補者アトラクト（会社の魅力の伝え方）
    ├── recruitment-playbook.md
    └── market_segments.py     # マーケットセグメント定義（工種×用途）
```

## データの場所

| 種別 | パス |
|------|------|
| 入力（RA） | `data/input/ra/` |
| 入力（CA） | `data/input/ca/` |
| 出力（法人マスタ） | `data/output/法人マスタ/` |

## FB 生成での参照

| 種別 | 参照ファイル |
|------|--------------|
| RA | manual, pss, checklist, reception, kadai, attract |
| CA | template（data/input/ca/_template_議事録.md）, manual |
