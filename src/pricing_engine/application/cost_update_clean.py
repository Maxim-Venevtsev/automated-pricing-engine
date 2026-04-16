import pandas as pd
from datetime import datetime
from pathlib import Path


def normalize_article(x):
    if pd.isna(x):
        return None
    x = str(x).strip()
    x = x.replace("-", "")
    if x.endswith(".0"):
        x = x[:-2]
    return x


def detect_cost_column(df):
    # 1. try by header
    for col in df.columns:
        col_lower = str(col).lower()
        if any(k in col_lower for k in ["цена", "стоим", "закуп"]):
            return col

    # 2. fallback by values
    numeric_cols = df.select_dtypes(include=["number"]).columns

    for col in numeric_cols:
        sample = df[col].dropna().head(50)
        if (sample % 1 != 0).any():  # has decimals
            return col

    raise ValueError("Cost column could not be reliably detected")


def clean_cost_file(input_path, output_dir):
    df = pd.read_excel(input_path)

    # detect cost column
    cost_col = detect_cost_column(df)

    # detect article column
    article_col = None
    for col in df.columns:
        if "артик" in str(col).lower():
            article_col = col
            break

    if not article_col:
        raise ValueError("Article column not found")

    # build clean df
    clean_df = pd.DataFrame()
    clean_df["article"] = df[article_col].apply(normalize_article)
    clean_df["cost"] = df[cost_col]

    # optional fields
    for col in df.columns:
        col_lower = str(col).lower()

        if "номен" in col_lower:
            clean_df["name"] = df[col]

        if "груп" in col_lower or "бренд" in col_lower:
            clean_df["price_group"] = df[col]

        if "ед" in col_lower:
            clean_df["unit"] = df[col]

    # drop empty articles
    clean_df = clean_df[clean_df["article"].notna()]

    # save
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"cost_update_clean_{datetime.now().strftime('%Y_%m_%d')}.xlsx"
    output_path = output_dir / filename

    clean_df.to_excel(output_path, index=False)

    return output_path


if __name__ == "__main__":
    input_file = "data/incoming/cost_updates/example.xlsx"
    output_dir = "data/staging/cost_updates"

    path = clean_cost_file(input_file, output_dir)
    print(f"Saved: {path}")