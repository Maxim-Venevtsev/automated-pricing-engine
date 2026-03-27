# Pipeline Architecture

                    EMAIL (supplier)
                          │
                          ▼
                ingestion_email.py
                          │
                          ▼
                ingestion_step1_clean
                          │
                          ▼
                ingestion_step2_validate
                          │
                          ▼
                ingestion_step3_filter
                          │
                          ▼
                ingestion_step4_normalize
                          │
                          ▼
                 corrected_price_4.xlsx
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
     ingestion_snapshot            pricing_apply_liquidity
            │                           │
            ▼                           ▼
     liquidity_recalculation        pricing_core
            │                           │
            ▼                           ▼
     liquidity_export             registry_update
            │                           │
            └─────────────┬─────────────┘
                          ▼
                     export_build
                          │
                          ▼
                     export_format
                          │
                          ▼
                     email_delivery
                          │
                          ▼
                     Dealers receive price list

------------------------------------------------------------------------

# System Layers

## Pipelines (Orchestration Layer)

    pipelines/full_pipeline.py

Responsible for:

- sequencing pipeline stages
- logging execution flow
- isolating step execution
- preserving stage boundaries

------------------------------------------------------------------------

## Application Layer

Business logic:

- ingestion
- pricing
- liquidity
- export

Each module is responsible for a single transformation step.

------------------------------------------------------------------------

## Infrastructure Layer

External systems:

- email
- database
- file system

------------------------------------------------------------------------

## Contracts-Cleanup Notes

At the contracts-cleanup stage:

- orchestration logic is stabilized without changing business behavior
- runtime directories are strictly separated from reference data
- future extension points are prepared (profiles, snapshots, delivery routing)
- configuration boundaries are enforced (settings vs constants)

This architecture is now ready for controlled feature expansion.