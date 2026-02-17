#!/usr/bin/env python3
"""
過去の文字起こしから法人マスタを一括生成

使い方:
  python scripts/bulk_import_company.py                    # 全件
  python scripts/bulk_import_company.py --dry-run          # 実行せず一覧のみ
  python scripts/bulk_import_company.py --ra-only          # long_calls（RA）のみ
  python scripts/bulk_import_company.py --ca-only          # 法人面談議事録（CA）のみ
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ra_fb import load_env, extract_ra_from_path, extract_company_name, extract_and_save_company_info
from ra_fb.config import LONG_CALLS_DIR, CA_DIR

load_env()


def _collect_ra_files() -> list[tuple[Path, str, str]]:
    """long_calls から RA 用ファイルを収集。(path, company_name, "ra")"""
    results = []
    base = LONG_CALLS_DIR
    for d in ["茂野", "小山田"]:
        dir_path = base / d
        if not dir_path.exists():
            continue
        for f in dir_path.glob("*.md"):
            if f.name.startswith("_") or f.name.lower() == "readme.md":
                continue
            ra_name = extract_ra_from_path(f)
            company_name = extract_company_name(f.stem, ra_name)
            if company_name:
                results.append((f, company_name, "ra"))
    return results


def _collect_ca_files() -> list[tuple[Path, str, str]]:
    """法人面談議事録から CA 用ファイルを収集。(path, company_name, "ca")"""
    results = []
    base = CA_DIR
    if not base.exists():
        return results
    for f in base.glob("*.md"):
        if f.name.startswith("_") or f.name.lower() == "readme.md":
            continue
        stem = f.stem
        if stem.endswith("_議事録"):
            company_name = stem[:-4]  # 議事録 を除去
        else:
            company_name = stem
        if company_name:
            results.append((f, company_name, "ca"))
    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="過去の文字起こしから法人マスタを一括生成")
    parser.add_argument("--dry-run", action="store_true", help="実行せず一覧のみ表示")
    parser.add_argument("--ra-only", action="store_true", help="long_calls（RA）のみ")
    parser.add_argument("--ca-only", action="store_true", help="法人面談議事録（CA）のみ")
    parser.add_argument("--no-research", action="store_true", help="事業リサーチ（Web検索）をスキップ")
    args = parser.parse_args()

    files = []
    if not args.ca_only:
        files.extend(_collect_ra_files())
    if not args.ra_only:
        files.extend(_collect_ca_files())

    if not files:
        print("対象ファイルがありません。", file=sys.stderr)
        sys.exit(0)

    print(f"対象: {len(files)} 件", file=sys.stderr)
    for i, (path, company, stype) in enumerate(files, 1):
        print(f"  {i}. {company} ({stype}) <- {path.name}", file=sys.stderr)

    if args.dry_run:
        print("\n--dry-run のため実行しません。", file=sys.stderr)
        return

    for path, company_name, source_type in files:
        try:
            transcript = path.read_text(encoding="utf-8")
            saved = extract_and_save_company_info(
                transcript,
                company_name=company_name,
                source_type=source_type,
                use_research=not args.no_research,
            )
            if saved:
                print(f"✅ {company_name}: {saved.name}")
            else:
                print(f"⚠️ {company_name}: 抽出失敗")

        except Exception as e:
            print(f"❌ {company_name}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
