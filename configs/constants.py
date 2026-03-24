"""
Business constants (domain/business rules).

Keep this file free of paths and secrets.
Paths/env belong to configs/settings.py.
"""

# ---------------------------------------------------------
# New item logic
# ---------------------------------------------------------

NEW_FLAG_VALUE = "New!"
NEW_DAYS = 14
RESTART_THRESHOLD_DAYS = 90

# ---------------------------------------------------------
# Liquidity / special offer logic
# ---------------------------------------------------------

# Items included in "специальное предложение" (by liquidity category)
SPECIAL_OFFER_LIQUIDITY = ("dead", "low")

# Exclude items from "специальное предложение" if they have any of these flags
EXCLUDE_FLAGS_FROM_SPECIAL_OFFER = (NEW_FLAG_VALUE,)

# ---------------------------------------------------------
# Sheet names
# ---------------------------------------------------------

SHEET_ALL = "все зч"
SHEET_HYUNDAI_KIA = "Hyundai_Kia"
SHEET_SPECIAL = "специальное предложение"

# Price group filter for Hyundai/Kia sheet
HYUNDAI_KIA_PRICE_GROUP = "HYUNDAI/KIA"