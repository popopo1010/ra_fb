#!/usr/bin/env python3
"""
Notta × Zapier Webhook サーバー

使い方:
  python scripts/webhook_server.py
  ngrok http 5000  # 公開
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ra_fb import load_env, generate_feedback_ra, generate_feedback_ca, post_to_slack

load_env()

try:
    from flask import Flask, request, jsonify
except ImportError:
    print("flask がインストールされていません。pip install flask", file=sys.stderr)
    sys.exit(1)

app = Flask(__name__)


@app.route("/webhook/notta", methods=["POST"])
def webhook_notta():
    """
    期待する JSON: { "type": "ra"|"ca", "transcript": "...", "company_name": "...", "ra_name": "..." }
    """
    if os.environ.get("WEBHOOK_SECRET") and request.headers.get("X-Webhook-Secret") != os.environ.get("WEBHOOK_SECRET"):
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    data = request.get_json() or request.form.to_dict() or {}
    transcript = data.get("transcript") or data.get("text") or data.get("content") or data.get("body") or ""
    if isinstance(transcript, dict):
        transcript = transcript.get("plain_text", transcript.get("text", "")) or ""
    transcript = str(transcript).strip()
    if not transcript:
        return jsonify({"ok": False, "error": "transcript が空です"}), 400

    company_name = (data.get("company_name") or data.get("company") or "").strip()
    ra_name = (data.get("ra_name") or data.get("ra") or "").strip()
    fb_type = (data.get("type") or data.get("fb_type") or "ra").lower().strip()
    if fb_type not in ("ra", "ca"):
        fb_type = "ra"

    try:
        if fb_type == "ra":
            full_message = generate_feedback_ra(transcript, ra_name=ra_name, company_name=company_name)
            posted = post_to_slack(full_message, ra_name=ra_name)
        else:
            full_message = generate_feedback_ca(transcript, company_name=company_name)
            url = os.environ.get("SLACK_WEBHOOK_URL_CA") or os.environ.get("SLACK_WEBHOOK_URL")
            posted = post_to_slack(full_message, webhook_url=url)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)[:500]}), 500

    if not posted:
        return jsonify({"ok": False, "error": "Slack 投稿に失敗しました", "feedback_generated": True}), 500

    return jsonify({"ok": True, "message": f"{'RA' if fb_type == 'ra' else 'CA'} FB を Slack に投稿しました"})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "status": "running"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=" * 50)
    print("RA/CA FB Webhook サーバー")
    print("  POST /webhook/notta  GET /health")
    print("=" * 50)
    app.run(host="0.0.0.0", port=port, debug=False)
