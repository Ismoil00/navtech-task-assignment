"""Пользователи, типы услуг и заявки

Revision ID: 0001
Revises:
Create Date: 2026-11-23
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

user_role = postgresql.ENUM("applicant", "operator", name="user_role", create_type=False)
application_status = postgresql.ENUM(
    "draft",
    "paid",
    "submitted",
    "approved",
    "rejected",
    "returned",
    name="application_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    user_role.create(bind)
    application_status.create(bind)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("username", name=op.f("uq_users_username")),
    )

    op.create_table(
        "service_types",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), server_default="TJS", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("sort_order", sa.SmallInteger(), server_default="0", nullable=False),
        sa.CheckConstraint("price > 0", name=op.f("ck_service_types_price_positive")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_service_types")),
        sa.UniqueConstraint("code", name=op.f("uq_service_types_code")),
    )

    op.create_table(
        "applications",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("applicant_id", sa.Uuid(), nullable=False),
        sa.Column("service_type_id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("comment", sa.String(1000), nullable=True),
        sa.Column("status", application_status, server_default="draft", nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["applicant_id"],
            ["users.id"],
            name=op.f("fk_applications_applicant_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["service_type_id"],
            ["service_types.id"],
            name=op.f("fk_applications_service_type_id_service_types"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_applications")),
    )
    op.create_index(
        "ix_applications_applicant_created", "applications", ["applicant_id", "created_at"]
    )
    op.create_index(
        "ix_applications_queue", "applications", ["status", "service_type_id", "submitted_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_applications_queue", table_name="applications")
    op.drop_index("ix_applications_applicant_created", table_name="applications")
    op.drop_table("applications")
    op.drop_table("service_types")
    op.drop_table("users")

    bind = op.get_bind()
    application_status.drop(bind)
    user_role.drop(bind)
