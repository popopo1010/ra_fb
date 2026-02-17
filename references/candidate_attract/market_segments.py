"""
マーケットセグメント定義（工種×用途の2軸構造＋マーケットサイズ）

建設業界のマーケットを構造化。プレイブック・法人比較で参照。
"""

# 建設投資総額（参考）
TOTAL_MARKET = "約75兆円（民間67%、公共33%）"

# 工種軸：施工管理の専門性
WORK_TYPES = {
    "電気系": {
        "market_size": "設備19兆円の約半数（約9〜10兆円）",
        "note": "DC・工場・再エネで需要旺盛。建築・土木両方に横断",
    },
    "土木": {
        "market_size": "土木工事 約35兆円",
        "note": "送配電・道路・河川。再エネ土木・公共で成長",
    },
    "建築": {
        "market_size": "建築工事 約40兆円",
        "note": "物流・オフィス・工場・DCで大型案件",
    },
    "管工事": {
        "market_size": "空調・衛生設備（設備投資の一部）",
        "note": "DC・工場・病院。DCは冷却が重要",
    },
}

# 用途軸：案件の受け皿（建物・施設タイプ）
USE_TYPES = {
    "DC": {
        "market_size": "急拡大（国策・脱炭素）",
        "growth": "高",
        "note": "データセンター。大型案件続出",
    },
    "再エネ": {
        "market_size": "高成長（補助金・FIT・蓄電池）",
        "growth": "高",
        "note": "太陽光・風力・蓄電池。政府目標で需要拡大",
    },
    "物流": {
        "market_size": "前年比10%超",
        "growth": "高",
        "note": "EC・倉庫。大型案件続出",
    },
    "工場": {
        "market_size": "半導体・脱炭素で大型案件",
        "growth": "高",
        "note": "製造業の設備投資",
    },
    "オフィス": {
        "market_size": "都市再開発",
        "growth": "中",
        "note": "テナントビル、リニューアル",
    },
    "公共": {
        "market_size": "生活基盤50%、産業基盤34%",
        "growth": "安定",
        "note": "インフラ老朽化対応。一定需要",
    },
    "住宅": {
        "market_size": "約16兆円",
        "growth": "安定",
        "note": "リフォーム堅調。地域密着",
    },
    "商業施設": {
        "market_size": "商業施設工事",
        "growth": "中",
        "note": "店舗・商業ビル。脱炭素化・長寿命化",
    },
    "自衛隊": {
        "market_size": "防衛関連施設",
        "growth": "中",
        "note": "特殊需要",
    },
}

# フラットなセグメント→工種 or 用途 のマッピング（法人マスタのセグメント用）
SEGMENT_TO_AXIS = {
    "電気系": "工種",
    "土木": "工種",
    "建築": "工種",
    "管工事": "工種",
    "DC": "用途",
    "再エネ": "用途",
    "物流": "用途",
    "工場": "用途",
    "オフィス": "用途",
    "公共": "用途",
    "住宅": "用途",
    "商業施設": "用途",
    "自衛隊": "用途",
    "その他": "その他",
}


def get_segment_info(segment: str) -> dict:
    """セグメントのマーケット情報を取得"""
    if segment in WORK_TYPES:
        info = WORK_TYPES[segment].copy()
        info["axis"] = "工種"
        return info
    if segment in USE_TYPES:
        info = USE_TYPES[segment].copy()
        info["axis"] = "用途"
        return info
    return {"market_size": "", "growth": "", "note": "", "axis": "その他"}
