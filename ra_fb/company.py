"""法人情報の抽出・格納・比較（都道府県×セグメント）"""

from __future__ import annotations

import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .config import load_env, MASTER_DIR

load_env()


def _research_company_online(company_name: str) -> str:
    """
    会社名から Web 検索で事業・マーケット情報を取得。
    事業一覧、売上構成、中期計画・IR・社長メッセージ、競合・成長性を検索。
    """
    if not company_name or company_name in ("未設定", "未確認"):
        return ""
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*duckduckgo_search.*renamed.*")
            from duckduckgo_search import DDGS
    except ImportError:
        return ""

    queries = [
        (f"{company_name} 公式サイト", True),  # URL取得のためhrefを含める
        f"{company_name} 事業 売上構成",
        f"{company_name} 中期経営計画 IR",
        f"{company_name} 社長メッセージ 経営方針",
        f"{company_name} 競合 マーケット 成長",
    ]
    all_snippets: list[str] = []
    seen: set[str] = set()

    try:
        ddgs = DDGS()
        for item in queries:
            q = item[0] if isinstance(item, tuple) else item
            include_url = isinstance(item, tuple) and item[1]
            try:
                results = list(ddgs.text(q, region="jp-jp", max_results=5))
                for r in results:
                    body = (r.get("body") or "").strip()
                    title = (r.get("title") or "").strip()
                    href = (r.get("href") or "").strip()
                    key = body or href
                    if key and key not in seen:
                        seen.add(key)
                        if include_url and href:
                            all_snippets.append(f"【{title}】\nURL: {href}\n{body}")
                        elif body:
                            all_snippets.append(f"【{title}】\n{body}")
                time.sleep(0.5)
            except Exception:
                continue
    except Exception:
        return ""

    if not all_snippets:
        return ""
    return "\n\n---\n\n".join(all_snippets[:15])

# 都道府県×セグメントで比較するためのセグメント一覧（候補者アトラクト準拠）
SEGMENTS = [
    "電気系", "土木", "建築", "管工事",
    "DC", "再エネ", "物流", "工場", "オフィス", "公共", "住宅",
]


def _sanitize_filename(name: str) -> str:
    """ファイル名に使える文字に変換"""
    if not name or not name.strip():
        return "未設定"
    s = name.strip()
    s = re.sub(r'[\\/:*?"<>|]', "_", s)
    s = s[:80]
    return s or "未設定"


