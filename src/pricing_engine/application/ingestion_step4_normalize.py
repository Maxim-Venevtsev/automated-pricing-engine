import logging
import re
import pandas as pd

from configs.settings import STAGING_DIR

logger = logging.getLogger(__name__)

INPUT_FILE = STAGING_DIR / "corrected_price_3.xlsx"
OUTPUT_FILE = STAGING_DIR / "corrected_price_4.xlsx"


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def fix_name(text):
    """
    Очистка и нормализация наименований
    """
    if pd.isna(text):
        return ""

    text = str(text)

    # " / " → "/", " , " → ", "
    text = text.replace(" / ", "/").replace(" , ", ", ")

    # вставить пробел после точки перед буквой: ".кг" → ". кг"
    text = re.sub(r"\.(?=[А-Яа-яA-Za-z])", ". ", text)

    # 1кг → 1 кг, 2шт → 2 шт, 250мл → 250 мл
    text = re.sub(r"(\d)(шт|кг|мл)", r"\1 \2", text, flags=re.IGNORECASE)

    # убрать двойные пробелы
    text = re.sub(r"\s{2,}", " ", text)

    # убрать первую группу до первого пробела (артикул)
    if " " in text:
        text = text.split(" ", 1)[1]

    return text.strip().upper()


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():
    logger.info("START → ingestion_step4_normalize")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    try:
        df = pd.read_excel(INPUT_FILE)
    except Exception as e:
        logger.error(f"Failed to read Excel file: {e}")
        raise

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

    rows_before = len(df)
    logger.info(f"Rows loaded: {rows_before}")

    # ---------------------------------------------------------
    # Normalize price_group
    # ---------------------------------------------------------
    df["price_group"] = (
        df["price_group"]
        .astype(str)
        .str.replace("HYUNDAI", "HYUNDAI/KIA", case=False)
        .str.upper()
        .str.strip()
    )

    # ---------------------------------------------------------
    # Normalize article
    # ---------------------------------------------------------
    df["article"] = (
        df["article"]
        .astype(str)
        .str.replace("-", "", regex=False)
        .str.strip()
    )

    # ---------------------------------------------------------
    # Normalize name
    # ---------------------------------------------------------
    df["name"] = df["name"].apply(fix_name)

    # ---------------------------------------------------------
    # Normalize price (string → float)
    # ---------------------------------------------------------
    df["price"] = (
        df["price"]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .str.replace(" ", "", regex=False)
    )

    df["price"] = pd.to_numeric(df["price"], errors="coerce")

    if df["price"].isna().any():
        raise RuntimeError("Invalid price values detected after conversion.")

    # ---------------------------------------------------------
    # Normalize stock
    # ---------------------------------------------------------
    df["stock"] = (
        df["stock"]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .str.replace(" ", "", regex=False)
    )

    df["stock"] = pd.to_numeric(df["stock"], errors="coerce").fillna(0)

    # ---------------------------------------------------------
    # Save normalized file
    # ---------------------------------------------------------
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:
        df.to_excel(OUTPUT_FILE, index=False)
    except Exception as e:
        logger.error(f"Failed to save normalized file: {e}")
        raise

    logger.info(f"Saved normalized file: {OUTPUT_FILE.name}")
    logger.info("DONE → ingestion_step4_normalize")


if __name__ == "__main__":
    main()