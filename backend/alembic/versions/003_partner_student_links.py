"""Add partner student links.

Revision ID: 003_partner_student_links
Revises: 002_partner_api_keys
Create Date: 2026-07-07
"""

from alembic import op
import sqlalchemy as sa


revision = "003_partner_student_links"
down_revision = "002_partner_api_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "partner_student_links",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("partner_name", sa.String(length=255), nullable=False),
        sa.Column("external_student_id", sa.String(length=160), nullable=False),
        sa.Column("student_id", sa.String(length=36), nullable=False),
        sa.Column("external_school_id", sa.String(length=160), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("partner_name", "external_student_id", name="uq_partner_student_external_id"),
    )
    op.create_index("ix_partner_student_links_partner_name", "partner_student_links", ["partner_name"])
    op.create_index("ix_partner_student_links_external_student_id", "partner_student_links", ["external_student_id"])
    op.create_index("ix_partner_student_links_student_id", "partner_student_links", ["student_id"])


def downgrade() -> None:
    op.drop_index("ix_partner_student_links_student_id", table_name="partner_student_links")
    op.drop_index("ix_partner_student_links_external_student_id", table_name="partner_student_links")
    op.drop_index("ix_partner_student_links_partner_name", table_name="partner_student_links")
    op.drop_table("partner_student_links")
