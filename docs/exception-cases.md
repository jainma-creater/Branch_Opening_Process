# Exception Cases

Real cases observed in business templates that the architecture MUST
support. These are not edge cases.

## 1. Multi-payee security deposit (Khandwa)

Deposit ₹42,000 split across two payees (2 × ₹21,000). Each payee can be
approved/paid independently with date, reference, proof and status.

```
security_deposits
 ├── deposit_payees (multiple)
 └── deposit_payments (per payee, possibly multiple)
```

## 2. Multi-branch CC request (Telangana)

One CC request bundles Shadnagar, Siricilla, Kamareddy, Nizamabad.

- Request has one number `CC-2026-NNNN`, one total amount, one decision.
- Items carry per-branch requested/approved amounts.
- **Never** create one CC per branch by default.

## 3. Property cancellation after advance payment

BO-2026-0005 example:

```
Property A → APPROVED → advance paid ₹60,550 → CANCELLED
Property B → added as replacement → UNDER_APPROVAL → new approval
```

- Property A stays in history with all connected transactions.
- The branch opening is **not** reset; only a new property option is
  added.
- Payments to the cancelled property remain visible and reconciled.

## 4. Advance / balance payment (50/50)

PO → 50% advance → work → final invoice → 50% balance.

- Payments are N milestone events, never exactly two by design.
- Reconciliation is computed: Approved − Paid = Remaining.
- Overpayment is rejected unless explicitly permitted.

## 5. Invoice mismatch and revision

Detected when invoice amount ≠ approved amount, or invoice contains an
unapproved line item.

```
Invoice submitted → Accounts review → MISMATCH → REVISION_REQUIRED
→ revised invoice → Accounts review → APPROVED
```

- Every revision is preserved (append-only versions).
- Status flow: DRAFT, SUBMITTED, UNDER_REVIEW, MISMATCH,
  REVISION_REQUIRED, REVISED, APPROVED, REJECTED, PAID.

## 6. Rent above limit

Property rent vs branch/area/region limit → `ABOVE_LIMIT` — flagged, not
blocked; escalation is a business decision recorded as an approval/
comment.

## 7. Undefined workflow transitions

If a transition is not defined in the workflow engine, the API returns a
conflict with the current business confirmation state instead of silently
moving the case.

## 8. Multiple quotations / vendors

One quotation request has up to N vendors. Comparison shows totals, rank
(L1/L2/L3), low/high/difference/average/savings — the L1 vendor is NEVER
auto-selected; selection is a manual business decision recorded as an
approval.

## 9. LOA with employee reference

LOA identifies an Employee + Employee Code and can be approved/issued/
executed with documents and audit trail.

## 10. Agreement with multiple licensors/owners

`agreement_parties` supports multiple licensors; agreement stores dates,
tenure, rent, annual increment, deposit, lock-in, fitout period and
documents as separate records.