#!/usr/bin/env python3
"""
既存の法人マスタを新構造（企業情報統合、候補者別訴求統合）に移行する。

使い方:
  python scripts/migrate_company_master.py --dry-run   # 移行内容を表示、ファイルは更新しない
  python scripts/migrate_company_master.py             # 移行を実行
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ra_fb.config import MASTER_DIR
from ra_fb.company import _extract_table_value, _parse_frontmatter_simple

# 旧キー → 新キー のマッピング（複数候補から取得）
KEY_MAPPINGS = {
    "事業概要": ["事業概要", "事業一覧・主軸事業", "会社の事業内容"],
    "マーケット成長性": ["マーケット成長性", "マーケットの成長性・競合", "マーケットの成長度合い"],
    "休日・直行直帰・リモート": [
        "休日・直行直帰・リモート",
        "休日数・直行直帰・リモート可否",
        "休日数",
        "リモート可否",
    ],
}


def _get_value(body: str, keys: list[str]) -> str:
    """複数キーから最初に見つかった値を返す"""
    for k in keys:
        v = _extract_table_value(body, k)
        if v:
            return v
    return ""


def _extract_前職規模別_usps(body: str) -> str:
    """前職規模別アトラクトUSPテーブルから大手・中堅・零細のUSPを抽出して1文に"""
    parts = []
    for label in ["大手出身者向け", "中堅出身者向け", "零細出身者向け"]:
        v = _extract_table_value(body, label)
        if v:
            short = label.replace("出身者向け", "")
            parts.append(f"{short}：{v}")
    return "。".join(parts) if parts else ""


def _extract_口コミ(body: str) -> str:
    """口コミ評価傾向を抽出"""
    return (
        _extract_table_value(body, "口コミ評価傾向")
        or _extract_table_value(body, "OpenWork・転職会議等")
        or ""
    )


def migrate_file(content: str) -> str:
    """旧形式の法人マスタを新形式に変換"""
    if not content.strip().startswith("---"):
        return content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return content

    frontmatter = parts[1]
    body = parts[2]

    # 既に新形式（企業情報セクションあり）ならスキップ
    if "## 企業情報" in body and "| 事業概要 |" in body:
        return content

    # 各項目を抽出
    company_name = _get_value(body, ["会社名"])
    prefecture = _get_value(body, ["都道府県"])
    job_overview = _get_value(body, KEY_MAPPINGS["事業概要"])
    market_growth = _get_value(body, KEY_MAPPINGS["マーケット成長性"])
    hp_url = _get_value(body, ["法人HP URL"])
    sales_ratio = _get_value(body, ["売上構成比"])
    focus = _get_value(body, ["今後の注力領域"])
    snapshot = _get_value(body, ["企業スナップショット"])
    usp_by_size = _extract_前職規模別_usps(body) or _get_value(body, ["前職規模別アトラクトUSP", "前職規模別USP"])
    decision_maker = _get_value(body, ["採用意思決定者"])
    kuchikomi = _extract_口コミ(body)

    # 労働条件
    shukka = _get_value(body, ["出張"])
    zangyo = _get_value(body, ["残業時間"])
    workstyle = _get_value(body, KEY_MAPPINGS["休日・直行直帰・リモート"])
    if not workstyle:
        hi = _get_value(body, ["休日数"])
        remote = _get_value(body, ["リモート可否"])
        if hi or remote:
            workstyle = "、".join(x for x in [hi, remote] if x)
    fukuri = _get_value(body, ["福利厚生"])

    # 候補者タイプ別（①〜③）
    type1_adopt = _get_value(body, ["①電気工事士もち、電気施工管理未経験", "①電気工事士もち、施工管理未経験"])
    type1_appeal = _get_value(body, ["訴求・差別化"])  # テーブル内の列
    # 候補者タイプ別テーブルは行ごとに 候補者タイプ | 採用 | 訴求・差別化 の形式
    # ①の行の採用・訴求を取るには別のパースが必要
    type1_row = _extract_candidate_type_row(body, "①")
    type2_row = _extract_candidate_type_row(body, "②")
    type3_row = _extract_candidate_type_row(body, "③")

    # 差別化メモ（同エリア×同セグメント差別化メモ セクションの内容）
    diff_memo = _extract_section_content(body, "同エリア×同セグメント差別化メモ")

    # その他のセクションはそのまま維持（仕事内容、採用条件、評価、面接、その他）
    work_content = _extract_section(body, "仕事内容")
    adopt_cond = _extract_section(body, "採用条件", drop_rows=["採用意思決定者"])
    eval_section = _extract_section(body, "評価・キャリアアップ")
    interview_section = _extract_section(body, "面接・選考")
    other_section = _extract_section(body, "その他")
    update_history = _extract_section(body, "更新履歴")

    # 新形式で組み立て
    new_body = f"""# 法人情報：{company_name or '(会社名)'}

## 企業情報

| 項目 | 内容 |
|------|------|
| 会社名 | {company_name or ""} |
| 都道府県 | {prefecture or ""} |
| 事業概要 | {job_overview or ""} |
| マーケット成長性 | {market_growth or ""} |
| 法人HP URL | {hp_url or ""} |
| 売上構成比 | {sales_ratio or ""} |
| 今後の注力領域 | {focus or ""} |
| 企業スナップショット | {snapshot or ""} |
| 前職規模別USP | {usp_by_size or ""} |
| 採用意思決定者 | {decision_maker or ""} |
| 口コミ評価傾向 | {kuchikomi or ""} |

{work_content}

