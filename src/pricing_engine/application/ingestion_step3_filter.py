import logging
import pandas as pd

from configs.settings import STAGING_DIR

logger = logging.getLogger(__name__)

INPUT_FILE = STAGING_DIR / "corrected_price_2.xlsx"
OUTPUT_FILE = STAGING_DIR / "corrected_price_3.xlsx"


def main():
    logger.info("START → ingestion_step3_filter")
    logger.info("STEP 3: REMOVE EMPTY price_group")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    # ---------------------------------------------------------
    # Load data
    # ---------------------------------------------------------
    try:
        df = pd.read_excel(INPUT_FILE)
    except Exception as e:
        logger.error(f"Failed to read Excel file: {e}")
        raise

    if "price_group" not in df.columns:
        raise RuntimeError("Column 'price_group' not found.")

    rows_before = len(df)
    logger.info(f"Rows before filtering: {rows_before}")

    # ---------------------------------------------------------
    # Remove real NaN
    # ---------------------------------------------------------
    df = df[df["price_group"].notna()]

    # ---------------------------------------------------------
    # Normalize string
    # ---------------------------------------------------------
    df["price_group"] = df["price_group"].astype(str).str.strip()

    # ---------------------------------------------------------
    # Remove empty / pseudo-null values
    # ---------------------------------------------------------
    invalid_values = ["", "nan", "none", "null"]
    df = df[~df["price_group"].str.lower().isin(invalid_values)]

    rows_after = len(df)
    removed = rows_before - rows_after

    logger.info(f"Rows removed: {removed}")
    logger.info(f"Rows after filtering: {rows_after}")

    if rows_after == 0:
        raise RuntimeError("All rows removed at ingestion_step3_filter stage!")

    # ---------------------------------------------------------
    # Save result
    # ---------------------------------------------------------
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:
        df.to_excel(OUTPUT_FILE, index=False)
    except Exception as e:
        logger.error(f"Failed to save filtered file: {e}")
        raise

    logger.info(f"Saved filtered file: {OUTPUT_FILE.name}")
    logger.info("DONE → ingestion_step3_filter")


if __name__ == "__main__":
    main()