# Approval Matrix

Approvals are **independent records** (`approvals` table). Changing a status
never happens without creating an approval record. Approval history is never
overwritten.

## Roles

| Role | Code | Typical responsibility |
|------|------|------------------------|
| Super Admin | `SUPER_ADMIN` | User/role management, configuration, full visibility |
| Admin | `ADMIN` | Case management, workflow advancement, PO creation |
| Business Team | `BUSINESS_TEAM` | Requirements, property search input |
| Regional Admin | `REGIONAL_ADMIN` | Property selection, quotations, cancellations/replacements |
| SD | `SD` | Security deposit processing |
| Accounts | `ACCOUNTS` | Quotation review, invoice review, payments, reconciliation |
| CC | `CC` | CC-level approval of multi-branch requests |
| MD | `MD` | Final approval |

## Approval types (approval_type)

- `PROPERTY` — property option approval
- `SECURITY_DEPOSIT` — deposit approval
- `LOA` — LOA request approval
- `AGREEMENT` — agreement execution authorization
- `QUOTATION` — final vendor selection (business decision, **not** auto-L1)
- `CC` — CC request approval
- `MD` — MD approval (separate event from CC)
- `PAYMENT` — payment request approval

## Decision vocabulary

`APPROVED` / `REJECTED` / `SENT_BACK`. Every decision stores approver,
decision date, comments, amount, reference. Previous decisions are preserved.

## Sequence (typical)

1. Property selected → `PROPERTY` approval (Regional Admin / Admin)
2. SD paid (with approval) → `SECURITY_DEPOSIT`
3. LOA issued → `LOA`
4. Agreement executed → `AGREEMENT`
5. 3 quotations → Accounts review → negotiation → final vendor
   (`QUOTATION` approval — manual selection)
6. CC request (can bundle many branch openings) → `CC` approval
7. `MD` approval (separate event)
8. PO created
9. Payment request (advance) → `PAYMENT` approval (Accounts)
10. Invoice (per PO) → Accounts review → `APPROVED` (or `MISMATCH` →
    `REVISION_REQUIRED` → revised → `APPROVED`)
11. Payment request (balance) → `PAYMENT` approval → paid

## Multi-branch CC rule

One CC request contains N `cc_request_items` (one per branch opening).
Item-level `requested_amount` / `approved_amount`, then one approval record
per item is allowed; the CC decision is recorded once on the request.

## Approval pending queue

Any approval with `decision = NULL` is pending, visible per role in the
dashboard and Reports (`approval-pending` report).