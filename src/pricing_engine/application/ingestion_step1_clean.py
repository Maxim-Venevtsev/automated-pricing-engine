import logging
from pathlib import Path
import pandas as pd

from configs.settings import INCOMING_DIR, STAGING_DIR

logger = logging.getLogger(__name__)

OUTPUT_FILE = STAGING_DIR / "corrected_price_1.xlsx"

OLD_HEADER_CANDIDATES = {"Ценовая группа", "Артикул", "Номенклатура", "Остаток", "Цена"}
NEW_HEADER_CANDIDATES = {"Артикул", "Номенклатура", "Бренд", "Остаток", "Цена"}


def get_latest_file(folder: Path) -> Path:
    files = [
        f for f in folder.iterdir()
        if f.suffix.lower() in (".xlsx", ".xls", ".csv")
    ]

    if not files:
        raise FileNotFoundError(f"No files found in {folder}")

    return max(files, key=lambda f: f.stat().st_mtime)


def normalize_text(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def detect_header_row(df: pd.DataFrame, max_scan_rows: int = 20) -> int:
    """
    Detect header row for both known supplier formats.

    Old format:
      - several service/header rows above the actual header
      - expected header contains: Ценовая группа / Артикул / Номенклатура / Остаток / Цена / Ед.

    New format:
      - first row is the header
      - expected header contains: Артикул / Номенклатура / Бренд / Остаток / Цена
    """
    scan_limit = min(len(df), max_scan_rows)

    for idx in range(scan_limit):
        row_values = {normalize_text(v) for v in df.iloc[idx].tolist()}
        if OLD_HEADER_CANDIDATES.issubset(row_values) or NEW_HEADER_CANDIDATES.issubset(row_values):
            return idx

    raise RuntimeError(
        "Could not detect header row in source file. "
        "Expected old format header or new format header within the first 20 rows."
    )


def extract_article(df: pd.DataFrame) -> pd.Series:
    """
    Preserve article as text.
    Priority:
      1) explicit article column from the file
      2) first token from name as fallback
    """
    article_from_column = (
        df["article_raw"].astype(str).str.strip()
        if "article_raw" in df.columns
        else pd.Series([""] * len(df), index=df.index, dtype="object")
    )

    article_from_name = (
        df["name"].astype(str).str.strip().str.split().str[0]
        if "name" in df.columns
        else pd.Series([""] * len(df), index=df.index, dtype="object")
    )

    article = article_from_column.where(article_from_column != "", article_from_name)
    return article.astype(str).str.strip()


def main():
    logger.info("START → ingestion_step1_clean")

    latest_file = get_latest_file(INCOMING_DIR)
    logger.info(f"Found incoming file: {latest_file.name}")

    try:
        df = pd.read_excel(latest_file, header=None, dtype=str)
    except Exception as e:
        logger.error(f"Failed to read Excel file: {e}")
        raise

    header_row_index = detect_header_row(df)
    logger.info(f"Detected header row at Excel row index: {header_row_index}")

    df.columns = df.iloc[header_row_index].astype(str).str.strip()
    df = df.iloc[header_row_index + 1:].reset_index(drop=True)

    df = df.dropna(how="all").copy()

    column_mapping = {
        "Ценовая группа": "price_group",
        "Бренд": "price_group",
        "Артикул": "article_raw",
        "Номенклатура": "name",
        "Остаток": "stock",
        "Цена": "price",
        "Ед.": "unit",
    }
    df = df.rename(columns=column_mapping)

    if "name" not in df.columns:
        raise RuntimeError("Column 'Номенклатура' not found in source file.")

    df["article"] = extract_article(df)

    if "unit" not in df.columns:
        df["unit"] = "шт"
    else:
        df["unit"] = df["unit"].fillna("").astype(str).str.strip().replace("", "шт")

    df["name"] = df["name"].astype(str).str.strip()
    df["price_group"] = df["price_group"].astype(str).str.strip()
    df["stock"] = df["stock"].astype(str).str.strip()
    df["price"] = df["price"].astype(str).str.strip()

    df = df[(df["article"] != "") & (df["name"] != "")].copy()

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

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:
        df.to_excel(OUTPUT_FILE, index=False)
    except Exception as e:
        logger.error(f"Failed to save cleaned file: {e}")
        raise

    logger.info(f"Rows saved: {len(df)}")
    logger.info(f"Saved cleaned file: {OUTPUT_FILE}")
    logger.info("DONE → ingestion_step1_clean")


if __name__ == "__main__":
    main()
