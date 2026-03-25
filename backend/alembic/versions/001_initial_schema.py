"""Initial schema — all tables for EduSight Africa.

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ---------------------------------------------------------------------------
# Helpers — postgresql.ENUM with create_type=False skips _on_table_create DDL
# ---------------------------------------------------------------------------
def _e(name: str, *values: str) -> postgresql.ENUM:
    """Return a postgresql.ENUM that references an existing DB type (no DDL)."""
    return postgresql.ENUM(*values, name=name, create_type=False)


def upgrade() -> None:
    # ------------------------------------------------------------------
    # ENUMS — use raw SQL so IF NOT EXISTS is supported (Postgres 12+)
    # ------------------------------------------------------------------
    enums = [
        ("school_type_enum",          "'public', 'private', 'community'"),
        ("connectivity_level_enum",   "'high', 'medium', 'low', 'none'"),
        ("user_role_enum",            "'teacher', 'parent', 'admin', 'superadmin'"),
        ("student_status_enum",       "'active', 'transferred', 'graduated'"),
        ("risk_level_enum",           "'low', 'medium', 'high', 'critical'"),
        ("intervention_type_enum",    "'academic', 'behavioral', 'attendance', 'home'"),
        ("intervention_status_enum",  "'planned', 'active', 'completed', 'discontinued'"),
        ("model_status_enum",         "'staging', 'production', 'archived'"),
    ]
    for name, values in enums:
        op.execute(sa.text(
            f"DO $$ BEGIN CREATE TYPE {name} AS ENUM ({values}); "
            f"EXCEPTION WHEN duplicate_object THEN NULL; END $$"
        ))

    # ------------------------------------------------------------------
    # schools
    # ------------------------------------------------------------------
    op.create_table(
        "schools",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("country_code", sa.String(3), nullable=False),
        sa.Column("district", sa.String(255), nullable=True),
        sa.Column("type", _e("school_type_enum", "public", "private", "community"),
                  nullable=False, server_default="public"),
        sa.Column("connectivity_level",
                  _e("connectivity_level_enum", "high", "medium", "low", "none"),
                  nullable=False, server_default="medium"),
        sa.Column("student_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", _e("user_role_enum", "teacher", "parent", "admin", "superadmin"),
                  nullable=False, server_default="teacher"),
        sa.Column("school_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("schools.id", ondelete="SET NULL"), nullable=True),
        sa.Column("preferred_language", sa.String(10), nullable=False, server_default="en"),
        sa.Column("country_id", sa.String(3), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_school_id", "users", ["school_id"])

    # ------------------------------------------------------------------
    # students
    # ------------------------------------------------------------------
    op.create_table(
        "students",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("grade_level", sa.Integer(), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("gender", sa.String(20), nullable=True),
        sa.Column("school_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("enrollment_date", sa.Date(), nullable=False),
        sa.Column("guardian_user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", _e("student_status_enum", "active", "transferred", "graduated"),
                  nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_students_school_id", "students", ["school_id"])
    op.create_index("ix_students_guardian_user_id", "students", ["guardian_user_id"])

    # ------------------------------------------------------------------
    # assessments
    # ------------------------------------------------------------------
    op.create_table(
        "assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("student_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assessed_by_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assessment_date", sa.Date(), nullable=False),
        sa.Column("math_score", sa.Float(), nullable=True),
        sa.Column("reading_score", sa.Float(), nullable=True),
        sa.Column("writing_score", sa.Float(), nullable=True),
        sa.Column("attendance_pct", sa.Float(), nullable=True),
        sa.Column("behavior_rating", sa.Integer(), nullable=True),
        sa.Column("literacy_level", sa.Integer(), nullable=True),
        sa.Column("additional_context", postgresql.JSONB(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_assessments_student_id", "assessments", ["student_id"])
    op.create_index("ix_assessments_assessed_by_id", "assessments", ["assessed_by_id"])
    op.create_index("ix_assessments_assessment_date", "assessments", ["assessment_date"])

    # ------------------------------------------------------------------
    # predictions
    # ------------------------------------------------------------------
    op.create_table(
        "predictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column("risk_level", _e("risk_level_enum", "low", "medium", "high", "critical"),
                  nullable=False),
        sa.Column("risk_probability", sa.Float(), nullable=False),
        sa.Column("feature_contributions", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("assessment_id", name="uq_predictions_assessment_id"),
    )
    op.create_index("ix_predictions_assessment_id", "predictions", ["assessment_id"])

    # ------------------------------------------------------------------
    # parent_observations
    # ------------------------------------------------------------------
    op.create_table(
        "parent_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("student_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("observer_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("observation_date", sa.Date(), nullable=False),
        sa.Column("homework_completion", sa.Float(), nullable=True),
        sa.Column("reading_minutes", sa.Integer(), nullable=True),
        sa.Column("focus_rating", sa.Integer(), nullable=True),
        sa.Column("behavior_home", sa.Integer(), nullable=True),
        sa.Column("mood", sa.Integer(), nullable=True),
        sa.Column("sleep_hours", sa.Float(), nullable=True),
        sa.Column("screen_time_minutes", sa.Integer(), nullable=True),
        sa.Column("physical_activity_minutes", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_parent_observations_student_id", "parent_observations", ["student_id"])
    op.create_index("ix_parent_observations_observer_id", "parent_observations", ["observer_id"])
    op.create_index("ix_parent_observations_observation_date", "parent_observations", ["observation_date"])

    # ------------------------------------------------------------------
    # interventions
    # ------------------------------------------------------------------
    op.create_table(
        "interventions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("student_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("type", _e("intervention_type_enum", "academic", "behavioral", "attendance", "home"),
                  nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status",
                  _e("intervention_status_enum", "planned", "active", "completed", "discontinued"),
                  nullable=False, server_default="planned"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("outcome_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_interventions_student_id", "interventions", ["student_id"])
    op.create_index("ix_interventions_created_by_id", "interventions", ["created_by_id"])

    # ------------------------------------------------------------------
    # model_versions
    # ------------------------------------------------------------------
    op.create_table(
        "model_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("version_string", sa.String(50), nullable=False),
        sa.Column("algorithm", sa.String(100), nullable=False),
        sa.Column("hyperparameters", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("training_metrics", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("fairness_metrics", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("dataset_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("trained_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("status", _e("model_status_enum", "staging", "production", "archived"),
                  nullable=False, server_default="staging"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("version_string", name="uq_model_versions_version_string"),
    )
    op.create_index("ix_model_versions_version_string", "model_versions", ["version_string"], unique=True)


def downgrade() -> None:
    op.drop_table("model_versions")
    op.drop_table("interventions")
    op.drop_table("parent_observations")
    op.drop_table("predictions")
    op.drop_table("assessments")
    op.drop_table("students")
    op.drop_table("users")
    op.drop_table("schools")

    for enum_name in [
        "model_status_enum", "intervention_status_enum", "intervention_type_enum",
        "risk_level_enum", "student_status_enum", "user_role_enum",
        "connectivity_level_enum", "school_type_enum",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