def _extract_company_info_with_claude(
    transcript: str,
    company_name: str,
    source_type: str,
    existing_content: Optional[str] = None,
    research_text: Optional[str] = None,
) -> str:
    """Claude で文字起こしから法人情報を抽出。都道府県×セグメントで比較可能な形式"""
    try:
        from anthropic import Anthropic
    except ImportError:
        return ""

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return ""

    client = Anthropic(api_key=api_key)
    source_label = "初回架電" if source_type == "ra" else "法人面談"

    merge_instruction = ""
    if existing_content:
        merge_instruction = """
【既存の法人情報】
上記と文字起こしを照らし合わせ、新規情報を追加・修正してマージした完全版を出力してください。既存で不明な項目は文字起こしから補完。矛盾する場合は新しい情報を優先。
都道府県・セグメントは必ず出力すること（比較の軸となるため）。
"""

    research_block = ""
    if research_text:
        research_block = f"""
【Web検索で取得した事業・マーケット情報】
以下の検索結果から、法人HP URL（公式サイト）、事業一覧・主軸事業、売上構成比（推定可）、今後の注力領域、マーケットの成長性・競合を抽出し、「## 事業リサーチ」セクションに構造化して記載してください。マーケットの成長性には**なぜ成長しているか（背景・要因）**を必ず含めること（成長しているかどうかだけでは判断できない）。URLは検索結果の「URL:」から取得。情報がない項目は「未確認」と記載。

{research_text[:6000]}
"""

    user_prompt = f"""以下の「{source_label}の文字起こし」から法人情報を抽出し、指定フォーマットで出力してください。
会社名は「{company_name or "未確認"}」としてください。

【重要】都道府県×セグメントで比較するため、以下を厳守してください。
・都道府県: 勤務地の都道府県を列挙（例: 愛知, 岐阜, 東京）。複数可
・セグメント: 電気系/土木/建築/管工事、DC/再エネ/物流/工場/オフィス/公共/住宅 から該当するものを列挙

【抽出する項目】以下の20項目を必ず抽出。未確認は「未確認」。
・1. 必要資格（必須・歓迎）
・2. 必要経験（年数・内容）
・3. 仕事内容（求人ポジションの具体的な業務）
・4. 会社の事業内容（主な事業・工事・案件）
・5. マーケットの成長度合い（成長度＋なぜ成長しているか背景・要因。高/中/低だけでは不十分）
・6. 都道府県（勤務地）
・7. 未経験OKかどうか（○/△/×）
・8. 年齢（条件）
・9. 出張ありなし（頻度・範囲）
・10. 福利厚生（社会保険、手当等）
・11. 残業時間（残業の状況）
・12. 採用人数（採用予定人数）
・13. 手数料（人材紹介手数料、聞けた場合）
・14. 面接の方式（オンライン/オフライン、形式）
・15. 面接回数（選考の回数）
・16. 面接で見ているポイント（面接で重視している点）
・17. 過去落とした人（落とした人の特徴・理由）
・18. 受かった人（受かった人の特徴）
・19. 評価（人事評価制度、評価の仕方）
・20. キャリアアップ制度（昇格・昇給・キャリアパス）
・候補者タイプ別: ①電気工事士もち施工管理未経験 ②施工管理資格もちマネジメント未経験 ③施工管理資格もちマネジメント経験あり の採用可否（○/△/×）と訴求・差別化
・同エリア差別化: 同都道府県×同セグメントの競合との違い、訴求の軸
{merge_instruction}
{research_block}

## 文字起こし（抜粋）
{transcript[:8000]}

## 出力形式（必ずYAML frontmatterから開始）

---
会社名: "{company_name or "未確認"}"
都道府県: ["愛知", "岐阜"]   # 勤務地の都道府県。複数可
セグメント: ["電気系", "施工管理"]   # 該当セグメント。電気系/土木/建築/管工事/DC/再エネ/物流/工場/オフィス/公共/住宅 から選択
最終更新: "{datetime.now().strftime("%Y-%m-%d")}"
出典: {source_label}
---

# 法人情報：{company_name or "未確認"}

## 基本情報
| 項目 | 内容 |
|------|------|
| 会社名 | |
| 都道府県 | |
| 会社の事業内容 | |
| マーケットの成長度合い | |

## 事業リサーチ（Web検索で補足）
| 項目 | 内容 |
|------|------|
| 法人HP URL | 公式サイトURL |
| 事業一覧・主軸事業 | 展開事業の一覧、主軸事業 |
| 売上構成比 | 各事業の構成比（推定可） |
| 今後の注力領域 | 中期計画・IR・社長メッセージ等から |
| マーケットの成長性・競合 | 成長性（なぜ成長しているか背景・要因）と競合状況 |

## 仕事内容
| 項目 | 内容 |
|------|------|
| 仕事内容 | 求人ポジションの具体的な業務 |

## 採用条件
| 項目 | 内容 |
|------|------|
| 必要資格 | |
| 必要経験 | |
| 未経験OK | ○/△/× |
| 年齢 | |
| 採用人数 | |

## 労働条件
| 項目 | 内容 |
|------|------|
| 出張 | あり/なし、頻度・範囲 |
| 残業時間 | |
| 福利厚生 | |

## 評価・キャリアアップ
| 項目 | 内容 |
|------|------|
| 評価 | 人事評価制度、評価の仕方 |
| キャリアアップ制度 | 昇格・昇給・キャリアパス |

## 面接・選考
| 項目 | 内容 |
|------|------|
| 面接の方式 | オンライン/オフライン、形式 |
| 面接回数 | 選考の回数 |
| 面接で見ているポイント | 面接で重視している点 |
| 過去落とした人 | 落とした人の特徴・理由 |
| 受かった人 | 受かった人の特徴 |

## その他
| 項目 | 内容 |
|------|------|
| 手数料 | 人材紹介手数料（聞けた場合） |
| 重視点 | |

## 候補者タイプ別
| 候補者タイプ | 採用 | 訴求・差別化 |
|--------------|------|--------------|
| ①電気工事士もち、電気施工管理未経験 | ○/△/× | |
| ②施工管理資格もち、マネジメント経験なし | ○/△/× | |
| ③施工管理資格もち、マネジメント経験あり | ○/△/× | |

## 同エリア×同セグメント差別化メモ
（都道府県×セグメントで比較する際の差別化ポイント）

## 更新履歴
- {datetime.now().strftime("%Y-%m-%d")}: {source_label}より抽出
"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0.2,
        )
        return (response.content[0].text if response.content else "").strip()
    except Exception:
        return ""


def extract_and_save_company_info(
    transcript: str,
    company_name: str = "",
    source_type: str = "ra",
    use_research: bool = True,
) -> Optional[Path]:
    """
    FB の文字起こしから法人情報を抽出し、法人マスタに格納する。
    都道府県×セグメントで比較可能な形式（YAML frontmatter付き）。
    use_research=True の場合、会社名から Web 検索で事業・マーケット情報を補足する。

    Args:
        transcript: 文字起こし
        company_name: 会社名（空の場合は文字起こしから推測）
        source_type: "ra"（初回架電） or "ca"（法人面談）
        use_research: Web検索で事業リサーチを実行するか（デフォルト True）

    Returns:
        保存したファイルパス。失敗時は None
    """
    if not transcript or not transcript.strip():
        return None

    MASTER_DIR.mkdir(parents=True, exist_ok=True)

    if not company_name or not company_name.strip():
        company_name = "未設定"

    research_text: Optional[str] = None
    if use_research and company_name not in ("未設定", "未確認"):
        research_text = _research_company_online(company_name)

    existing_content = None
    filepath = MASTER_DIR / f"{_sanitize_filename(company_name)}.md"
    if filepath.exists():
        existing_content = filepath.read_text(encoding="utf-8")

    content = _extract_company_info_with_claude(
        transcript,
        company_name,
        source_type,
        existing_content,
        research_text=research_text,
    )
    if not content:
        return None

    filepath.write_text(content, encoding="utf-8")
    return filepath


def _parse_frontmatter_simple(fm_text: str) -> dict:
    """簡易YAML frontmatterパース（PyYAML不要）"""
    meta = {}
    for line in fm_text.splitlines():
        line = line.strip()
        if ":" not in line or line.startswith("#"):
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip().strip('"\'')
        if key in ("都道府県", "セグメント") and val.startswith("["):
            # ["愛知", "岐阜"] 形式
            items = re.findall(r'["\']([^"\']+)["\']', val)
            meta[key] = [i.strip() for i in items if i.strip()]
        else:
            meta[key] = val
    return meta


def list_companies_by_region_segment(
    prefecture: str,
    segment: str,
) -> List[dict]:
    """
    都道府県×セグメントで法人を絞り込み。

    Args:
        prefecture: 都道府県（愛知、東京、大阪 等）
        segment: セグメント（電気系、土木、DC、再エネ 等）

    Returns:
        [{path, meta, body}, ...]
    """
    results = []
    if not MASTER_DIR.exists():
        return results

    prefecture = (prefecture or "").strip()
    segment = (segment or "").strip()
    if not prefecture or not segment:
        return results

    for f in MASTER_DIR.glob("*.md"):
        if f.name.startswith("_"):
            continue
        try:
            text = f.read_text(encoding="utf-8")
            if not text.strip().startswith("---"):
                continue
            parts = text.split("---", 2)
            if len(parts) < 3:
                continue
            meta = _parse_frontmatter_simple(parts[1])
            body = parts[2].strip()

            prefs = meta.get("都道府県") or []
            segs = meta.get("セグメント") or []
            if isinstance(prefs, str):
                prefs = [p.strip() for p in prefs.replace("、", ",").split(",") if p.strip()]
            if isinstance(segs, str):
                segs = [s.strip() for s in segs.replace("、", ",").split(",") if s.strip()]

            if prefecture in prefs and segment in segs:
                results.append({"path": f, "meta": meta, "body": body})
        except Exception:
            continue

    return results


def compare_companies(prefecture: str, segment: str) -> str:
    """
    都道府県×セグメントで法人を比較し、差別化を出力。

    Returns:
        比較結果のテキスト
    """
    companies = list_companies_by_region_segment(prefecture, segment)
    if not companies:
        return f"【{prefecture} × {segment}】に該当する法人はありません。\n\n法人マスタに情報を追加してください（FB生成時に自動格納）。"

    lines = [
        f"# 法人比較：{prefecture} × {segment}",
        f"該当 {len(companies)} 社",
        "",
    ]
    for i, c in enumerate(companies, 1):
        meta = c.get("meta") or {}
        name = meta.get("会社名", c["path"].stem)
        lines.append(f"## {i}. {name}")
        lines.append("")
        lines.append(c.get("body", "")[:2000])
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)
