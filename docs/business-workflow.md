# Business Workflow

Branch / Area / Region Opening Management Platform — Svatantra Micro Housing Finance Corporation Ltd.

## Purpose

The platform is the system of record for opening a new branch. The existing
process (Gmail, Excel, Google Drive, manual follow-ups) is replaced by this
application. Gmail templates/emails are business references only — there is
**no Gmail integration** and no Gmail clone.

## Core Workflow (fixed, sequential at business level)

| # | Stage code | Business stage |
|---|------------|----------------|
| 1 | `REQUIREMENT` | Branch Requirement |
| 2 | `PROPERTY_SEARCH` | Location / Property Search |
| 3 | `PROPERTY_APPROVAL` | Property Approval |
| 4 | `SECURITY_DEPOSIT` | Security Deposit (SD) |
| 5 | `LOA` | LOA Request / Issuance |
| 6 | `AGREEMENT` | Agreement Preparation / Execution |
| 7 | `QUOTATION` | Infrastructure / Furniture Quotations |
| 8 | `ACCOUNTS` | Accounts Review |
| 9 | `CC_APPROVAL` | CC Approval |
| 10 | `MD_APPROVAL` | MD Approval |
| 11 | `PAYMENT` | Purchase Order / Payment |
| 12 | `INFRASTRUCTURE` | Infrastructure Work |
| 13 | `OPERATIONAL_READINESS` | Operational Readiness |
| 14 | `OPENING` | Branch Opening |
| 15 | `COMPLETED` | Completed |

**IMPORTANT:** The workflow is sequential at the *business* level, but
individual stages contain parallel activities, revisions, exceptions and
multiple records. It is **not** modelled as a single linear status field.

## Stage-adjacent parallel activities

- Property stage: multiple property options, cancellation, replacement.
- SD stage: multiple payees, partial payments.
- Quotation stage: 3+ vendors, comparison, negotiation.
- Payment stage: advance, balance, partial, final payments; invoice
  review/revision loops.
- CC stage: one request may bundle several branch openings.

## Real business examples

### Example 1 — Khandwa (single branch)

- Branch: Khandwa, Madhya Pradesh, Area: Indore
- Branch Code: SMHFC_B00145
- Property: 700 sq.ft, Rent ₹14,000
- Deposit: ₹42,000 split across multiple payees (e.g. 2 × ₹21,000)
- LOA: Employee + Employee Code
- Agreement: 01-Sep-2026 → 31-Jul-2027

Path: Property → Approval → SD → LOA → Agreement.

### Example 2 — Telangana (multi-branch CC, procurement exceptions)

One CC approval request bundles:

- Shadnagar, Siricilla, Kamareddy, Nizamabad

Each branch case carries:

- Multiple vendors (L1, L2, L3) and multiple quotations
- Multiple PO / payment events: 50% advance, later balance payment
- Invoice mismatch and invoice revision
- Property cancellation **after advance payment**
- Replacement property with new approval

## Entities owned by the workflow

Properties, approvals, deposits, payees, LOA, agreements, quotation requests,
quotations + items, CC requests + items, purchase orders, invoices, payments,
infrastructure, documents, audit events. All workflow stages generate tasks.