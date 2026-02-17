#!/usr/bin/env python3
"""
法人マスタの不足項目（企業スナップショット、前職規模別USP、採用意思決定者、
休日数・直行直帰・リモート、口コミ評価傾向）をWeb検索で補完。

FBにない情報をリサーチして追加する。既存の法人マスタを一括補完可能。

使い方:
  python scripts/supplement_company_research.py              # 全法人マスタを補完
  python scripts/supplement_company_research.py 会社名         # 指定会社のみ
  python scripts/supplement_company_research.py --dry-run      # 補完対象のみ表示、更新しない
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ra_fb import load_env, supplement_company_master_from_research
from ra_fb.config import MASTER_DIR
from ra_fb.company import _needs_supplement

load_env()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="法人マスタの不足項目をWeb検索で補完")
    parser.add_argument("company", nargs="?", help="会社名（省略時は全件）")
    parser.add_argument("--dry-run", action="store_true", help="補完対象のみ表示、更新しない")
    args = parser.parse_args()

    if not MASTER_DIR.exists():
        print("法人マスタディレクトリがありません。", file=sys.stderr)
        sys.exit(1)

    targets = []
    if args.company:
        path = MASTER_DIR / f"{args.company}.md"
        if not path.exists():
            # ファイル名に_が含まれる場合など
            for f in MASTER_DIR.glob("*.md"):
                if args.company in f.stem and not f.name.startswith("_"):
                    path = f
                    break
        if path.exists():
            targets.append(path)
        else:
            print(f"該当する法人マスタが見つかりません: {args.company}", file=sys.stderr)
            sys.exit(1)
    else:
        for f in MASTER_DIR.glob("*.md"):
            if f.name.startswith("_") or f.name in ("マスタ項目一覧.md", "README.md"):
                continue
            try:
                text = f.read_text(encoding="utf-8")
                if not text.strip().startswith("---"):
                    continue
                parts = text.split("---", 2)
                if len(parts) < 3:
                    continue
                body = parts[2].strip()
                if _needs_supplement(body):
                    targets.append(f)
            except Exception:
                continue

    if not targets:
        print("補完が必要な法人マスタはありません。", file=sys.stderr)
        return

    print(f"補完対象: {len(targets)} 件", file=sys.stderr)
    for t in targets:
        print(f"  - {t.stem}", file=sys.stderr)

    if args.dry_run:
        print("\n--dry-run のため更新しません。", file=sys.stderr)
        return

    updated = 0
    for path in targets:
        result = supplement_company_master_from_research(path)
        if result:
            updated += 1
            print(f"✅ 補完: {path.stem}", file=sys.stderr)
        else:
            print(f"⚠️ スキップ（検索結果なし or エラー）: {path.stem}", file=sys.stderr)

    print(f"\n完了: {updated}/{len(targets)} 件を更新", file=sys.stderr)


if __name__ == "__main__":
    main()
