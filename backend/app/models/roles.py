from __future__ import annotations

from enum import StrEnum


class RoleCode(StrEnum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    BUSINESS_TEAM = "BUSINESS_TEAM"
    REGIONAL_ADMIN = "REGIONAL_ADMIN"
    SD = "SD"
    ACCOUNTS = "ACCOUNTS"
    CC = "CC"
    MD = "MD"


ROLE_SEED = [
    (RoleCode.SUPER_ADMIN.value, "Platform super administrator"),
    (RoleCode.ADMIN.value, "Case administrator"),
    (RoleCode.BUSINESS_TEAM.value, "Business / requirements team"),
    (RoleCode.REGIONAL_ADMIN.value, "Regional administrator"),
    (RoleCode.SD.value, "Security deposit officer"),
    (RoleCode.ACCOUNTS.value, "Accounts / finance"),
    (RoleCode.CC.value, "Cost committee approver"),
    (RoleCode.MD.value, "Managing director approver"),
]