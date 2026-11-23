"""Вложения, платежи и история статусов

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

payment_status = postgresql.ENUM(
    "processing", "succeeded", "failed", "refunded", name="payment_status", create_type=False
)
# тип создан в 0001, здесь только ссылаемся на него
application_status = postgresql.ENUM(name="application_status", create_type=False)


def upgrade() -> None:
    payment_status.create(op.get_bind())

    op.create_table(
        "attachments",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("storage_key", sa.String(255), nullable=False),
        sa.Column("uploaded_by", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("size_bytes > 0", name=op.f("ck_attachments_size_positive")),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["applications.id"],
            name=op.f("fk_attachments_application_id_applications"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by"],
            ["users.id"],
            name=op.f("fk_attachments_uploaded_by_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_attachments")),
        sa.UniqueConstraint("application_id", name=op.f("uq_attachments_application_id")),
        sa.UniqueConstraint("storage_key", name=op.f("uq_attachments_storage_key")),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("idempotency_key", sa.String(64), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", payment_status, server_default="processing", nullable=False),
        sa.Column("provider_ref", sa.String(100), nullable=True),
        sa.Column("failure_reason", sa.String(255), nullable=True),
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("amount > 0", name=op.f("ck_payments_amount_positive")),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["applications.id"],
            name=op.f("fk_payments_application_id_applications"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payments")),
        sa.UniqueConstraint(
            "application_id", "idempotency_key", name="uq_payments_application_idempotency_key"
        ),
    )
    # Не больше одного «живого» платежа на заявку — защита от двойного списания в самой БД
    op.create_index(
        "uq_payments_one_active_per_application",
        "payments",
        ["application_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('processing', 'succeeded', 'refunded')"),
    )

    op.create_table(
        "application_status_history",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("from_status", application_status, nullable=True),
        sa.Column("to_status", application_status, nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("comment", sa.String(1000), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["applications.id"],
            name=op.f("fk_application_status_history_application_id_applications"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            name=op.f("fk_application_status_history_actor_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_application_status_history")),
    )
    op.create_index(
        "ix_application_status_history_application",
        "application_status_history",
        ["application_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_application_status_history_application", table_name="application_status_history"
    )
    op.drop_table("application_status_history")
    op.drop_index("uq_payments_one_active_per_application", table_name="payments")
    op.drop_table("payments")
    op.drop_table("attachments")
    payment_status.drop(op.get_bind())
