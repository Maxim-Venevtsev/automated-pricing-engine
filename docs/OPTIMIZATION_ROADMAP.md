# Pipeline Optimization Roadmap

Goal: reduce runtime and complexity while keeping behavior identical.

Current runtime: \~10--12 seconds

Main bottlenecks:

• multiple Excel reads/writes\
• repeated pandas loads\
• CSV registries\
• DB round trips

------------------------------------------------------------------------

# Phase 1 --- Safe Optimization

Remove unnecessary Excel stages.

Current:

clean → validate → filter → normalize → XLS → next step

Target:

single dataframe flow.

Expected gain:

2--3x faster.

------------------------------------------------------------------------

# Phase 2 --- Data Flow Refactor

Pipeline becomes:

    email → dataframe
            ↓
    clean
            ↓
    validate
            ↓
    filter
            ↓
    normalize
            ↓
    pricing
            ↓
    export

Excel only written at:

final output.

------------------------------------------------------------------------

# Phase 3 --- SQLAlchemy Migration

Replace raw DB connections.

Benefits:

• connection pooling • safer queries • easier joins • compatibility with
pandas

------------------------------------------------------------------------

# Phase 4 --- Liquidity Optimization

Current:

full recalculation each run.

Improvement:

incremental updates.

Expected gain:

5--10x for large datasets.

------------------------------------------------------------------------

# Phase 5 --- Dealer Segmentation

Generate different price lists by dealer rules.

Implementation:

rules engine + config.

------------------------------------------------------------------------

# Phase 6 --- Scheduling

Add:

cron Airflow or Prefect

for automated daily runs.
