#!/usr/bin/env python3
"""
都道府県×セグメントで法人を比較

使い方:
  python scripts/compare_companies.py 愛知 電気系
  python scripts/compare_companies.py 東京 DC
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ra_fb import load_env, compare_companies

load_env()


def main():
    if len(sys.argv) < 3:
        print("使い方: python scripts/compare_companies.py <都道府県> <セグメント>", file=sys.stderr)
        print("例: python scripts/compare_companies.py 愛知 電気系", file=sys.stderr)
        print("", file=sys.stderr)
        print("セグメント例: 電気系, 土木, 建築, 管工事, DC, 再エネ, 物流, 工場, オフィス, 公共, 住宅", file=sys.stderr)
        sys.exit(1)

    prefecture = sys.argv[1]
    segment = sys.argv[2]
    result = compare_companies(prefecture, segment)
    print(result)


if __name__ == "__main__":
    main()
