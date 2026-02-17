"""設定の一元管理"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# パス定数（一箇所で管理）
DATA_DIR = ROOT / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
REF_DIR = ROOT / "references"

# 入力データ
LONG_CALLS_DIR = INPUT_DIR / "ra"  # 初回架電（RA）文字起こし
CA_DIR = INPUT_DIR / "ca"  # 法人面談（CA）議事録

# 出力データ
MASTER_DIR = OUTPUT_DIR / "法人マスタ"  # 法人情報（FB生成時に自動格納）

# 参照資料
MANUAL_DIR = REF_DIR / "manual"  # 架電マニュアル・PSS
CANDIDATE_ATTRACT_DIR = REF_DIR / "candidate_attract"  # 候補者アトラクト


def load_env() -> None:
    """ .env を読み込み"""
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
        return
    except ImportError:
        pass
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())
