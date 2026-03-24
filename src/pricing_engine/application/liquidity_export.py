import logging
from datetime import datetime

import pandas as pd
import mysql.connector

from configs.settings import (
    MYSQL_CONFIG,
    REFERENCE_DIR,
)

logger = logging.getLogger(__name__)

# Operational window (можно позже вынести в settings)
OPERATIONAL_WINDOW = 28

OUTPUT_FILE = REFERENCE_DIR / "liquidity_category.xlsx"


# ---------------------------------------------------------
# DB connection
# ---------------------------------------------------------

def get_connection():
    if not MYSQL_CONFIG["host"]:
        raise ValueError("MYSQL configuration is incomplete. Check .env file.")

    return mysql.connector.connect(
        host=MYSQL_CONFIG["host"],
        port=MYSQL_CONFIG["port"],
        user=MYSQL_CONFIG["user"],
        password=MYSQL_CONFIG["password"],
        database=MYSQL_CONFIG["database"],
    )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    logger.info("START → liquidity_export")

    conn = get_connection()

    try:
        query = """
            SELECT article, category, window_days
            FROM liquidity_category
            WHERE window_days = %s
        """

        df = pd.read_sql(query, conn, params=(OPERATIONAL_WINDOW,))

    finally:
        conn.close()

    if df.empty:
        raise ValueError(
            f"No liquidity data found for window {OPERATIONAL_WINDOW}."
        )

    df["updated_at"] = datetime.now()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:
        df.to_excel(OUTPUT_FILE, index=False)
    except Exception as e:
        logger.error(f"Failed to export liquidity file: {e}")
        raise

    logger.info(
        f"Liquidity category exported for window {OPERATIONAL_WINDOW} days."
    )
    logger.info(f"Saved to: {OUTPUT_FILE.name}")
    logger.info("DONE → liquidity_export")


if __name__ == "__main__":
    main()