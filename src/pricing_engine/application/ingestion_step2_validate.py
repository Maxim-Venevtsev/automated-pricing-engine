import logging
from pathlib import Path
import pandas as pd

from configs.settings import STAGING_DIR

logger = logging.getLogger(__name__)

INPUT_FILE = STAGING_DIR / "corrected_price_1.xlsx"
OUTPUT_FILE = STAGING_DIR / "corrected_price_2.xlsx"


def main():
    logger.info("START → ingestion_step2_validate")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    logger.info(f"Loading file: {INPUT_FILE.name}")

    try:
        df = pd.read_excel(INPUT_FILE)
    except Exception as e:
        logger.error(f"Failed to read Excel file: {e}")
        raise

    # ---------------------------------------------------------
    # Required columns (contract)
    # ---------------------------------------------------------
    required_columns = [
        "price_group",
        "article",
        "name",
        "stock",
        "unit",
        "price",
    ]

    # Check missing columns
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise RuntimeError(f"Missing required columns: {missing}")

    # ---------------------------------------------------------
    # Check duplicate columns
    # ---------------------------------------------------------
    if df.columns.duplicated().any():
        duplicates = df.columns[df.columns.duplicated()].tolist()
        raise RuntimeError(f"Duplicate column names found: {duplicates}")

    # ---------------------------------------------------------
    # Drop completely empty rows (safety)
    # ---------------------------------------------------------
    df = df.dropna(how="all")

    # ---------------------------------------------------------
    # Enforce column order
    # ---------------------------------------------------------
    df = df[required_columns]

    # ---------------------------------------------------------
    # Save validated file
    # ---------------------------------------------------------
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:
        df.to_excel(OUTPUT_FILE, index=False)
    except Exception as e:
        logger.error(f"Failed to save validated file: {e}")
        raise

    logger.info(f"Saved validated file: {OUTPUT_FILE.name}")
    logger.info("DONE → ingestion_step2_validate")


if __name__ == "__main__":
    main()