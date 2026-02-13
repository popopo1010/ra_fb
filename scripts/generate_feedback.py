#!/usr/bin/env python3
"""
初回架電の文字起こしからフィードバックを生成し、Slack #dk_ra_初回架電fb に投稿する

使い方:
  python scripts/generate_feedback.py references/long_calls/茂野/TOKAI_EC_茂野_016.md
  python scripts/generate_feedback.py path/to/transcript.md --no-slack  # Slackに送らず標準出力のみ
"""

import os
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass


def load_references() -> dict[str, str]:
    """リファレンスを読み込む（Slack FB 用）"""
    refs = {}
    # 順序: 架電マニュアル → PSS → チェックリスト → 受付突破 → 課題整理
    # トークン配分: 重要度に応じて文字数制限（合計約35k以内）
    paths = {
        "manual": ROOT / "references" / "manual" / "営業新規架電マニュアル.md",
        "pss": ROOT / "references" / "manual" / "PSS_プロフェッショナルセリングスキル.md",
        "checklist": ROOT / "references" / "初回面談_確認チェックリスト.md",
        "reception": ROOT / "references" / "long_calls" / "受付突破_断りパターンと繋ぎ方.md",
        "kadai": ROOT / "references" / "long_calls" / "茂野vs小山田_課題整理.md",
    }
    limits = {"manual": 7000, "pss": 10000, "checklist": 4000, "reception": 4000, "kadai": 6000}
    for key, p in paths.items():
        if p.exists():
            text = p.read_text(encoding="utf-8")
            refs[key] = text[: limits.get(key, 8000)]
    return refs


def generate_feedback_with_claude(transcript: str, refs: dict[str, str], ra_name: str = "") -> str:
    """Claude API（Anthropic）でフィードバックを生成"""
    try:
        from anthropic import Anthropic
    except ImportError:
        return _generate_template_feedback(transcript, ra_name)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _generate_template_feedback(transcript, ra_name)

    client = Anthropic(api_key=api_key)

    ref_text = "\n\n---\n\n".join(f"【{k}】\n{v}" for k, v in refs.items())

    system_prompt = "あなたは人材紹介営業の架電フィードバック専門家です。PSS（オープニング・プロービング・サポーティング・クロージング）の観点を活用し、評価は厳しく、指摘を具体的に。過度に褒めず、聞けていない点・改善すべき点を明確に指摘します。"

    user_prompt = f"""あなたは人材紹介営業（電気工事士・施工管理）の架電フィードバック担当です。
以下の「初回架電の文字起こし」を、リファレンスに基づいて評価し、
RA向けのフィードバックを出力してください。

【リファレンスの活用】
・manual: 架電マニュアル（受付突破・ヒアリング・業界知識）
・pss: PSS（プロフェッショナル・セリング・スキル）オープニング・プロービング・サポーティング・クロージングの観点で評価する
・checklist: 初回面談の確認項目
・reception: 受付突破の断りパターンと繋ぎ方
・kadai: 課題整理・改善の観点

【評価のスタンス】
・指摘は厳しく行う。内容を甘く評価しすぎない。
・「良かった点」は事実ベースで簡潔に。過度に褒めない。
・「改善点」は具体的に、聞けていない項目・逃した機会・次回すべきことを明確に指摘する。
・PSSの観点（オープニング・プロービング・サポーティング・クロージング）で、どこができていたか・できていなかったかを指摘する。
・聞けていない採用概要（人数・年収・出張・重視点など）は「未確認」とし、聞くべきだった点を改善点で指摘する。
・全体所感では課題と次回への厳しいアドバイスを優先する。

【重要】
・書き起こし（文字起こし）は出力に含めないでください。
・マークダウン形式（##、**、-など）は使わず、プレーンテキストで記載してください。
・視認性のため、見出しは【】で囲み、箇条書きは・を使用してください。
・メールアドレス確認は復唱で十分。HP確認はRA自身が裏で行う。

## リファレンス
{ref_text}

## 出力形式（以下の6項目で構成、マークダウンは使わない）

1. 【良かった点】
2. 【改善点】
3. 【採用概要状況】以下の項目を最低限含める。聞けていない項目は「未確認」と記載。
   ・採用必要数
   ・エリア
   ・必要資格
   ・未経験の採用有無
   ・年齢
   ・経験
   ・年収（固定/賞与）
   ・出張
   ・採用において重視している点
   ・その他
4. 【進めるにあたっての障壁】（断り・懸念・不明点など）
5. 【具体的に聞き方を変えた方がいい点と言い回し】（改善案を具体的なセリフで）
6. 【全体所感】（総括・次回へのアドバイス）

## 文字起こし（評価対象、出力には含めない）
{transcript[:12000]}

## フィードバック（上記6項目の形式で、プレーンテキストで出力）
"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0.3,
        )
        text = response.content[0].text if response.content else ""
        return text.strip()
    except Exception as e:
        return f"[AI生成エラー: {e}]\n\n" + _generate_template_feedback(transcript, ra_name)


def _generate_template_feedback(transcript: str, ra_name: str) -> str:
    """APIなし時のテンプレートフィードバック（書き起こしは含めない、マークダウンなし）"""
    return """【良かった点】
・（ANTHROPIC_API_KEYを設定するとAIが自動で記入します）

【改善点】
・（同上）

【採用概要状況】
・採用必要数：（同上）
・エリア：（同上）
・必要資格：（同上）
・未経験の採用有無：（同上）
・年齢：（同上）
・経験：（同上）
・年収（固定/賞与）：（同上）
・出張：（同上）
・採用において重視している点：（同上）
・その他：（同上）

【進めるにあたっての障壁】
・（同上）

【具体的に聞き方を変えた方がいい点と言い回し】
・（同上）

【全体所感】
・（同上）
"""


def extract_ra_name(filepath: Path) -> str:
    """ファイルパスからRA名を推測（例: 茂野/xxx.md → 茂野）"""
    parts = filepath.parts
    if "茂野" in parts:
        return "茂野"
    if "重野" in parts:
        return "重野"
    if "小山田" in parts:
        return "小山田"
    return ""


def main():
    parser = argparse.ArgumentParser(description="初回架電フィードバック生成＆Slack投稿")
    parser.add_argument("transcript", type=Path, help="文字起こしファイルのパス")
    parser.add_argument("--no-slack", action="store_true", help="Slackに送らず標準出力のみ")
    parser.add_argument("--no-ai", action="store_true", help="AIを使わずテンプレートのみ")
    args = parser.parse_args()

    if not args.transcript.exists():
        print(f"エラー: ファイルが見つかりません: {args.transcript}", file=sys.stderr)
        sys.exit(1)

    transcript = args.transcript.read_text(encoding="utf-8")
    ra_name = extract_ra_name(args.transcript)

    refs = load_references()
    if args.no_ai:
        feedback = _generate_template_feedback(transcript, ra_name)
    else:
        feedback = generate_feedback_with_claude(transcript, refs, ra_name)

    # ヘッダーを付与（マークダウンなし）
    header = f"📞 初回架電FB | {args.transcript.stem}"
    if ra_name:
        header += f" | RA: {ra_name}"
    full_message = f"{header}\n\n{feedback}"

    print(full_message)

    if not args.no_slack:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from post_to_slack import post_to_slack
        success = post_to_slack(full_message)
        if success:
            print("\n✅ #dk_ra_初回架電fb に投稿しました", file=sys.stderr)
        else:
            print("\n❌ Slack投稿に失敗しました", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
