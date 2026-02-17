#!/usr/bin/env python3
"""
法人マスタからマーケット成長性・事業戦略を抽出し、
アトラクトプレイブックに「法人別事例」セクションを追加・更新。

使い方:
  python scripts/update_playbook.py
  python scripts/update_playbook.py --dry-run   # 更新せず抽出結果のみ表示
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ra_fb import load_env, update_playbook_from_masters, collect_attract_examples_from_masters

load_env()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="法人マスタからプレイブックを更新")
    parser.add_argument("--dry-run", action="store_true", help="更新せず抽出結果のみ表示")
    args = parser.parse_args()

    examples = collect_attract_examples_from_masters()
    if not examples:
        print("抽出できる法人がありません。法人マスタを確認してください。", file=sys.stderr)
        sys.exit(0)

    print(f"抽出: {len(examples)} 社", file=sys.stderr)
    for ex in examples[:5]:
        print(f"  - {ex['company_name']}: {ex['growth'][:50]}...", file=sys.stderr)
    if len(examples) > 5:
        print(f"  ... 他 {len(examples) - 5} 社", file=sys.stderr)

    if args.dry_run:
        print("\n--dry-run のためプレイブックは更新しません。", file=sys.stderr)
        return

    path = update_playbook_from_masters()
    if path:
        print(f"\n✅ プレイブックを更新: {path}", file=sys.stderr)
    else:
        print("\n⚠️ プレイブックの更新に失敗しました。", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
