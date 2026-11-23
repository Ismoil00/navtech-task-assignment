from enum import StrEnum

from sqlalchemy import Enum

from app.domain.enums import ApplicationStatus, UserRole


def pg_enum(enum_cls: type[StrEnum], name: str) -> Enum:
    # В БД храним значения ("draft"), а не имена членов enum ("DRAFT")
    return Enum(enum_cls, name=name, values_callable=lambda members: [m.value for m in members])


user_role_enum = pg_enum(UserRole, "user_role")
application_status_enum = pg_enum(ApplicationStatus, "application_status")
