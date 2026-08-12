"""Workflow transition definitions.

The core workflow is fixed. Only transitions listed here are allowed;
anything else returns a business-conflict response instead of inventing
a route.
"""

from __future__ import annotations

SEQUENCE = [
    "REQUIREMENT",
    "PROPERTY_SEARCH",
    "PROPERTY_APPROVAL",
    "SECURITY_DEPOSIT",
    "LOA",
    "AGREEMENT",
    "QUOTATION",
    "ACCOUNTS",
    "CC_APPROVAL",
    "MD_APPROVAL",
    "PAYMENT",
    "INFRASTRUCTURE",
    "OPERATIONAL_READINESS",
    "OPENING",
    "COMPLETED",
]

SEQUENCE_INDEX = {stage: idx for idx, stage in enumerate(SEQUENCE)}

#: Forward/special transitions. ACCOUNTS may go back to QUOTATION for
#: negotiation or revision — a defined business route.
TRANSITIONS: dict[str, list[str]] = {
    "REQUIREMENT": ["PROPERTY_SEARCH"],
    "PROPERTY_SEARCH": ["PROPERTY_APPROVAL"],
    "PROPERTY_APPROVAL": ["SECURITY_DEPOSIT"],
    "SECURITY_DEPOSIT": ["LOA"],
    "LOA": ["AGREEMENT"],
    "AGREEMENT": ["QUOTATION"],
    "QUOTATION": ["ACCOUNTS"],
    "ACCOUNTS": ["CC_APPROVAL", "QUOTATION"],
    "CC_APPROVAL": ["MD_APPROVAL"],
    "MD_APPROVAL": ["PAYMENT"],
    "PAYMENT": ["INFRASTRUCTURE"],
    "INFRASTRUCTURE": ["OPERATIONAL_READINESS"],
    "OPERATIONAL_READINESS": ["OPENING"],
    "OPENING": ["COMPLETED"],
    "COMPLETED": [],
}

#: Roles allowed to advance a stage (role -> target stages they may advance into).
ROLL_TRANSITIONS: dict[str, list[str]] = {
    "ADMIN": SEQUENCE[1:],
    "SUPER_ADMIN": SEQUENCE[1:],
    "ACCOUNTS": ["CC_APPROVAL", "QUOTATION"],
    "CC": ["MD_APPROVAL"],
    "MD": ["PAYMENT"],
    "REGIONAL_ADMIN": ["PROPERTY_APPROVAL", "SECURITY_DEPOSIT", "LOA", "AGREEMENT", "QUOTATION"],
}


def is_allowed(current: str, target: str) -> bool:
    return target in TRANSITIONS.get(current, [])


def previous_stage(stage: str) -> str | None:
    index = SEQUENCE_INDEX.get(stage)
    if index is None or index == 0:
        return None
    return SEQUENCE[index - 1]


def next_stage(stage: str) -> str | None:
    index = SEQUENCE_INDEX.get(stage)
    if index is None or index == len(SEQUENCE) - 1:
        return None
    return SEQUENCE[index + 1]


def can_role_advance(role: str, target: str) -> bool:
    return target in ROLL_TRANSITIONS.get(role, [])