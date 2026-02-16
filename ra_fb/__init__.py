"""
RA FB システム - 初回架電・法人面談のフィードバック生成
"""

from .config import ROOT, load_env
from .utils import extract_ra_from_path, extract_ra_from_filename, extract_company_name
from .feedback import generate_feedback_ra, generate_feedback_ca
from .slack import post_to_slack

__all__ = [
    "ROOT",
    "load_env",
    "extract_ra_from_path",
    "extract_ra_from_filename",
    "extract_company_name",
    "generate_feedback_ra",
    "generate_feedback_ca",
    "post_to_slack",
]
