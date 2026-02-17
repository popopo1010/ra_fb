"""
RA FB システム - 初回架電・法人面談のフィードバック生成
"""

from .config import (
    ROOT,
    load_env,
    DATA_DIR,
    INPUT_DIR,
    OUTPUT_DIR,
    REF_DIR,
    MASTER_DIR,
    LONG_CALLS_DIR,
    CA_DIR,
    MANUAL_DIR,
    CANDIDATE_ATTRACT_DIR,
)
from .utils import extract_ra_from_path, extract_ra_from_filename, extract_company_name
from .feedback import generate_feedback_ra, generate_feedback_ca
from .slack import post_to_slack
from .company import extract_and_save_company_info, compare_companies, list_companies_by_region_segment

__all__ = [
    "ROOT",
    "DATA_DIR",
    "INPUT_DIR",
    "OUTPUT_DIR",
    "REF_DIR",
    "MASTER_DIR",
    "LONG_CALLS_DIR",
    "CA_DIR",
    "MANUAL_DIR",
    "CANDIDATE_ATTRACT_DIR",
    "load_env",
    "extract_ra_from_path",
    "extract_ra_from_filename",
    "extract_company_name",
    "generate_feedback_ra",
    "generate_feedback_ca",
    "post_to_slack",
    "extract_and_save_company_info",
    "compare_companies",
    "list_companies_by_region_segment",
]
