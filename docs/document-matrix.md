# Document Matrix

Documents are first-class, versioned records. Physical files are stored
outside the repo (configurable `UPLOAD_DIR`); the DB stores metadata +
storage key.

## Document types

| Type code | Attached to |
|-----------|-------------|
| `PROPERTY_PHOTO` | property option |
| `PROPERTY_DOCUMENT` | property option |
| `PROPERTY_APPROVAL` | property option / approval |
| `SD_DOCUMENT` | deposit / deposit_payment |
| `LOA` | loa request |
| `AGREEMENT` | agreement (draft) |
| `SIGNED_AGREEMENT` | agreement (executed) |
| `QUOTATION` | quotation |
| `CC_APPROVAL` | cc request |
| `PO` | purchase order |
| `INVOICE` | invoice |
| `PAYMENT_PROOF` | payment |
| `INFRASTRUCTURE_DOCUMENT` | infrastructure project |
| `OPENING_PHOTO` | opening |

## Storage model

- `documents`: id, branch_opening_id, document_type, entity_type,
  entity_id, file_name, storage_key, version, status, uploaded_by,
  uploaded_at.
- `document_versions`: append-only history of every version.

## Rules

- Upload validates file type and size (server side, not client only).
- Download is authorized: only users with access to the owning branch
  opening can download.
- Versions are immutable history — a re-upload creates a new version, the
  old one remains downloadable for audit.
- Missing files / wrong entity → 404; unauthorized → 403; malformed
  uploads → 422.

## Access control

Role-based: SUPER_ADMIN/ADMIN everywhere; REGIONAL_ADMIN within own
region; others only what their role requires (documents tied to the
case's workflow stage). Implemented in backend, not only frontend.