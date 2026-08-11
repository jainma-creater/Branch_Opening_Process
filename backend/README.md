# Branch Opening Platform

Production-oriented backend for the Branch / Area / Region opening workflow.

## Current milestone

Phase 1 foundation:
- FastAPI application
- PostgreSQL-ready SQLAlchemy configuration
- Region → Area → Branch hierarchy
- Branch Opening aggregate
- Fixed workflow stage vocabulary
- Health endpoint
- Initial automated test

## Run

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -e ".[test]"
copy .env.example .env
pytest
uvicorn app.main:app --reload
```

Health endpoint:

`GET /api/v1/health`
