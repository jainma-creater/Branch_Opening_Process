# Status Matrix

## Case status (branch_openings.case_status)

| Status | Meaning |
|--------|---------|
| `DRAFT` | Created, not yet activated |
| `ACTIVE` | Workflow in progress |
| `ON_HOLD` | Paused (business decision) |
| `COMPLETED` | All stages done, opening recorded |
| `CANCELLED` | Case cancelled as a whole |
| `EXCEPTION` | Needs business intervention (e.g. blocked transition) |

## Workflow instance status (per stage)

`PENDING` → `IN_PROGRESS` → `SUBMITTED` → `APPROVED` → `COMPLETED`
with `REJECTED` / `SENT_BACK` branches.

## Workflow task status

`PENDING` / `IN_PROGRESS` / `COMPLETED` / `CANCELLED`

## Property option status

| Status | Meaning |
|--------|---------|
| `UNDER_REVIEW` | Being evaluated |
| `SELECTED` | Chosen option (pre-approval) |
| `APPROVED` | Approved |
| `REJECTED` | Evaluated and rejected |
| `NOT_SELECTED` | Viable but not chosen |
| `CANCELLED` | Previously selected/approved, later cancelled |
| `REPLACEMENT` | Replacement property identified |
| `UNDER_APPROVAL` | Approval in progress (e.g. replacement) |

Historical options are never deleted.

## Rent limit check

`property.rent` vs applicable limit (branch → area → region fallback):
`WITHIN_LIMIT` / `ABOVE_LIMIT`.

## Deposit / payment status

- deposit_payment: `PENDING` / `APPROVED` / `PAID` / `REJECTED`
- payment_request: `DRAFT` / `SUBMITTED` / `APPROVED` / `REJECTED` /
  `PAID` / `CANCELLED`
- payment: `PENDING` / `PAID` / `REVERSED`

## Invoice status (revision lifecycle)

`DRAFT` → `SUBMITTED` → `UNDER_REVIEW` → `MISMATCH` →
`REVISION_REQUIRED` → `REVISED` → `APPROVED` → `PAID`
(plus `REJECTED` from review).

Comparison always available: Approved amount vs PO amount vs Invoice amount
vs Paid amount. Every revision is preserved (new version, old stays).

## PO status

`DRAFT` / `ISSUED` / `APPROVED` / `CANCELLED`

## Readiness checklist item status

`PENDING` / `IN_PROGRESS` / `COMPLETED`

## LOA status

`REQUESTED` / `APPROVED` / `ISSUED` / `EXECUTED` / `REJECTED`

## Agreement status

`DRAFT` / `UNDER_EXECUTION` / `EXECUTED` / `CANCELLED`

## Audit events

Append-only; `action` + `stage` + `user_id` + `old_value`/`new_value` +
`timestamp`.