#!/usr/bin/env python3
"""後方互換: slack_server のエイリアス"""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).parent / "slack_server.py"), run_name="__main__")
