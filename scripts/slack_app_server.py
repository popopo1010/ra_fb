#!/usr/bin/env python3
"""
Slack Slash コマンド /rafb 用サーバー（Socket Mode = ngrok 不要）

使い方:
  1. Slack App で Socket Mode を有効化し、App-Level Token を発行
  2. .env に SLACK_BOT_TOKEN と SLACK_APP_TOKEN を設定
  3. python3 scripts/slack_app_server.py を実行するだけ
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# .env 読み込み
def _load_env():
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())


_load_env()

try:
    from slack_bolt import App
    from slack_bolt.adapter.socket_mode import SocketModeHandler
except ImportError:
    print("slack_bolt がインストールされていません。", file=sys.stderr)
    print("", file=sys.stderr)
    print("対処法:", file=sys.stderr)
    print("  1. ./setup.sh を実行して venv を作成", file=sys.stderr)
    print("  2. source venv/bin/activate で有効化", file=sys.stderr)
    print("  3. python scripts/slack_app_server.py を再実行", file=sys.stderr)
    sys.exit(1)

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
    print("エラー: .env に SLACK_BOT_TOKEN と SLACK_APP_TOKEN を設定してください", file=sys.stderr)
    sys.exit(1)

app = App(token=SLACK_BOT_TOKEN)


def run_feedback_from_text(transcript_text: str) -> tuple[str, bool]:
    """貼り付けた文字起こしからフィードバックを生成"""
    import subprocess
    import tempfile
    script_path = ROOT / "scripts" / "generate_feedback.py"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(transcript_text)
        tmp_path = f.name
    try:
        result = subprocess.run(
            [sys.executable, str(script_path), tmp_path, "--no-slack"],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            timeout=60,
        )
        if result.returncode != 0:
            return f"エラー: {result.stderr or result.stdout}", False
        return result.stdout, True
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def post_to_slack(text: str) -> bool:
    """Slack に投稿"""
    if not SLACK_WEBHOOK_URL:
        return False
    import urllib.request
    import json
    payload = {"blocks": [{"type": "section", "text": {"type": "plain_text", "text": text, "emoji": True}}]}
    req = urllib.request.Request(
        SLACK_WEBHOOK_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as res:
            return res.status == 200
    except Exception:
        return False


def _open_transcript_modal(client, trigger_id: str, channel_id: str = ""):
    """文字起こし入力用モーダルを開く"""
    view = {
        "type": "modal",
        "callback_id": "rafb_transcript_modal",
        "title": {"type": "plain_text", "text": "初回架電FB"},
        "submit": {"type": "plain_text", "text": "送信"},
        "blocks": [
            {
                "type": "input",
                "block_id": "transcript_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "transcript_input",
                    "multiline": True,
                    "placeholder": {"type": "plain_text", "text": "文字起こしをここに貼り付けてください"},
                },
                "label": {"type": "plain_text", "text": "文字起こし"},
            }
        ],
    }
    if channel_id:
        view["private_metadata"] = channel_id
    client.views_open(trigger_id=trigger_id, view=view)


@app.command("/rafb")
def handle_rafb(ack, body, client, command):
    """Slash コマンド /rafb → モーダルで入力スペースを表示"""
    ack()

    channel_id = command.get("channel_id", "")
    _open_transcript_modal(client, body["trigger_id"], channel_id)


@app.view("rafb_transcript_modal")
def handle_modal_submit(ack, body, client, view):
    """モーダル送信時にフィードバック生成"""
    ack()

    values = view.get("state", {}).get("values", {})
    transcript = (
        values.get("transcript_block", {}).get("transcript_input", {}).get("value", "")
    ).strip()

    if not transcript:
        return

    # ユーザーに処理中を通知
    user_id = body.get("user", {}).get("id", "")
    channel_id = view.get("private_metadata") or body.get("container", {}).get("channel_id", "")
    if user_id and channel_id:
        try:
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text="処理中です。完了次第 #dk_ra_初回架電fb に投稿します。",
            )
        except Exception:
            pass

    import threading

    def _do():
        feedback, success = run_feedback_from_text(transcript)
        if success:
            post_to_slack(feedback)

    threading.Thread(target=_do, daemon=True).start()


if __name__ == "__main__":
    print("=" * 50)
    print("RA FB サーバー起動（Socket Mode = ngrok 不要）")
    print("Slack で /rafb が使えます")
    print("=" * 50)
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
