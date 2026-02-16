"""設定の一元管理"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


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