## 労働条件

| 項目 | 内容 |
|------|------|
| 出張 | {shukka or ""} |
| 残業時間 | {zangyo or ""} |
| 休日・直行直帰・リモート | {workstyle or ""} |
| 福利厚生 | {fukuri or ""} |

{eval_section}
{interview_section}
{other_section}

## 候補者別訴求

| セグメント | 採用 | 訴求・差別化 |
|------------|------|--------------|
| ①電気工事士もち、施工管理未経験 | {type1_row.get("adopt", "")} | {type1_row.get("appeal", "")} |
| ②施工管理資格もち、マネジメント未経験 | {type2_row.get("adopt", "")} | {type2_row.get("appeal", "")} |
| ③施工管理資格もち、マネジメント経験あり | {type3_row.get("adopt", "")} | {type3_row.get("appeal", "")} |
| 大手出身者向け（1,000名以上） | - | {_get_usp_for_size(usp_by_size, "大手")} |
| 中堅出身者向け（100〜999名） | - | {_get_usp_for_size(usp_by_size, "中堅")} |
| 零細出身者向け（100名未満） | - | {_get_usp_for_size(usp_by_size, "零細")} |

## 同エリア×同セグメント差別化メモ

{diff_memo}

{update_history}
"""

    return "---" + parts[1] + "---\n" + new_body


def _get_usp_for_size(usp_text: str, size: str) -> str:
    """前職規模別USPテーブルから特定サイズのUSPを抽出"""
    if not usp_text:
        return ""
    for part in usp_text.split("。"):
        if part.strip().startswith(size + "："):
            return part.split("：", 1)[1].strip()
    return ""


def _extract_candidate_type_row(body: str, prefix: str) -> dict:
    """候補者タイプ別テーブルから①〜③の行を抽出"""
    result = {"adopt": "", "appeal": ""}
    # ## 候補者タイプ別 の後のテーブルをパース（\n\n または \n の両方に対応）
    m = re.search(r"## 候補者タイプ別\s*\n+(.*?)(?=\n## |\Z)", body, re.DOTALL)
    if not m:
        return result
    table = m.group(1)
    for line in table.splitlines():
        if "|" not in line:
            continue
        # セパレータ行をスキップ
        stripped = line.strip()
        if re.match(r"^\|[\s\-:]+\|", stripped):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) >= 3:
            first = cells[0]
            # ①〜③で始まる、または数字＋．で始まる行をマッチ
            if first.startswith(prefix) or (prefix == "①" and first.startswith("1.")):
                result["adopt"] = cells[1] if len(cells) > 1 else ""
                result["appeal"] = cells[2] if len(cells) > 2 else ""
                break
    return result


def _extract_section_content(body: str, section_name: str) -> str:
    """セクションの見出し以降の内容を取得（次の##まで）"""
    m = re.search(rf"## {re.escape(section_name)}\s*\n\n?(.*?)(?=\n## |\Z)", body, re.DOTALL)
    if not m:
        return ""
    return m.group(1).strip()


def _extract_section(body: str, section_name: str, drop_rows: list[str] | None = None) -> str:
    """セクション全体（見出し含む）を取得。drop_rows で指定した項目の行を除外"""
    m = re.search(rf"(## {re.escape(section_name)}\s*\n\n?.*?)(?=\n## |\Z)", body, re.DOTALL)
    if not m:
        return ""
    section = m.group(1).strip()
    if drop_rows:
        lines = section.split("\n")
        new_lines = []
        for line in lines:
            if "|" in line:
                cells = [c.strip() for c in line.split("|")[1:-1]]
                if cells and cells[0] in drop_rows:
                    continue
            new_lines.append(line)
        section = "\n".join(new_lines)
    return section


def main():
    import argparse
    parser = argparse.ArgumentParser(description="法人マスタを新構造に移行")
    parser.add_argument("--dry-run", action="store_true", help="移行内容を表示、ファイルは更新しない")
    args = parser.parse_args()

    if not MASTER_DIR.exists():
        print("法人マスタディレクトリがありません。", file=sys.stderr)
        sys.exit(1)

    targets = []
    for f in MASTER_DIR.glob("*.md"):
        if f.name.startswith("_") or f.name in ("マスタ項目一覧.md", "README.md"):
            continue
        content = f.read_text(encoding="utf-8")
        if "## 企業情報" in content and "| 事業概要 |" in content:
            continue  # 既に新形式
        targets.append((f, content))

    if not targets:
        print("移行対象の法人マスタはありません。", file=sys.stderr)
        return

    print(f"移行対象: {len(targets)} 件", file=sys.stderr)
    for f, _ in targets:
        print(f"  - {f.stem}", file=sys.stderr)

    if args.dry_run:
        print("\n--dry-run のためファイルは更新しません。", file=sys.stderr)
        # 1件だけサンプル表示
        f, content = targets[0]
        migrated = migrate_file(content)
        print(f"\n【{f.stem} の移行サンプル（先頭500文字）】", file=sys.stderr)
        print(migrated[:500], file=sys.stderr)
        return

    updated = 0
    for f, content in targets:
        try:
            migrated = migrate_file(content)
            f.write_text(migrated, encoding="utf-8")
            updated += 1
            print(f"✅ 移行: {f.stem}", file=sys.stderr)
        except Exception as e:
            print(f"⚠️ エラー {f.stem}: {e}", file=sys.stderr)

    print(f"\n完了: {updated}/{len(targets)} 件を移行", file=sys.stderr)


if __name__ == "__main__":
    main()
