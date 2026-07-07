"""Add partner API keys.

Revision ID: 002
Revises: 001
Create Date: 2026-07-07 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "partner_api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("key_hash", sa.String(64), nullable=False),
        sa.Column("organization_name", sa.String(255), nullable=True),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("schools.id", ondelete="SET NULL"), nullable=True),
        sa.Column("scopes", sa.String(255), nullable=False, server_default="predict:write,predict:read"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("key_hash", name="uq_partner_api_keys_key_hash"),
    )
    op.create_index("ix_partner_api_keys_key_hash", "partner_api_keys", ["key_hash"], unique=True)
    op.create_index("ix_partner_api_keys_school_id", "partner_api_keys", ["school_id"])


def downgrade() -> None:
    op.drop_index("ix_partner_api_keys_school_id", table_name="partner_api_keys")
    op.drop_index("ix_partner_api_keys_key_hash", table_name="partner_api_keys")
    op.drop_table("partner_api_keys")
