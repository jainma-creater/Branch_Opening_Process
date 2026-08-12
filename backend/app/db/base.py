from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import all models so Base.metadata is complete for migrations/tests.
from app.models import (  # noqa: E402, F401
    Area,
    Branch,
    BranchOpening,
    Region,
    Role,
    User,
    WorkflowInstance,
    WorkflowStageDefinition,
)
