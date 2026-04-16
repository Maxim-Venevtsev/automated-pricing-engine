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


def find_column(df, candidates, required=False, field_name="column"):
    normalized = {str(col).strip().lower(): col for col in df.columns}

    for candidate in candidates:
        candidate = candidate.lower()
        for norm_name, original_name in normalized.items():
            if candidate == norm_name or candidate in norm_name:
                return original_name

    if required:
        raise ValueError(f"{field_name.capitalize()} not found")

    return None


def detect_cost_column(df):
    # 1. explicit header-based detection
    explicit = find_column(
        df,
        candidates=[
            "cost",
            "себестоимость",
            "закуп",
            "стоимость",
            "цена закуп",
        ],
        required=False,
        field_name="cost column",
    )
    if explicit is not None:
        return explicit

    # 2. fallback by numeric pattern
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    for col in numeric_cols:
        sample = df[col].dropna().head(50)
        if len(sample) == 0:
            continue
        # cost often has decimals, stock often integer-only
        if (sample % 1 != 0).any():
            return col

    raise ValueError("Cost column could not be reliably detected")


def clean_cost_file(input_path, output_dir):
    df = pd.read_excel(input_path)

    # --- required columns
    article_col = find_column(
        df,
        candidates=["article", "артикул", "артик"],
        required=True,
        field_name="article column",
    )

    cost_col = detect_cost_column(df)

    # --- optional columns
    name_col = find_column(
        df,
        candidates=["name", "номенклатура"],
        required=False,
        field_name="name column",
    )

    price_group_col = find_column(
        df,
        candidates=["price_group", "ценовая группа", "бренд"],
        required=False,
        field_name="price_group column",
    )

    unit_col = find_column(
        df,
        candidates=["unit", "ед", "ед."],
        required=False,
        field_name="unit column",
    )

    # --- build normalized dataframe
    clean_df = pd.DataFrame()

    clean_df["article"] = df[article_col].apply(normalize_article)
    clean_df["cost"] = pd.to_numeric(df[cost_col], errors="coerce")

    if price_group_col is not None:
        clean_df["price_group"] = df[price_group_col]
    else:
        clean_df["price_group"] = None

    if name_col is not None:
        clean_df["name"] = df[name_col]
    else:
        clean_df["name"] = None

    if unit_col is not None:
        clean_df["unit"] = df[unit_col]
    else:
        clean_df["unit"] = "шт"

    # keep only valid rows
    clean_df = clean_df[clean_df["article"].notna()].copy()
    clean_df = clean_df[clean_df["cost"].notna()].copy()

    # reorder columns
    clean_df = clean_df[["article", "price_group", "name", "unit", "cost"]]

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