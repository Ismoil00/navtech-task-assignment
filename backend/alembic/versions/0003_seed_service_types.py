"""Справочник типов услуг

Справочник — часть схемы, поэтому заполняется миграцией, а не скриптом:
на любой базе после `alembic upgrade head` он одинаковый.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-23
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

service_types = sa.table(
    "service_types",
    sa.column("code", sa.String),
    sa.column("name", sa.String),
    sa.column("description", sa.String),
    sa.column("price", sa.Integer),
    sa.column("currency", sa.String),
    sa.column("sort_order", sa.SmallInteger),
)

# Цены в дирамах: 5000 = 50 сомони
SERVICE_TYPES = [
    {
        "code": "criminal_record_certificate",
        "name": "Справка о несудимости",
        "description": "Справка об отсутствии судимости для работы, учёбы или выезда за рубеж.",
        "price": 5000,
    },
    {
        "code": "property_register_extract",
        "name": "Выписка из реестра недвижимости",
        "description": "Сведения о собственнике и обременениях объекта недвижимости.",
        "price": 4000,
    },
    {
        "code": "sole_proprietor_registration",
        "name": "Регистрация индивидуального предпринимателя",
        "description": "Государственная регистрация физического лица в качестве ИП.",
        "price": 12000,
    },
    {
        "code": "driver_license_replacement",
        "name": "Замена водительского удостоверения",
        "description": "Замена удостоверения в связи с окончанием срока действия или утерей.",
        "price": 8000,
    },
    {
        "code": "document_apostille",
        "name": "Апостиль на документ",
        "description": "Проставление апостиля для использования документа за рубежом.",
        "price": 6000,
    },
]


def upgrade() -> None:
    op.bulk_insert(
        service_types,
        [
            {**item, "currency": "TJS", "sort_order": index}
            for index, item in enumerate(SERVICE_TYPES, start=1)
        ],
    )


def downgrade() -> None:
    codes = [item["code"] for item in SERVICE_TYPES]
    op.execute(service_types.delete().where(service_types.c.code.in_(codes)))
