<!--
Sync Impact Report
- Version change: [TEMPLATE] → 1.0.0 (initial ratification)
- Modified principles: n/a (first version)
- Added sections: Core Principles (5), Locked Scope & Technology Stack, Definition of Done & Quality Gates, Governance
- Removed sections: none
- Follow-up TODOs: none
-->
# FinPulse Constitution

## Purpose

FinPulse is a demo data platform built to demonstrate solution-architecture capability to an
incoming client. It implements a full-stack financial-transactions analytics pipeline covering
batch and streaming ingestion, warehouse modeling, fraud-signal ML scoring, and BI reporting.
The financial-transactions domain is illustrative: patterns established here (medallion layering,
dbt-centric transformation, batch/streaming convergence) MUST generalize to other domains, not
remain hardcoded to finance-specific concepts.

## Core Principles

### I. Medallion Data Layering
All data MUST flow through three explicit layers: raw (unmodified source data), staging
(cleaned, typed, deduplicated), and marts (business-ready, dimensional/aggregated). No component
may write directly to marts without passing through staging. Rationale: a fixed layering
contract makes the pipeline's data lineage legible to a client audience unfamiliar with the
implementation, and keeps each layer independently debuggable.

### II. Unified Transformation Path
Batch and streaming ingestion MUST both land in the same raw zone before any transformation
occurs. Exactly one transformation layer (dbt) serves both paths — streaming data is never
transformed by a separate code path than batch data. Rationale: divergent batch/streaming
transformation logic is the most common source of "it works in the demo but not live" failures;
unifying the path eliminates that class of bug entirely.

### III. dbt as Single Source of Transformation Truth
All business logic and data transformation MUST be defined as dbt models, not ad-hoc scripts
(Python, SQL run outside dbt, etc.). Rationale: dbt models are testable, documented, and
version-controlled by construction — ad-hoc transformation scripts erode the audit trail a
client-facing architecture demo depends on.

### IV. Independent Component Testability
Every pipeline component (ingestion job, dbt model, ML scoring job, dashboard) MUST be runnable
and verifiable in isolation, without requiring the full stack to be live. Rationale: a component
that only works as part of the whole stack cannot be demoed incrementally or debugged in
isolation when something breaks mid-presentation.

### V. Demo Clarity Over Production Hardening
Where a tradeoff exists between production-grade robustness and clarity/simplicity for a demo
audience, clarity MUST win. This is a reference architecture, not a production system, and MUST
NOT accumulate production-only complexity (auth hardening, HA, compliance controls) that obscures
the architectural pattern being demonstrated. Rationale: the deliverable's value is in showing the
client a legible, defensible architecture — not in shipping a production system.

## Locked Scope & Technology Stack

**In scope**: synthetic financial transaction data (accounts, transactions, merchants); batch
historical load; a simulated real-time transaction stream; medallion warehouse modeling; a
simple anomaly/fraud-signal scoring model applied in batch; a BI dashboard surfacing core KPIs.

**Out of scope for this demo**: production-grade security/auth, PII handling, or regulatory
compliance; multi-tenant or high-availability infrastructure; real payment processor integration.
Any request to add these MUST be treated as a new, explicitly-scoped feature, not folded silently
into the existing demo.

**Locked technology decisions** (MUST NOT be substituted without a constitution amendment):
- Orchestration: Airflow
- Raw/object storage: MinIO (S3-compatible, local)
- Streaming: Redpanda (Kafka-compatible)
- Warehouse: Postgres
- Transformation: dbt
- ML: scikit-learn, batch scoring only (no real-time inference in v1)
- BI: Metabase
- Deployment: Docker Compose, entirely local — no cloud account required

## Definition of Done & Quality Gates

A change is complete only when the full stack still satisfies all of the following, verified via
a clean checkout:
1. `docker compose up` brings up the entire stack from a clean checkout with no manual steps.
2. Historical batch data flows raw → marts automatically via an Airflow DAG.
3. Simulated streaming transactions land in raw and flow through the same dbt models as batch
   data within a defined scheduled interval.
4. Fraud-signal scores appear on transactions in the gold (marts) layer.
5. The Metabase dashboard displays: transaction volume over time, revenue by merchant/region, and
   flagged-transaction rate.

## Governance

This constitution supersedes ad-hoc practice for FinPulse. All specs, plans, and task breakdowns
produced via Spec Kit MUST be checked for compliance with these principles before implementation
begins; any conflict MUST be resolved by amending this document, not by silently deviating from
it in code.

**Amendment procedure**: propose the change and rationale, classify it as MAJOR (incompatible
principle removal/redefinition), MINOR (new principle or materially expanded guidance), or PATCH
(clarification/wording), update this file with a Sync Impact Report, and commit the change with
message `docs: amend constitution to vX.Y.Z (<summary>)`.

**Compliance review**: each `/speckit-plan` and `/speckit-tasks` pass MUST be reviewed against
this constitution before `/speckit-implement` runs.

**Version**: 1.0.0 | **Ratified**: 2026-09-03 | **Last Amended**: 2026-09-03
