# Entity Model

## Core convention

- Database primary keys: integers (existing foundation) — human-readable
  business numbers are stored in dedicated columns (e.g. `opening_number`,
  `po_number`, `cc_number`).
- No giant tables, no JSON blobs for relational data.
- Historical records are **never deleted** (properties, payments, approvals,
  invoice revisions are append-only).
- Foreign keys, indexes, unique + check constraints, created/updated
  timestamps everywhere.

## Hierarchy

```
Region ──┬─ Area ──┬─ Branch ──┬─ BranchOpening (case)
         │         │           │
         └ rent_limit └ rent_limit └ rent_limit
```

Rent limits are configurable per level (`rent_limit` on region/area/branch).
Rent-limit comparison result: `WITHIN_LIMIT` / `ABOVE_LIMIT`. No escalation
rules are invented.

## Aggregate: branch_openings (BO-YYYY-NNNN)

`opening_number` is the human-readable case id. The aggregate owns:

```
branch_opening
 ├── workflow_stage_definitions / workflow_instances (per-stage state)
 ├── workflow_tasks (PENDING / IN_PROGRESS / COMPLETED / CANCELLED)
 ├── approvals (independent records; status changes always create one)
 ├── audit_events (every important action)
 ├── property_options (multiple; cancelled/replaced ones stay)
 ├── security_deposits ── deposit_payees / deposit_payments
 ├── loa_requests
 ├── agreements ── agreement_parties (multiple licensors/owners)
 ├── quotation_requests ── quotation_request_items
 │       └── quotations ── quotation_items (one per vendor)
 ├── cc_requests ── cc_request_items (many branch openings per CC request)
 ├── purchase_orders (PO ≠ invoice)
 ├── invoices (DRAFT→…→APPROVED/PAID; revisions preserved)
 ├── payment_requests ── payments (advance/balance/partial/final/other)
 ├── infrastructure_projects ── infrastructure_items
 ├── readiness_checklist_items (configurable catalogue + per-case status)
 ├── opening (dates, photos)
 └── documents (first-class, versioned)
```

## Entity list

- regions, areas, branches, roles, users
- branch_openings
- workflow_stage_definitions, workflow_instances, workflow_tasks,
  audit_events, approvals
- property_options, property_evaluations (remarks recorded inline on the
  option; evaluation steps kept as audit events)
- security_deposits, deposit_payees, deposit_payments
- loa_requests
- agreements, agreement_parties
- vendors, quotation_requests, quotation_request_items, quotations,
  quotation_items
- cc_requests, cc_request_items
- purchase_orders
- invoices (revision via version + status)
- payment_requests, payments
- infrastructure_projects, infrastructure_items
- readiness_checklist_items (catalogue), case_readiness_items (per case)
- branch_openings (opening record fields)
- documents, document_versions (version history)

## Key relationships

- One branch opening → many property options (option_sequence 1..n)
- One CC request → many branch openings (cc_request_items)
- One invoice → one PO; one PO → one quotation
- One approval row references entity_type + entity_id (polymorphic,
  `approval_type` distinguishes SD / LOA / CC / MD / payment)
- Documents reference `entity_type` + `entity_id` (propiedad: first-class
  polymorphic attachment)

## Statuses

See `status-matrix.md`.