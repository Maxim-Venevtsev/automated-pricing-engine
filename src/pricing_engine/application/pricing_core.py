import logging
import os
import time
import pandas as pd

from configs.settings import (
    STAGING_DIR,
    BASE_PRICE_FILE,
)

logger = logging.getLogger(__name__)

INPUT_FILE = STAGING_DIR / "corrected_price_45.xlsx"
OUTPUT_FILE = STAGING_DIR / "corrected_price_5.xlsx"


# ---------------------------------------------------------
# Load input
# ---------------------------------------------------------

def load_corrected_price():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"{INPUT_FILE} not found")

    df = pd.read_excel(INPUT_FILE)

    required = {
        "article",
        "price",
        "liquidity_coef",
    }

    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in input file: {missing}")

    df["article"] = df["article"].astype(str)

    return df.copy()


def load_base_price():

    if not BASE_PRICE_FILE.exists():
        raise FileNotFoundError(f"{BASE_PRICE_FILE} not found")

    df = pd.read_excel(BASE_PRICE_FILE)

    required = {
        "article",
        "base_price",
        "min_price",
    }

    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in base_price.xlsx: {missing}")

    df["article"] = df["article"].astype(str)

    return df[["article", "base_price", "min_price"]].copy()


# ---------------------------------------------------------
# Save helper (safe on Windows locks)
# ---------------------------------------------------------

def save_excel_safely(df: pd.DataFrame, target_path, retries: int = 3, sleep_sec: float = 0.5):
    """
    Write to a temp file and atomically replace target.
    Helps avoid partial files and gives clearer behavior on Windows file locks.
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = target_path.with_name(target_path.stem + ".__tmp__" + target_path.suffix)

    last_err = None
    for attempt in range(1, retries + 1):
        try:
            # 1) write temp
            df.to_excel(tmp_path, index=False)

            # 2) replace target (atomic on same filesystem)
            os.replace(tmp_path, target_path)
            return

        except PermissionError as e:
            last_err = e
            logger.warning(
                f"PermissionError while saving {target_path.name} (attempt {attempt}/{retries}). "
                f"Maybe the file is open in Excel. Retrying..."
            )
            time.sleep(sleep_sec)

        finally:
            # If temp exists and replace didn't happen, try to cleanup
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except Exception:
                pass

    # If we got here — still locked
    raise PermissionError(
        f"Cannot write '{target_path}'. It is likely opened in Excel or locked by another process. "
        f"Close the file and retry."
    ) from last_err


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    logger.info("START → pricing_core")

    df = load_corrected_price()
    base_df = load_base_price()

    total_rows = len(df)

    # ---------------------------------------------------------
    # Merge base price
    # ---------------------------------------------------------

    df = df.merge(
        base_df,
        on="article",
        how="left"
    )

    # Fallback logic
    df["base_price"] = df["base_price"].fillna(df["price"])
    df["min_price"] = df["min_price"].fillna(0)

    # Ensure numeric
    df["base_price"] = pd.to_numeric(df["base_price"], errors="coerce").fillna(0)
    df["liquidity_coef"] = pd.to_numeric(df["liquidity_coef"], errors="coerce").fillna(1.0)
    df["min_price"] = pd.to_numeric(df["min_price"], errors="coerce").fillna(0)

    # ---------------------------------------------------------
    # Pricing logic
    # ---------------------------------------------------------

    df["price_before_liquidity"] = df["base_price"]

    # If new → skip liquidity
    if "flag" in df.columns:
        new_mask = df["flag"] == "New!"
    else:
        new_mask = pd.Series(False, index=df.index)

    df["price_after_liquidity"] = df["base_price"]

    df.loc[~new_mask, "price_after_liquidity"] = (
        df.loc[~new_mask, "base_price"] *
        df.loc[~new_mask, "liquidity_coef"]
    )

    # Min price protection
    df["price"] = df[["price_after_liquidity", "min_price"]].max(axis=1)

    # ---------------------------------------------------------
    # Telemetry
    # ---------------------------------------------------------

    skipped_new = int(new_mask.sum())
    liquidity_applied = int((~new_mask).sum())

    logger.info(f"New items (pricing skipped): {skipped_new}")
    logger.info(f"Liquidity applied: {liquidity_applied}")
    logger.info(f"Total rows: {total_rows}")

    # ---------------------------------------------------------
    # Cleanup technical columns
    # ---------------------------------------------------------

    df.drop(columns=["price_after_liquidity"], inplace=True)

    registry_columns = [
        "first_seen",
        "last_seen",
        "is_active",
        "days_since_first_seen"
    ]

    for col in registry_columns:
        if col in df.columns:
            df.drop(columns=[col], inplace=True)

    # ---------------------------------------------------------
    # Save
    # ---------------------------------------------------------

    try:
        save_excel_safely(df, OUTPUT_FILE, retries=3, sleep_sec=0.5)
    except Exception as e:
        logger.error(f"Failed to save pricing_core file: {e}")
        raise

    logger.info(f"Saved: {OUTPUT_FILE.name}")
    logger.info("DONE → pricing_core")


if __name__ == "__main__":
    main()