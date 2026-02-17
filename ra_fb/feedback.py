"""FB 生成ロジック（RA・CA）"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict

from .config import ROOT, load_env

load_env()


def _load_candidate_attract() -> str:
    """候補者アトラクト（会社の魅力の伝え方）を読み込む。
    SALES_FB_AGENT_PATH が設定されていれば sales-fb-agent から、
    なければ references/candidate_attract/ のローカルコピーを使用。
    """
    sales_path = os.environ.get("SALES_FB_AGENT_PATH")
    if sales_path:
        p = Path(sales_path) / "reference" / "domain" / "construction" / "04-recruitment-playbook.md"
        if p.exists():
            return p.read_text(encoding="utf-8")[:6000]
    p = ROOT / "references" / "candidate_attract" / "recruitment-playbook.md"
    if p.exists():
        return p.read_text(encoding="utf-8")[:6000]
    return ""


def _load_references_ra() -> Dict[str, str]:
    """RA 用リファレンス"""
    refs = {}
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
            refs[key] = p.read_text(encoding="utf-8")[: limits.get(key, 8000)]
    attract = _load_candidate_attract()
    if attract:
        refs["attract"] = attract
    return refs


def _load_references_ca() -> Dict[str, str]:
    """CA 用リファレンス"""
    refs = {}
    paths = {
        "template": ROOT / "references" / "法人面談議事録" / "_template_議事録.md",
        "manual": ROOT / "references" / "manual" / "営業新規架電マニュアル.md",
    }
    for key, p in paths.items():
        if p.exists():
            refs[key] = p.read_text(encoding="utf-8")[:8000]
    return refs


def _generate_ra_with_claude(transcript: str, refs: Dict[str, str], ra_name: str = "") -> str:
    """Claude API で RA FB を生成"""
    try:
        from anthropic import Anthropic
    except ImportError:
        return _template_ra(ra_name)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _template_ra(ra_name)

    client = Anthropic(api_key=api_key)
    ref_text = "\n\n---\n\n".join(f"【{k}】\n{v}" for k, v in refs.items())

    system_prompt = "あなたは人材紹介営業の架電フィードバック専門家です。PSS（オープニング・プロービング・サポーティング・クロージング）の観点を活用し、評価は厳しく、指摘を具体的に。過度に褒めず、聞けていない点・改善すべき点を明確に指摘します。"

    user_prompt = f"""あなたは人材紹介営業（電気工事士・施工管理）の架電フィードバック担当です。
以下の「初回架電の文字起こし」を、リファレンスに基づいて評価し、RA向けのフィードバックを出力してください。

【リファレンスの活用】
・manual: 架電マニュアル（受付突破・ヒアリング・業界知識）
・pss: PSS（オープニング・プロービング・サポーティング・クロージング）の観点で評価
・checklist: 初回面談の確認項目
・reception: 受付突破の断りパターンと繋ぎ方
・kadai: 課題整理・改善の観点
・attract: 候補者アトラクト（訴求軸・候補者タイプ×セグメント・伝え方）※あれば

【評価のスタンス】
・指摘は厳しく。聞けていない項目は「未確認」。マークダウンは使わず、【】と・を使用。
・メールアドレス確認は復唱で十分。HP確認はRA自身が裏で行う。
・各項目内の箇条書きには番号を付ける（1. 2. 3. … の形式）。見やすさのため必ず守ること。

## リファレンス
{ref_text}

## 出力形式（7項目、マークダウンなし）
1. 【良かった点】
2. 【改善点】
3. 【採用概要状況】採用必要数・エリア・資格・年齢・経験・年収・出張・重視点等。未確認は「未確認」
4. 【進めるにあたっての障壁】
5. 【具体的に聞き方を変えた方がいい点と言い回し】
6. 【この会社の魅力を候補者に伝える時に、どう伝えるといいか】attract を参照し、この企業のセグメント・候補者タイプに合わせた訴求の軸・言い回しを具体的に
7. 【全体所感】

## 文字起こし（出力に含めない）
{transcript[:12000]}

## フィードバック（上記形式でプレーンテキストで出力）
"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0.3,
        )
        return (response.content[0].text if response.content else "").strip()
    except Exception as e:
        return f"[AI生成エラー: {e}]\n\n" + _template_ra(ra_name)


def _generate_ca_with_claude(transcript: str, refs: Dict[str, str]) -> str:
    """Claude API で CA FB を生成"""
    try:
        from anthropic import Anthropic
    except ImportError:
        return _template_ca()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _template_ca()

    client = Anthropic(api_key=api_key)
    ref_text = "\n\n---\n\n".join(f"【{k}】\n{v}" for k, v in refs.items())

    system_prompt = "あなたは人材紹介営業の法人面談フィードバック専門家です。議事録テンプレートの観点で、聞けた項目・聞けていない項目を整理し、CA向けに改善点を具体的に指摘します。"

    user_prompt = f"""以下の「法人面談の文字起こし」を、リファレンスに基づいて評価し、CA向けのフィードバックを出力してください。

【リファレンスの活用】
・template: 法人面談議事録の聞けた項目チェックリスト
・manual: 架電マニュアル（参考）

【評価の観点】
・営業情報・求職者情報・事業理解。聞けていない項目は「未確認」。
・マークダウンは使わず、【】と・を使用。

## リファレンス
{ref_text}

## 出力形式（マークダウンなし）
1. 【聞けた項目】
2. 【未確認・聞けていない項目】
3. 【改善点】
4. 【全体所感】

## 文字起こし（出力に含めない）
{transcript[:12000]}

## フィードバック（上記形式でプレーンテキストで出力）
"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0.3,
        )
        return (response.content[0].text if response.content else "").strip()
    except Exception as e:
        return f"[AI生成エラー: {e}]\n\n" + _template_ca()


def _template_ra(ra_name: str) -> str:
    return """【良かった点】
・（ANTHROPIC_API_KEYを設定するとAIが自動で記入します）

【改善点】
・（同上）

【採用概要状況】
・採用必要数・エリア・資格・年齢・経験・年収・出張・重視点：（同上）

【進めるにあたっての障壁】
・（同上）

【具体的に聞き方を変えた方がいい点と言い回し】
・（同上）

【この会社の魅力を候補者に伝える時に、どう伝えるといいか】
・（同上。references/candidate_attract/ または sales-fb-agent を参照）

【全体所感】
・（同上）
"""


def _template_ca() -> str:
    return """【聞けた項目】
・（ANTHROPIC_API_KEYを設定するとAIが自動で記入します）

【未確認・聞けていない項目】
・（同上）

【改善点】
・（同上）

【全体所感】
・（同上）
"""


def generate_feedback_ra(
    transcript: str,
    ra_name: str = "",
    company_name: str = "",
    use_ai: bool = True,
) -> str:
    """RA（初回架電）FB を生成。戻り値: full_message（ヘッダー含む）"""
    refs = _load_references_ra()
    feedback = _generate_ra_with_claude(transcript, refs, ra_name) if use_ai else _template_ra(ra_name)
    header = f"📞 初回架電FB | 会社名: {company_name or 'ー'} | RA担当: {ra_name or 'ー'}"
    return f"{header}\n\n{feedback}"


def generate_feedback_ca(
    transcript: str,
    company_name: str = "",
    use_ai: bool = True,
) -> str:
    """CA（法人面談）FB を生成。戻り値: full_message（ヘッダー含む）"""
    refs = _load_references_ca()
    feedback = _generate_ca_with_claude(transcript, refs) if use_ai else _template_ca()
    header = f"📋 CA FB | 会社名: {company_name or 'ー'}"
    return f"{header}\n\n{feedback}"
