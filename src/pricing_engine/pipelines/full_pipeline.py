import sys
import time
import logging
import argparse
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------
# Import application steps
# ---------------------------------------------------------

# Ingestion
from pricing_engine.application.ingestion_email import main as download_incoming
from pricing_engine.application.ingestion_step1_clean import main as process_1
from pricing_engine.application.ingestion_step2_validate import main as process_2
from pricing_engine.application.ingestion_step3_filter import main as process_3
from pricing_engine.application.ingestion_step4_normalize import main as process_4
from pricing_engine.application.ingestion_snapshot import main as ingest_snapshot

# Liquidity
from pricing_engine.application.liquidity_recalculation import main as recalc_liquidity
from pricing_engine.application.liquidity_export import main as extract_liquidity

# Pricing
from pricing_engine.application.pricing_apply_liquidity import main as process_45
from pricing_engine.application.pricing_core import main as process_5
from pricing_engine.application.registry_update import main as registry_update

# Validation
from pricing_engine.application.validation_missing_base_price import main as check_missing

# Output
from pricing_engine.application.export_build import main as process_6
from pricing_engine.application.export_format import main as process_7

# Delivery
from pricing_engine.infrastructure.email_delivery import main as send_prices


# ---------------------------------------------------------
# Logging setup
# ---------------------------------------------------------

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

log_file = LOG_DIR / f"pipeline_{datetime.today().strftime('%Y_%m_%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def section(title: str):
    logger.info("")
    logger.info("=" * 70)
    logger.info(title)
    logger.info("=" * 70)


def run_step(step_function, step_name, stage):
    logger.info(f"[{stage}] START → {step_name}")
    start = time.time()

    try:
        step_function()
    except Exception:
        logger.error(f"[{stage}] FAILED → {step_name}")
        logger.exception("Stack trace:")
        raise

    duration = round(time.time() - start, 2)
    logger.info(f"[{stage}] DONE  → {step_name} ({duration} sec)")


def run_isolated(step_function, step_name, stage, custom_args=None):
    logger.info(f"[{stage}] START → {step_name}")
    start = time.time()

    original_argv = sys.argv.copy()

    try:
        sys.argv = custom_args or [step_name]
        step_function()
    except Exception:
        logger.error(f"[{stage}] FAILED → {step_name}")
        logger.exception("Stack trace:")
        raise
    finally:
        sys.argv = original_argv

    duration = round(time.time() - start, 2)
    logger.info(f"[{stage}] DONE  → {step_name} ({duration} sec)")


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Full price automation pipeline")
    parser.add_argument("--with-ingestion", action="store_true")
    parser.add_argument("--historical", action="store_true")

    args = parser.parse_args()

    section("START FULL PRICE PIPELINE")
    total_start = time.time()

    try:

        # -------------------------------------------------
        # STAGE 1 — INGESTION
        # -------------------------------------------------
        section("STAGE 1 — INGESTION")

        run_step(download_incoming, "download_incoming", "INGESTION")
        run_step(process_1, "ingestion_step1_clean", "INGESTION")
        run_step(process_2, "ingestion_step2_validate", "INGESTION")
        run_step(process_3, "ingestion_step3_filter", "INGESTION")
        run_step(process_4, "ingestion_step4_normalize", "INGESTION")

        # -------------------------------------------------
        # STAGE 2 — DATABASE & LIQUIDITY
        # -------------------------------------------------
        if args.with_ingestion:
            section("STAGE 2 — DATABASE & LIQUIDITY")

            if args.historical:
                run_isolated(
                    ingest_snapshot,
                    "ingest_price_snapshot",
                    "DATABASE",
                    ["ingest_price_snapshot", "--historical"]
                )
            else:
                run_isolated(
                    ingest_snapshot,
                    "ingest_price_snapshot",
                    "DATABASE",
                    ["ingest_price_snapshot"]
                )

            run_step(recalc_liquidity, "liquidity_recalculation", "LIQUIDITY")
            run_step(extract_liquidity, "liquidity_export", "LIQUIDITY")

        # -------------------------------------------------
        # STAGE 3 — PRICING
        # -------------------------------------------------
        section("STAGE 3 — PRICING")

        run_step(process_45, "pricing_apply_liquidity", "PRICING")
        run_step(process_5, "pricing_core", "PRICING")

        # 🔥 Registry update AFTER pricing_core
        run_step(registry_update, "registry_update", "STATE")

        run_step(check_missing, "validation_missing_base_price", "PRICING")

        # -------------------------------------------------
        # STAGE 4 — OUTPUT
        # -------------------------------------------------
        section("STAGE 4 — OUTPUT")

        run_step(process_6, "export_build", "OUTPUT")
        run_step(process_7, "export_format", "OUTPUT")

        run_isolated(
            send_prices,
            "send_prices",
            "DELIVERY",
            ["send_prices"]
        )

    except Exception:
        section("PIPELINE FAILED")
        sys.exit(1)

    total_duration = round(time.time() - total_start, 2)

    section(f"PIPELINE COMPLETED SUCCESSFULLY ({total_duration} sec)")
    sys.exit(0)


if __name__ == "__main__":
    main()