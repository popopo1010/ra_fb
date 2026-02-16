#!/usr/bin/env python3
"""後方互換: cli.py ra のエイリアス"""
import sys
if len(sys.argv) >= 2 and sys.argv[1] not in ("ra", "ca"):
    sys.argv.insert(1, "ra")
elif len(sys.argv) < 2:
    sys.argv.insert(1, "ra")
import runpy
runpy.run_path(__file__.replace("generate_feedback.py", "cli.py"), run_name="__main__")
