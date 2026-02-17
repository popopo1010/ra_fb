"""法人情報の抽出・格納・比較（都道府県×セグメント）"""

from __future__ import annotations

import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .config import load_env, MASTER_DIR, CANDIDATE_ATTRACT_DIR, SEGMENT_ORDER

load_env()

# マーケットセグメント情報（工種×用途の2軸＋マーケットサイズ）
# references/candidate_attract/market_segments.py と同期
_SEGMENT_MARKET_INFO: dict[str, dict] = {
    "電気系": {"market_size": "設備19兆円の約半数", "axis": "工種"},
    "土木": {"market_size": "土木工事 約35兆円", "axis": "工種"},
    "建築": {"market_size": "建築工事 約40兆円", "axis": "工種"},
    "管工事": {"market_size": "空調・衛生設備", "axis": "工種"},
    "DC": {"market_size": "急拡大（国策）", "axis": "用途"},
    "再エネ": {"market_size": "高成長（補助金・FIT）", "axis": "用途"},
    "物流": {"market_size": "前年比10%超", "axis": "用途"},
    "工場": {"market_size": "半導体・脱炭素で大型案件", "axis": "用途"},
    "オフィス": {"market_size": "都市再開発", "axis": "用途"},
    "公共": {"market_size": "生活基盤50%、産業基盤34%", "axis": "用途"},
    "住宅": {"market_size": "約16兆円", "axis": "用途"},
    "商業施設": {"market_size": "商業施設工事", "axis": "用途"},
    "自衛隊": {"market_size": "防衛関連施設", "axis": "用途"},
    "その他": {"market_size": "", "axis": "その他"},
}


def _get_segment_market_size(segment: str) -> str:
    return _SEGMENT_MARKET_INFO.get(segment, {}).get("market_size", "")


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
        f"{company_name} OpenWork 口コミ 評判",
        f"{company_name} 転職会議 口コミ",
        f"{company_name} 休日 残業 働き方 福利厚生",
        f"{company_name} 直行直帰 リモート 在宅",
        f"{company_name} 採用 人事 採用担当",
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
SEGMENTS = SEGMENT_ORDER[:11]  # 基本11種（商業施設・自衛隊・その他を除く）


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
【Web検索で取得した事業・マーケット・企業情報】
以下の検索結果から、以下を抽出し、該当セクションに構造化して記載してください。文字起こしにない項目は検索結果から補完すること。情報がない項目は「未確認」と記載。

■ 企業情報セクションに統合して記載。重複なく1テーブルで。
  - 事業概要、マーケット成長性、法人HP URL、売上構成比、今後の注力領域
  - 企業スナップショット、前職規模別USP、採用意思決定者、口コミ評価傾向
■ 労働条件の「休日・直行直帰・リモート」に働き方の詳細を1行で

{research_text[:8000]}
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
・4. 事業概要（会社の事業内容＋事業一覧・主軸事業を統合）
・5. マーケット成長性（成長度＋なぜ成長しているか背景・要因と競合。高/中/低だけでは不十分）
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
・候補者別訴求: ①〜③の採用可否と訴求、大手・中堅・零細出身者向けの一言USP。重複なく記載
・同エリア差別化: 同都道府県×同セグメントの競合との違いに特化（企業の一般論は差別化メモに書かない）
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

## 企業情報
| 項目 | 内容 |
|------|------|
| 会社名 | |
| 都道府県 | |
| 事業概要 | 主な事業・工事・案件、事業一覧・主軸事業 |
| マーケット成長性 | 成長度＋なぜ成長しているか（背景・要因）と競合 |
| 法人HP URL | 公式サイト（Web検索で補足） |
| 売上構成比 | 各事業の構成比（推定可） |
| 今後の注力領域 | 中期計画・IR等から |
| 企業スナップショット | 一言で言うとどういう会社か、業界内ポジション、直近の勢い |
| 前職規模別USP | 大手・中堅・零細出身者向けの一言USP |
| 採用意思決定者 | 人事部／現場部長／経営者直轄など |
| 口コミ評価傾向 | OpenWork・転職会議等の評価傾向 |

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
| 休日・直行直帰・リモート | 完全週休2日、直行直帰OK、リモート可否等 |
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

## 候補者別訴求
| セグメント | 採用 | 訴求・差別化 |
|------------|------|--------------|
| ①電気工事士もち、施工管理未経験 | ○/△/× | |
| ②施工管理資格もち、マネジメント未経験 | ○/△/× | |
| ③施工管理資格もち、マネジメント経験あり | ○/△/× | |
| 大手出身者向け（1,000名以上） | - | 一言USP |
| 中堅出身者向け（100〜999名） | - | 一言USP |
| 零細出身者向け（100名未満） | - | 一言USP |

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


