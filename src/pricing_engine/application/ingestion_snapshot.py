import argparse
import logging
import re
from datetime import datetime, date
from pathlib import Path

import pandas as pd
import mysql.connector

from configs.settings import (
    STAGING_DIR,
    OUTPUT_DIR,
    MYSQL_CONFIG,
)

logger = logging.getLogger(__name__)

DATA_FILE = STAGING_DIR / "corrected_price_4.xlsx"

FILENAME_RE = re.compile(r"(\d{4}_\d{2}_\d{2})")


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def extract_date_from_filename(filename: str) -> date:
    match = FILENAME_RE.search(filename)
    if not match:
        raise ValueError(f"Cannot extract date from filename: {filename}")

    return datetime.strptime(match.group(1), "%Y_%m_%d").date()


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.lower()
    )
    return df


def mysql_connection():
    if not MYSQL_CONFIG["host"]:
        raise ValueError("MYSQL configuration is incomplete. Check .env file.")

    return mysql.connector.connect(
        host=MYSQL_CONFIG["host"],
        port=MYSQL_CONFIG["port"],
        user=MYSQL_CONFIG["user"],
        password=MYSQL_CONFIG["password"],
        database=MYSQL_CONFIG["database"],
        autocommit=False,
    )


# ---------------------------------------------------------
# Core ingestion
# ---------------------------------------------------------

def ingest_dataframe(df: pd.DataFrame, snapshot_date: date) -> int:
    conn = mysql_connection()
    cursor = conn.cursor()

    insert_sql = """
        INSERT INTO price_snapshots
        (snapshot_date, article, stock, price, price_group, created_at)
        VALUES (%s, %s, %s, %s, %s, NOW())
        ON DUPLICATE KEY UPDATE
            stock = VALUES(stock),
            price = VALUES(price),
            price_group = VALUES(price_group),
            updated_at = NOW()
    """

    rows_written = 0

    try:
        for _, row in df.iterrows():
            cursor.execute(
                insert_sql,
                (
                    snapshot_date,
                    row["article"],
                    int(row["stock"]) if pd.notna(row["stock"]) else 0,
                    float(row["price"]) if pd.notna(row["price"]) else None,
                    row["price_group"],
                )
            )
            rows_written += 1

        conn.commit()

    except Exception as e:
        conn.rollback()
        logger.error(f"Database ingestion failed: {e}")
        raise

    finally:
        cursor.close()
        conn.close()

    return rows_written


# ---------------------------------------------------------
# Load current staging file
# ---------------------------------------------------------

def load_data_file() -> pd.DataFrame:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Data file not found: {DATA_FILE}")

    logger.info(f"Loading data file: {DATA_FILE.name}")

    df = pd.read_excel(DATA_FILE)
    df = normalize_columns(df)

    required = {"article", "stock", "price", "price_group"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in data file: {missing}")

    df = df[["article", "stock", "price", "price_group"]].copy()
    df["article"] = df["article"].astype(str).str.strip()

    return df


# ---------------------------------------------------------
# Historical ingestion
# ---------------------------------------------------------

def ingest_historical():
    files = sorted(
        [
            f for f in OUTPUT_DIR.glob("Лига-М_запчасти_*.xlsx")
            if not f.name.startswith("~$")
        ]
    )

    if not files:
        logger.info("No historical files found.")
        return

    total_rows = 0

    for file in files:
        snapshot_date = extract_date_from_filename(file.name)

        logger.info(f"Processing {file.name} → {snapshot_date}")

        df = pd.read_excel(file, header=6)
        df = normalize_columns(df)

        column_map = {
            "артикул": "article",
            "остаток": "stock",
            "цена (с ндс)": "price",
            "ценовая группа": "price_group",
        }

        df = df.rename(columns=column_map)
        df = df[["article", "stock", "price", "price_group"]]
        df["article"] = df["article"].astype(str).str.strip()

        rows = ingest_dataframe(df, snapshot_date)
        total_rows += rows

        logger.info(f"Upserted rows: {rows}")

    logger.info(f"TOTAL upserted rows: {total_rows}")


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--historical",
        action="store_true",
        help="Ingest all formatted output files as historical snapshots",
    )
    args = parser.parse_args()

    logger.info("START → ingestion_snapshot")

    if args.historical:
        ingest_historical()
    else:
        df = load_data_file()
        snapshot_date = date.today()

        rows = ingest_dataframe(df, snapshot_date)
        logger.info(f"Upserted rows: {rows}")

    logger.info("DONE → ingestion_snapshot")


if __name__ == "__main__":
    main()