import logging
from datetime import timedelta
import pandas as pd
import mysql.connector

from configs.settings import MYSQL_CONFIG

logger = logging.getLogger(__name__)


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
        autocommit=False,
    )


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------

def load_snapshots(conn):
    query = "SELECT article, snapshot_date, stock FROM price_snapshots"
    df = pd.read_sql(query, conn)
    df["snapshot_date"] = pd.to_datetime(df["snapshot_date"])
    return df


def load_thresholds(conn):
    query = "SELECT * FROM liquidity_thresholds"
    return pd.read_sql(query, conn)


# ---------------------------------------------------------
# Calculate turnover for one window
# ---------------------------------------------------------

def calculate_turnover(df, window_days):

    max_date = df["snapshot_date"].max()
    window_start = max_date - timedelta(days=window_days)

    df_window = df[df["snapshot_date"] >= window_start].copy()
    df_window = df_window.sort_values(["article", "snapshot_date"])

    first_seen = df.groupby("article")["snapshot_date"].min().reset_index()
    first_seen.columns = ["article", "first_seen"]

    df_window = df_window.merge(first_seen, on="article", how="left")

    df_window["prev_stock"] = df_window.groupby("article")["stock"].shift(1)
    df_window["sold"] = (df_window["prev_stock"] - df_window["stock"]).clip(lower=0)
    df_window["sold"] = df_window["sold"].fillna(0)

    grouped = df_window.groupby("article").agg(
        total_sold=("sold", "sum"),
        avg_stock=("stock", "mean"),
        first_seen=("first_seen", "first")
    ).reset_index()

    grouped["window_days"] = window_days
    grouped["period_start"] = window_start
    grouped["period_end"] = max_date
    grouped["age_days"] = (max_date - grouped["first_seen"]).dt.days

    grouped["turnover"] = grouped.apply(
        lambda r: r["total_sold"] / r["avg_stock"]
        if r["avg_stock"] > 0 else 0,
        axis=1
    )

    grouped["days_to_sell"] = grouped.apply(
        lambda r: window_days / r["turnover"]
        if r["turnover"] > 0 else None,
        axis=1
    )

    return grouped


# ---------------------------------------------------------
# Save turnover
# ---------------------------------------------------------

def save_turnover(conn, df, window_days):

    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM turnover_metrics WHERE window_days = %s",
            (window_days,)
        )

        insert_sql = """
            INSERT INTO turnover_metrics
            (article, window_days, period_start, period_end,
             total_sold, avg_stock, turnover, days_to_sell)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """

        for _, r in df.iterrows():
            days_to_sell = None if pd.isna(r["days_to_sell"]) else float(r["days_to_sell"])

            cursor.execute(insert_sql, (
                r["article"],
                int(r["window_days"]),
                r["period_start"],
                r["period_end"],
                float(r["total_sold"]),
                float(r["avg_stock"]),
                float(r["turnover"]),
                days_to_sell
            ))

        conn.commit()

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to save turnover for window {window_days}: {e}")
        raise
    finally:
        cursor.close()


# ---------------------------------------------------------
# Save liquidity
# ---------------------------------------------------------

def save_liquidity(conn, turnover_df, threshold):

    cursor = conn.cursor()
    window_days = int(threshold["window_days"])

    try:
        cursor.execute(
            "DELETE FROM liquidity_category WHERE window_days = %s",
            (window_days,)
        )

        insert_sql = """
            INSERT INTO liquidity_category
            (article, window_days, category, reason)
            VALUES (%s,%s,%s,%s)
        """

        for _, r in turnover_df.iterrows():

            if r["age_days"] < threshold["min_age_days"]:
                category = "unknown"
                reason = "age < min_age_days"

            elif r["days_to_sell"] and r["days_to_sell"] > threshold["max_days_to_sell_dead"]:
                category = "dead"
                reason = "days_to_sell too high"

            elif r["turnover"] >= threshold["min_turnover_high"]:
                category = "high"
                reason = "high turnover"

            elif r["turnover"] >= threshold["min_turnover_medium"]:
                category = "medium"
                reason = "medium turnover"

            else:
                category = "low"
                reason = "low turnover"

            cursor.execute(insert_sql, (
                r["article"],
                window_days,
                category,
                reason
            ))

        conn.commit()

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to save liquidity for window {window_days}: {e}")
        raise
    finally:
        cursor.close()


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    logger.info("START → liquidity_recalculation (multi-window)")

    conn = get_connection()

    try:
        snapshots = load_snapshots(conn)
        thresholds_df = load_thresholds(conn)

        for _, threshold in thresholds_df.iterrows():
            window = int(threshold["window_days"])
            logger.info(f"Processing window: {window} days")

            turnover_df = calculate_turnover(snapshots, window)

            save_turnover(conn, turnover_df, window)
            save_liquidity(conn, turnover_df, threshold)

        logger.info("Multi-window liquidity recalculated successfully.")

    finally:
        conn.close()

    logger.info("DONE → liquidity_recalculation")


if __name__ == "__main__":
    main()