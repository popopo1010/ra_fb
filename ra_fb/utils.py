"""共通ユーティリティ。茂野・重野・大城は同一人物"""

from pathlib import Path


def extract_ra_from_path(filepath: Path) -> str:
    """ファイルパスからRA名を推測。茂野・重野・大城は茂野に統一"""
    parts = filepath.parts
    if "小山田" in parts:
        return "小山田"
    if any(p in parts for p in ("茂野", "重野", "大城")):
        return "茂野"
    return ""


def extract_ra_from_filename(name: str) -> str:
    """ファイル名からRA名を推測。茂野・重野・大城は茂野に統一"""
    n = name or ""
    if "小山田" in n:
        return "小山田"
    if any(p in n for p in ("茂野", "重野", "大城")):
        return "茂野"
    return ""


def extract_company_name(stem: str, ra_name: str) -> str:
    """ファイル名（拡張子なし）から会社名を推測。形式: {企業名略}_{RA}_{連番}"""
    parts = (stem or "").split("_")
    if ra_name and ra_name in parts:
        idx = parts.index(ra_name)
        return "_".join(parts[:idx]) if idx > 0 else ""
    if parts and parts[-1].isdigit():
        return "_".join(parts[:-1]) if len(parts) > 1 else (parts[0] or "")
    return stem or ""
