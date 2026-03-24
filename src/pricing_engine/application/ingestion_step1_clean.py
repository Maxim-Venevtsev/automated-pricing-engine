import logging
from pathlib import Path
import pandas as pd

from configs.settings import INCOMING_DIR, STAGING_DIR

logger = logging.getLogger(__name__)

OUTPUT_FILE = STAGING_DIR / "corrected_price_1.xlsx"


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def get_latest_file(folder: Path) -> Path:
    files = [
        f for f in folder.iterdir()
        if f.suffix.lower() in (".xlsx", ".xls", ".csv")
    ]

    if not files:
        raise FileNotFoundError(f"No files found in {folder}")

    return max(files, key=lambda f: f.stat().st_mtime)


# ---------------------------------------------------------
# Main logic
# ---------------------------------------------------------

def main():
    logger.info("START → ingestion_step1_clean")

    # ---------------------------------------------------------
    # Find latest incoming file
    # ---------------------------------------------------------
    latest_file = get_latest_file(INCOMING_DIR)
    logger.info(f"Found incoming file: {latest_file.name}")

    # ---------------------------------------------------------
    # Load raw Excel as STRING (critical!)
    # ---------------------------------------------------------
    try:
        df = pd.read_excel(latest_file, header=None, dtype=str)
    except Exception as e:
        logger.error(f"Failed to read Excel file: {e}")
        raise

    # ---------------------------------------------------------
    # Extract header row (10th row in Excel → index 9)
    # ---------------------------------------------------------
    HEADER_ROW_INDEX = 9

    if len(df) <= HEADER_ROW_INDEX:
        raise RuntimeError("Source file does not contain expected header row.")

    df.columns = df.iloc[HEADER_ROW_INDEX].astype(str).str.strip()
    df = df.iloc[HEADER_ROW_INDEX + 1:].reset_index(drop=True)

    # ---------------------------------------------------------
    # Drop completely empty rows
    # ---------------------------------------------------------
    df = df.dropna(how="all")

    # ---------------------------------------------------------
    # Normalize expected columns
    # ---------------------------------------------------------
    column_mapping = {
        "Ценовая группа": "price_group",
        "Артикул": "article_raw",
        "Номенклатура": "name",
        "Остаток": "stock",
        "Цена": "price",
        "Ед.": "unit",
    }

    df = df.rename(columns=column_mapping)

    # ---------------------------------------------------------
    # Rebuild article from name (first token)
    # ---------------------------------------------------------
    if "name" not in df.columns:
        raise RuntimeError("Column 'Номенклатура' not found in source file.")

    df["article"] = df["name"].astype(str).str.strip().str.split().str[0]

    # ---------------------------------------------------------
    # Contract enforcement
    # ---------------------------------------------------------
    required_columns = [
        "price_group",
        "article",
        "name",
        "stock",
        "unit",
        "price",
    ]

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise RuntimeError(f"Missing required columns: {missing}")

    df = df[required_columns]

    # ---------------------------------------------------------
    # Save cleaned file
    # ---------------------------------------------------------
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:
        df.to_excel(OUTPUT_FILE, index=False)
    except Exception as e:
        logger.error(f"Failed to save cleaned file: {e}")
        raise

    logger.info(f"Saved cleaned file: {OUTPUT_FILE.name}")
    logger.info("DONE → ingestion_step1_clean")


if __name__ == "__main__":
    main()