# Feature Specification: FinPulse Transaction Analytics Platform

**Feature Branch**: `001-transaction-analytics`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: "FinPulse transaction analytics platform (v1 demo scope, per the ratified constitution). Retail banking transactions arrive via historical batch load and a simulated real-time stream; every transaction is fraud-scored; a fraud/risk operations analyst reviews transaction volume, revenue by merchant/region, and flagged-transaction rate on a BI dashboard."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Historical Trend Review (Priority: P1)

A fraud/risk operations analyst opens the dashboard and reviews transaction volume over time and
revenue broken down by merchant and region, based on the full historical batch dataset, to
understand overall business activity without querying the warehouse directly.

**Why this priority**: This is the smallest slice that proves the core value chain end-to-end —
data lands, gets modeled, and becomes a readable business view. Without it, nothing else in the
platform has anything to build on.

**Independent Test**: Load only the historical batch dataset (no streaming, no fraud scoring) and
confirm the dashboard renders volume-over-time and revenue-by-merchant/region charts that match
the underlying data.

**Acceptance Scenarios**:

1. **Given** the historical batch dataset has been loaded, **When** the analyst opens the
   dashboard, **Then** they see total transaction volume plotted over time.
2. **Given** the historical batch dataset has been loaded, **When** the analyst views the revenue
   breakdown, **Then** revenue is shown grouped by both merchant and region.

---

### User Story 2 - Fraud Risk Visibility (Priority: P2)

The analyst reviews the flagged-transaction rate on the dashboard and can see which transactions
were flagged as high fraud-risk, so they can identify anomalies worth investigating.

**Why this priority**: Fraud-signal scoring is the platform's distinguishing capability beyond a
generic BI report — it depends on User Story 1's data already being modeled, but delivers
independent, demonstrable value (a working ML scoring layer feeding a KPI).

**Independent Test**: With the historical dataset already loaded and modeled (per US1), run the
fraud-scoring step and confirm every transaction has a risk score, and the dashboard's
flagged-transaction-rate KPI reflects the scored data.

**Acceptance Scenarios**:

1. **Given** the historical dataset has been scored for fraud risk, **When** the analyst views the
   dashboard, **Then** they see the current flagged-transaction rate.
2. **Given** a transaction has been flagged as high risk, **When** the analyst inspects flagged
   transactions, **Then** every flagged transaction shows a risk score.

---

### User Story 3 - Live Activity Monitoring (Priority: P3)

The analyst sees newly streamed transactions reflected in the dashboard's KPIs within a bounded,
predictable time window of them occurring, without needing to know or care whether a given
transaction arrived via batch or streaming.

**Why this priority**: Streaming is additive freshness on top of an already-working batch +
scoring pipeline (US1 + US2) — valuable to demonstrate architecturally, but the platform is
already a viable, demoable product without it.

**Independent Test**: With US1 and US2 already working, start the streaming simulator and confirm
that new transactions appear in raw storage, flow through the same models as batch data, get
fraud-scored, and update the dashboard's KPIs within the defined refresh interval — with no
separate code path from the batch flow.

**Acceptance Scenarios**:

1. **Given** the platform is running with streaming active, **When** a new simulated transaction
   is emitted, **Then** it appears in the dashboard's transaction volume within the defined
   refresh interval.
2. **Given** a streamed transaction is scored as high fraud-risk, **When** the next scoring cycle
   runs, **Then** it is reflected in the flagged-transaction-rate KPI exactly as a batch-sourced
   flagged transaction would be.

---

### Edge Cases

- What happens when a transaction arrives with a missing or unrecognized merchant/region?
- How does the dashboard behave if the streaming simulator stops or lags — does it show stale data
  clearly, or silently go quiet?
- How does the system handle a transaction ID collision between the batch dataset and the
  streaming path?
- What happens when the fraud-scoring step runs before a batch of new transactions has finished
  landing — are unscored transactions ever counted as "not flagged" by mistake?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate synthetic accounts, merchants, and transactions using a single
  consistent schema shared by both the batch and streaming sources.
- **FR-002**: System MUST load the historical transaction batch into the raw data layer on a
  schedule, without manual intervention.
- **FR-003**: System MUST ingest simulated real-time transactions into the same raw data layer
  used by the batch path.
- **FR-004**: System MUST transform raw transaction data — regardless of whether it arrived via
  batch or streaming — through one consistent set of staging and marts models, producing
  identical output schemas.
- **FR-005**: System MUST assign a fraud-risk score to every transaction, including transactions
  that arrived via the streaming path, on a scheduled cadence.
- **FR-006**: System MUST display transaction volume over time on the dashboard.
- **FR-007**: System MUST display revenue broken down by both merchant and region on the
  dashboard.
- **FR-008**: System MUST display the current flagged-transaction rate on the dashboard.
- **FR-009**: System MUST make newly streamed transactions visible in dashboard KPIs within a
  defined, bounded refresh interval rather than requiring a manual data reload.
- **FR-010**: System MUST be startable end-to-end from a clean checkout via a single startup
  action, with no manual per-service configuration.

### Key Entities

- **Account**: A synthetic bank account holder. Key attributes: account identifier, region,
  opening date.
- **Merchant**: A business receiving transaction payments. Key attributes: merchant identifier,
  name, category, region.
- **Transaction**: A single payment event between an account and a merchant. Key attributes:
  transaction identifier, account, merchant, amount, currency, timestamp, source (batch or
  streaming).
- **Fraud Risk Score**: A derived score and flag attached to a transaction by the scoring step,
  indicating its assessed fraud risk.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: From a clean checkout, an analyst can view fully populated volume, revenue, and
  flagged-rate KPIs for the entire historical dataset (~50,000 transactions) within 15 minutes of
  platform startup.
- **SC-002**: A newly streamed transaction is reflected in the dashboard's KPIs within 5 minutes
  of occurring, with no manual action beyond having the dashboard open.
- **SC-003**: 100% of transactions — batch and streaming alike — receive a fraud-risk score before
  being counted in the flagged-transaction-rate KPI; none are silently excluded.
- **SC-004**: The platform reaches a fully running, browsable state from a clean checkout using a
  single startup action, with zero manual per-component configuration steps.
- **SC-005**: An analyst unfamiliar with the platform's internals can identify the top
  merchant/region by revenue and the current flagged-transaction rate within 2 minutes of first
  opening the dashboard.

## Assumptions

- "Real-time" streaming is simulated via a synthetic event generator, not a connection to a real
  banking network or live payment processor.
- Fraud-risk scoring is a demo-grade anomaly signal intended to demonstrate the ML layer's
  plumbing end-to-end, not a validated production fraud-detection model.
- Consistent with the constitution's batch-scoring principle, the streaming-to-dashboard refresh
  interval is scheduled (minutes-scale), not sub-second live push to the UI.
- Demo data volumes (~50,000 historical transactions, ~500 accounts, ~200 merchants, ~5
  transactions/sec streaming) are illustrative defaults, adjustable later without changing scope.
- Authentication, PII handling, regulatory compliance, and multi-tenancy are explicitly out of
  scope, per the ratified project constitution.
