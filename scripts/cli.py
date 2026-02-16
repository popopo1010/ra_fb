#!/usr/bin/env python3
"""
RA/CA FB 生成 CLI

使い方:
  python scripts/cli.py ra references/long_calls/茂野/TOKAI_EC_茂野_016.md
  python scripts/cli.py ca path/to/transcript.md --no-slack
"""

import os
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ra_fb import (
    load_env,
    extract_ra_from_path,
    extract_company_name,
    generate_feedback_ra,
    generate_feedback_ca,
    post_to_slack,
)

load_env()


def main():
    parser = argparse.ArgumentParser(description="RA/CA FB 生成＆Slack投稿")
    parser.add_argument("type", choices=["ra", "ca"], help="ra=初回架電, ca=法人面談")
    parser.add_argument("transcript", type=Path, help="文字起こしファイル")
    parser.add_argument("--no-slack", action="store_true", help="Slackに送らない")
    parser.add_argument("--no-ai", action="store_true", help="AIを使わずテンプレートのみ")
    parser.add_argument("--ra-name", type=str, default="", help="RA名（type=ra時）")
    parser.add_argument("--company-name", type=str, default="", help="会社名")
    args = parser.parse_args()

    if not args.transcript.exists():
        print(f"エラー: ファイルが見つかりません: {args.transcript}", file=sys.stderr)
        sys.exit(1)

    transcript = args.transcript.read_text(encoding="utf-8")
    ra_name = args.ra_name or (extract_ra_from_path(args.transcript) if args.type == "ra" else "")
    company_name = args.company_name or extract_company_name(args.transcript.stem, ra_name)

    if args.type == "ra":
        full_message = generate_feedback_ra(
            transcript, ra_name=ra_name, company_name=company_name, use_ai=not args.no_ai
        )
    else:
        full_message = generate_feedback_ca(
            transcript, company_name=company_name, use_ai=not args.no_ai
        )

    print(full_message)

    if not args.no_slack:
        if args.type == "ra":
            success = post_to_slack(full_message, ra_name=ra_name)
        else:
            url = os.environ.get("SLACK_WEBHOOK_URL_CA") or os.environ.get("SLACK_WEBHOOK_URL")
            success = post_to_slack(full_message, webhook_url=url)

        if success:
            ch = "CA FB" if args.type == "ca" else "#dk_ra_初回架電fb"
            print(f"\n✅ {ch} に投稿しました", file=sys.stderr)
        else:
            print("\n❌ Slack投稿に失敗しました", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
