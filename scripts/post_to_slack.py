#!/usr/bin/env python3
"""
初回架電フィードバックを Slack #dk_ra_初回架電fb に投稿するスクリプト
環境変数 SLACK_WEBHOOK_URL を使用（.env で設定）
"""

import os
import sys
import json
from pathlib import Path

# プロジェクトルートをパスに追加
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _load_env():
    """.env を読み込み（dotenv がなくても手動で読み込む）"""
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
        return
    except ImportError:
        pass
    # dotenv がない場合: .env を手動でパース
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())


_load_env()


def post_to_slack(text: str, webhook_url: str | None = None) -> bool:
    """Slackにテキストを投稿する"""
    url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        print("エラー: SLACK_WEBHOOK_URL が設定されていません。.env を確認してください。", file=sys.stderr)
        return False

    # Slackのブロック形式で送信（plain_textで視認性を確保）
    payload = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": text,
                    "emoji": True
                }
            }
        ]
    }

    try:
        import urllib.request
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req) as res:
            if res.status == 200:
                return True
            print(f"エラー: Slack API が {res.status} を返しました", file=sys.stderr)
            return False
    except Exception as e:
        print(f"エラー: Slack投稿に失敗しました - {e}", file=sys.stderr)
        return False


def main():
    if len(sys.argv) > 1:
        # ファイルパスが渡された場合
        filepath = Path(sys.argv[1])
        if not filepath.exists():
            print(f"エラー: ファイルが見つかりません: {filepath}", file=sys.stderr)
            sys.exit(1)
        text = filepath.read_text(encoding="utf-8")
    else:
        # 標準入力から読み取り
        text = sys.stdin.read()

    if not text.strip():
        print("エラー: 投稿する内容が空です", file=sys.stderr)
        sys.exit(1)

    success = post_to_slack(text)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
