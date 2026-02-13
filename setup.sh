#!/bin/bash
# RA_FBシステム セットアップスクリプト
# macOS などで pip が使えない場合、venv を作成して依存関係をインストール

set -e
cd "$(dirname "$0")"

echo "=== RA_FBシステム セットアップ ==="

if [ -d "venv" ] && [ "$1" != "--force" ]; then
    echo "venv は既に存在します。"
    echo "有効化: source venv/bin/activate"
    echo "再構築する場合: ./setup.sh --force"
    exit 0
fi

if [ -d "venv" ] && [ "$1" = "--force" ]; then
    echo "venv を削除して再構築します..."
    rm -rf venv
fi

echo "仮想環境を作成中..."
python3 -m venv venv

echo "依存関係をインストール中..."
./venv/bin/pip install -r requirements.txt

echo ""
echo "=== セットアップ完了 ==="
echo ""
echo "使い方:"
echo "  1. 仮想環境を有効化:  source venv/bin/activate"
echo "  2. Slack App サーバー起動:  python scripts/slack_app_server.py"
echo "  3. またはフィードバック生成:  python scripts/generate_feedback.py references/long_calls/茂野/xxx.md"
echo ""
echo ".env が未設定の場合は cp .env.example .env で作成し、トークンを設定してください。"