# リサーチで補完する項目（FBにない時にWeb検索で追加）
SUPPLEMENT_KEYS = [
    "企業スナップショット",
    "前職規模別USP",
    "採用意思決定者",
    "口コミ評価傾向",
]
SUPPLEMENT_KEY_WORKSTYLE = "休日・直行直帰・リモート"  # 労働条件セクション


def _needs_supplement(body: str) -> bool:
    """企業スナップショット等の補完が必要か判定"""
    if not _extract_table_value(body, "企業スナップショット"):
        return True
    if "前職規模別" not in body and "大手出身者向け" not in body:
        return True
    if "採用意思決定者" not in body:
        return True
    if "口コミ" not in body and "OpenWork" not in body:
        return True
    workstyle_keys = (SUPPLEMENT_KEY_WORKSTYLE, "休日数・直行直帰・リモート可否", "休日数", "リモート可否")
    if not any(_extract_table_value(body, k) for k in workstyle_keys):
        return True
    return False


def _supplement_from_research_with_claude(
    existing_content: str,
    company_name: str,
    research_text: str,
) -> str:
    """既存法人情報に検索結果から不足項目を補完。Claudeでマージ。"""
    try:
        from anthropic import Anthropic
    except ImportError:
        return ""

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or not research_text:
        return ""

    client = Anthropic(api_key=api_key)
    user_prompt = f"""以下の既存法人情報があります。Web検索結果から、不足している項目を補完してマージした完全版を出力してください。

【補完対象項目】## 企業情報 セクションに以下を追加・更新。既存テーブルに統合すること。
・企業スナップショット、前職規模別USP、採用意思決定者、口コミ評価傾向
・労働条件の「休日・直行直帰・リモート」行

既存の内容は維持し、不足項目のみ追加。検索結果に情報がない項目は「未確認」と記載。
出力は既存と同じMarkdown形式（YAML frontmatter、## 見出し、テーブル）で行うこと。
既存に「## 企業情報」がなければ作成し、基本情報・事業リサーチ・企業スナップショットを1テーブルに統合すること。

---
【既存法人情報】
{existing_content[:6000]}

---
【Web検索結果】
{research_text[:8000]}
"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0.2,
        )
        return (response.content[0].text if response.content else "").strip()
    except Exception:
        return ""


def supplement_company_master_from_research(
    company_name_or_path: str | Path,
) -> Optional[Path]:
    """
    法人マスタの不足項目（企業スナップショット等）をWeb検索で補完。
    FBにない情報をリサーチして追加する。

    Args:
        company_name_or_path: 会社名 または 法人マスタファイルパス

    Returns:
        更新したファイルパス。補完不要・失敗時は None
    """
    path = Path(company_name_or_path) if isinstance(company_name_or_path, (str, Path)) else None
    if path and path.exists() and path.suffix == ".md":
        filepath = path
        company_name = path.stem
    else:
        company_name = str(company_name_or_path).strip()
        if not company_name or company_name in ("未設定", "未確認"):
            return None
        filepath = MASTER_DIR / f"{_sanitize_filename(company_name)}.md"
        if not filepath.exists():
            return None

    content = filepath.read_text(encoding="utf-8")
    if not content.strip().startswith("---"):
        return None
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None
    body = parts[2].strip()

    if not _needs_supplement(body):
        return filepath  # 補完不要

    research_text = _research_company_online(company_name)
    if not research_text:
        return filepath

    merged = _supplement_from_research_with_claude(content, company_name, research_text)
    if not merged or "---" not in merged:
        return None

    filepath.write_text(merged, encoding="utf-8")
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


def _extract_table_value(body: str, key: str) -> str:
    """本文からマークダウンテーブルの項目値を抽出"""
    pattern = rf"\|\s*{re.escape(key)}\s*\|\s*([^\n|]+?)\s*\|"
    m = re.search(pattern, body)
    if m:
        val = m.group(1).strip()
        return val if val and val != "未確認" else ""
    return ""


def collect_attract_examples_from_masters() -> List[dict]:
    """
    全法人マスタからマーケット成長性・事業戦略を抽出。
    アトラクトプレイブック更新用。
    """
    results = []
    if not MASTER_DIR.exists():
        return results

    for f in MASTER_DIR.glob("*.md"):
        if f.name.startswith("_") or f.name in ("マスタ項目一覧.md", "README.md"):
            continue
        try:
            text = f.read_text(encoding="utf-8")
            if not text.strip().startswith("---"):
                continue
            parts = text.split("---", 2)
            if len(parts) < 3:
                continue
            meta = _parse_frontmatter_simple(parts[1])
            body = parts[2]

            company_name = meta.get("会社名", f.stem)
            segs = meta.get("セグメント") or []
            if isinstance(segs, str):
                segs = [s.strip() for s in segs.replace("、", ",").split(",") if s.strip()]

            growth = (
                _extract_table_value(body, "マーケット成長性")
                or _extract_table_value(body, "マーケットの成長性・競合")
                or _extract_table_value(body, "マーケットの成長度合い")
            )
            strategy = (
                _extract_table_value(body, "今後の注力領域")
                or _extract_table_value(body, "事業概要")
                or _extract_table_value(body, "事業一覧・主軸事業")
            )
            if not growth and not strategy:
                continue

            results.append({
                "company_name": company_name,
                "segments": segs,
                "growth": growth,
                "strategy": strategy,
            })
        except Exception:
            continue

    return results


def update_playbook_from_masters() -> Optional[Path]:
    """
    法人マスタからマーケット成長性・事業戦略を抽出し、
    アトラクトプレイブックに「法人別事例」セクションを追加・更新。
    """
    playbook_path = CANDIDATE_ATTRACT_DIR / "recruitment-playbook.md"
    if not playbook_path.exists():
        return None

    examples = collect_attract_examples_from_masters()
    if not examples:
        return playbook_path

    # セグメント別にグループ化（複数セグメントの会社は各セグメントに出現）
    by_segment: dict[str, list] = {}
    for ex in examples:
        segs = ex["segments"] or ["その他"]
        for seg in segs:
            if seg not in by_segment:
                by_segment[seg] = []
            by_segment[seg].append(ex)

    # セグメントの表示順（config で一元管理）
    ordered_segs = [s for s in SEGMENT_ORDER if s in by_segment]
    ordered_segs += [s for s in sorted(by_segment) if s not in ordered_segs]

    # ユニーク会社数
    all_companies = set(ex["company_name"] for ex in examples)

    lines = [
        "",
        "---",
        "",
        "## 5. 法人別事例（マーケット成長性・事業戦略）",
        "",
        "※法人マスタから自動抽出。面談で聞けた実例を整理。`python scripts/update_playbook.py` で更新",
        "",
        "### 5.1 全体概要（ドメイン×会社）",
        "",
        "事業ドメイン（セグメント）ごとのカバー状況。解像度が上がるほど全体像が見える。",
        "",
        "| 項目 | 値 |",
        "|------|-----|",
        f"| ユニーク会社数 | **{len(all_companies)} 社** |",
        f"| ドメイン数 | {len(ordered_segs)} |",
        "",
        "**ドメイン別会社数（マーケットサイズ付き）**",
        "",
        "| 軸 | ドメイン | マーケットサイズ | 会社数 |",
        "|----|----------|------------------|--------|",
    ]

    for seg in ordered_segs:
        items = by_segment[seg]
        unique_in_seg = len(set(ex["company_name"] for ex in items))
        axis = _SEGMENT_MARKET_INFO.get(seg, {}).get("axis", "")
        mkt = _get_segment_market_size(seg)
        lines.append(f"| {axis} | {seg} | {mkt} | {unique_in_seg} 社 |")
    lines.extend(["", ""])

    lines.extend([
        "### 5.2 ドメイン別会社一覧",
        "",
        "各ドメインにどの会社があるか。下記の詳細テーブルへのインデックス。",
        "",
    ])

    for seg in ordered_segs:
        items = by_segment[seg]
        names = sorted(set(ex["company_name"] for ex in items))
        lines.append(f"- **{seg}** ({len(names)}社): " + "、".join(names))
    lines.extend(["", ""])

    lines.extend([
        "### 5.3 法人別事例（詳細）",
        "",
    ])

    for seg in ordered_segs:
        items = by_segment[seg]
        lines.append(f"#### {seg}")
        lines.append("")
        lines.append("| 会社名 | マーケット成長性 | 事業戦略・注力領域 |")
        lines.append("|--------|------------------|-------------------|")
        for ex in items:
            growth_short = (ex["growth"][:80] + "…") if len(ex["growth"]) > 80 else ex["growth"]
            strategy_short = (ex["strategy"][:80] + "…") if len(ex["strategy"]) > 80 else ex["strategy"]
            name = ex["company_name"].replace("|", "｜")
            growth_short = growth_short.replace("|", "｜").replace("\n", " ")
            strategy_short = strategy_short.replace("|", "｜").replace("\n", " ")
            lines.append(f"| {name} | {growth_short} | {strategy_short} |")
        lines.append("")

    new_section = "\n".join(lines)

    content = playbook_path.read_text(encoding="utf-8")
    if "## 5. 法人別事例" in content:
        content = re.sub(
            r"\n---\n\n## 5\. 法人別事例.*",
            new_section,
            content,
            flags=re.DOTALL,
        )
    else:
        content = content.rstrip() + new_section

    playbook_path.write_text(content, encoding="utf-8")
    return playbook_path


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
