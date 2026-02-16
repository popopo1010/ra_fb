#!/usr/bin/env python3
"""
Slack /rafb ・ /fb サーバー（Socket Mode）

使い方:
  python scripts/slack_server.py
"""

import os
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ra_fb import (
    load_env,
    extract_ra_from_filename,
    extract_company_name,
    generate_feedback_ra,
    generate_feedback_ca,
    post_to_slack,
)

load_env()

try:
    from slack_bolt import App
    from slack_bolt.adapter.socket_mode import SocketModeHandler
except ImportError:
    print("slack_bolt がインストールされていません。pip install slack_bolt", file=sys.stderr)
    sys.exit(1)

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
    print("エラー: .env に SLACK_BOT_TOKEN と SLACK_APP_TOKEN を設定してください", file=sys.stderr)
    sys.exit(1)

app = App(token=SLACK_BOT_TOKEN)


def _download_slack_file(client, file_id: str) -> tuple[str | None, str | None, str | None, str]:
    """Slack ファイルをダウンロード。戻り値: (text, channel_id, user_id, filename)"""
    try:
        resp = client.files_info(file=file_id)
        if not resp.get("ok"):
            return None, None, None, ""
        f = resp.get("file", {})
        mimetype = (f.get("mimetype") or "").lower()
        name = (f.get("name") or "").lower()
        if not ("text/" in mimetype or mimetype == "application/octet-stream" or name.endswith((".txt", ".md"))):
            return None, None, None, ""
        url = f.get("url_private_download")
        if not url:
            return None, None, None, ""
        import urllib.request
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"})
        with urllib.request.urlopen(req, timeout=30) as r:
            text = r.read().decode("utf-8", errors="replace")
        chs = f.get("channels") or []
        return text, chs[0] if chs else None, f.get("user"), f.get("name") or ""
    except Exception:
        return None, None, None, ""


def _open_ra_modal(client, trigger_id: str, channel_id: str = ""):
    view = {
        "type": "modal",
        "callback_id": "rafb_modal",
        "title": {"type": "plain_text", "text": "初回架電FB"},
        "submit": {"type": "plain_text", "text": "送信"},
        "blocks": [
            {"type": "input", "block_id": "transcript", "element": {"type": "plain_text_input", "action_id": "t", "multiline": True, "placeholder": {"type": "plain_text", "text": "文字起こしを貼り付け"}}, "label": {"type": "plain_text", "text": "文字起こし"}},
            {"type": "input", "block_id": "company", "element": {"type": "plain_text_input", "action_id": "c", "placeholder": {"type": "plain_text", "text": "例: TOKAI_EC"}}, "label": {"type": "plain_text", "text": "会社名"}, "optional": True},
            {"type": "input", "block_id": "ra", "element": {"type": "static_select", "action_id": "r", "placeholder": {"type": "plain_text", "text": "RA担当"}, "options": [{"text": {"type": "plain_text", "text": "未選択"}, "value": "_none"}, {"text": {"type": "plain_text", "text": "小山田"}, "value": "小山田"}, {"text": {"type": "plain_text", "text": "茂野"}, "value": "茂野"}]}, "label": {"type": "plain_text", "text": "RA担当"}, "optional": True},
        ],
    }
    if channel_id:
        view["private_metadata"] = channel_id
    client.views_open(trigger_id=trigger_id, view=view)


def _open_ca_modal(client, trigger_id: str, channel_id: str = ""):
    view = {
        "type": "modal",
        "callback_id": "cafb_modal",
        "title": {"type": "plain_text", "text": "CA FB（法人面談）"},
        "submit": {"type": "plain_text", "text": "送信"},
        "blocks": [
            {"type": "input", "block_id": "transcript", "element": {"type": "plain_text_input", "action_id": "t", "multiline": True, "placeholder": {"type": "plain_text", "text": "法人面談の文字起こし"}}, "label": {"type": "plain_text", "text": "文字起こし"}},
            {"type": "input", "block_id": "company", "element": {"type": "plain_text_input", "action_id": "c", "placeholder": {"type": "plain_text", "text": "例: サンケイビル"}}, "label": {"type": "plain_text", "text": "会社名"}, "optional": True},
        ],
    }
    if channel_id:
        view["private_metadata"] = channel_id
    client.views_open(trigger_id=trigger_id, view=view)


