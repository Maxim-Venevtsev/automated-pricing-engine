import pandas as pd
from pathlib import Path
from datetime import datetime


def update_master_cost(clean_file_path, master_cost_path):
    clean_df = pd.read_excel(clean_file_path)

    master_path = Path(master_cost_path)

    if master_path.exists():
        master_df = pd.read_excel(master_path)
    else:
        master_df = pd.DataFrame(columns=clean_df.columns.tolist())

    # ensure article is string
    clean_df["article"] = clean_df["article"].astype(str)
    master_df["article"] = master_df["article"].astype(str)

    # merge logic
    master_df = master_df.set_index("article")
    clean_df = clean_df.set_index("article")

    # update existing
    master_df.update(clean_df)

    # append new
    new_articles = clean_df.index.difference(master_df.index)
    new_rows = clean_df.loc[new_articles]

    master_df = pd.concat([master_df, new_rows])

    master_df = master_df.reset_index()

    # audit fields
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    master_df["last_updated_in_cost"] = now

    if "first_seen_in_cost" not in master_df.columns:
        master_df["first_seen_in_cost"] = now

    # save
    master_path.parent.mkdir(parents=True, exist_ok=True)
    master_df.to_excel(master_path, index=False)

    print(f"Master cost updated: {master_path}")


if __name__ == "__main__":
    clean_file = "data/staging/cost_updates/cost_update_clean.xlsx"
    master_cost = "data/reference/master_cost.xlsx"

    update_master_cost(clean_file, master_cost)