"""Slack 投稿"""

import json
import os
import sys
import urllib.request

from .config import load_env

load_env()

SLACK_TEXT_LIMIT = 3000


def _chunk_text(text: str, limit: int = SLACK_TEXT_LIMIT) -> list[str]:
    """長文をSlack制限内で分割"""
    if len(text) <= limit:
        return [text]
    chunks = []
    while text:
        chunk = text[:limit]
        last_nl = chunk.rfind("\n")
        if last_nl > limit // 2:
            chunk, text = chunk[: last_nl + 1], text[last_nl + 1 :]
        else:
            text = text[limit:]
        chunks.append(chunk)
    return chunks


def _post_to_webhook(url: str, text: str) -> bool:
    """指定Webhookに投稿"""
    chunks = _chunk_text(text)
    payload = {
        "blocks": [
            {"type": "section", "text": {"type": "plain_text", "text": c, "emoji": True}}
            for c in chunks
        ]
    }
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as res:
            return res.status == 200
    except Exception as e:
        print(f"Slack投稿エラー: {e}", file=sys.stderr)
        return False


def post_to_slack(
    text: str,
    webhook_url: str | None = None,
    ra_name: str = "",
) -> bool:
    """Slackに投稿。ra_name 指定時は個別Webhookにも投稿"""
    url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        print("エラー: SLACK_WEBHOOK_URL が設定されていません。.env を確認してください。", file=sys.stderr)
        return False

    if not _post_to_webhook(url, text):
        return False

    if ra_name:
        key = f"SLACK_WEBHOOK_URL_{ra_name}"
        individual_url = os.environ.get(key)
        if individual_url:
            _post_to_webhook(individual_url, text)

    return True
