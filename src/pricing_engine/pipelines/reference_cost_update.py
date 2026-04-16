import os
from pathlib import Path

from pricing_engine.application.cost_update_clean import clean_cost_file
from pricing_engine.application.master_cost_update import update_master_cost


INCOMING_DIR = Path("data/incoming/cost_updates")
STAGING_DIR = Path("data/staging/cost_updates")
MASTER_COST_PATH = Path("data/reference/master_cost.xlsx")


def find_latest_file(directory):
    files = list(directory.glob("*.xlsx"))
    if not files:
        return None
    return max(files, key=lambda f: f.stat().st_mtime)


def run():
    print("=== REFERENCE COST UPDATE PIPELINE START ===")

    latest_file = find_latest_file(INCOMING_DIR)

    if not latest_file:
        print("No cost update files found.")
        return

    print(f"Found cost file: {latest_file}")

    # Step 1: clean
    clean_file = clean_cost_file(latest_file, STAGING_DIR)
    print(f"Clean file created: {clean_file}")

    # Step 2: update master cost
    update_master_cost(clean_file, MASTER_COST_PATH)

    print("=== REFERENCE COST UPDATE PIPELINE DONE ===")


if __name__ == "__main__":
    run()