def _get_modal_values(values: dict, block_id: str, action_id: str) -> str:
    el = values.get(block_id, {}).get(action_id, {})
    val = (el.get("value") if isinstance(el, dict) else "") or ""
    return str(val).strip()


@app.command("/rafb")
def cmd_rafb(ack, body, client, command):
    ack()
    _open_ra_modal(client, body["trigger_id"], command.get("channel_id", ""))


@app.command("/fb")
def cmd_fb(ack, body, client, command):
    ack()
    _open_ca_modal(client, body["trigger_id"], command.get("channel_id", ""))


@app.view("rafb_modal")
def view_rafb(ack, body, client, view):
    ack()
    v = view.get("state", {}).get("values", {})
    transcript = _get_modal_values(v, "transcript", "t")
    company_name = _get_modal_values(v, "company", "c")
    ra_val = _get_modal_values(v, "ra", "r")
    ra_name = "" if (not ra_val or ra_val == "_none") else ra_val
    if not transcript:
        return

    user_id = body.get("user", {}).get("id", "")
    channel_id = view.get("private_metadata") or ""
    if user_id and channel_id:
        try:
            client.chat_postEphemeral(channel=channel_id, user=user_id, text="処理中です。完了次第 #dk_ra_初回架電fb に投稿します。")
        except Exception:
            pass

    def _do():
        msg = generate_feedback_ra(transcript, ra_name=ra_name, company_name=company_name)
        post_to_slack(msg, ra_name=ra_name)

    threading.Thread(target=_do, daemon=True).start()


@app.view("cafb_modal")
def view_cafb(ack, body, client, view):
    ack()
    v = view.get("state", {}).get("values", {})
    transcript = _get_modal_values(v, "transcript", "t")
    company_name = _get_modal_values(v, "company", "c")
    if not transcript:
        return

    user_id = body.get("user", {}).get("id", "")
    channel_id = view.get("private_metadata") or ""
    if user_id and channel_id:
        try:
            client.chat_postEphemeral(channel=channel_id, user=user_id, text="処理中です。完了次第 CA FB チャンネルに投稿します。")
        except Exception:
            pass

    def _do():
        msg = generate_feedback_ca(transcript, company_name=company_name)
        url = os.environ.get("SLACK_WEBHOOK_URL_CA") or SLACK_WEBHOOK_URL
        post_to_slack(msg, webhook_url=url)

    threading.Thread(target=_do, daemon=True).start()


@app.event("file_shared")
def evt_file_shared(event, client):
    file_id = event.get("file_id")
    if not file_id:
        return
    text, ch, uid, fname = _download_slack_file(client, file_id)
    if not text or not text.strip():
        return

    ra_name = extract_ra_from_filename(fname)
    company_name = extract_company_name(Path(fname).stem if fname else "", ra_name)
    channel_id = event.get("channel_id") or ch or ""
    user_id = event.get("user_id") or uid or ""

    if user_id and channel_id:
        try:
            client.chat_postEphemeral(channel=channel_id, user=user_id, text="テキストファイルを検出しました。処理中です。")
        except Exception:
            pass

    def _do():
        msg = generate_feedback_ra(text, ra_name=ra_name, company_name=company_name)
        post_to_slack(msg, ra_name=ra_name)

    threading.Thread(target=_do, daemon=True).start()


if __name__ == "__main__":
    print("=" * 50)
    print("RA FB サーバー起動")
    print("Slack: /rafb（RA） /fb（CA）")
    if not SLACK_WEBHOOK_URL:
        print("⚠️ SLACK_WEBHOOK_URL が未設定です")
    print("=" * 50)
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
