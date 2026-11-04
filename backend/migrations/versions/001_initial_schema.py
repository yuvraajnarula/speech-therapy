"""001 - Initial schema: users, therapy_sessions, exercise_attempts, consent_records, audit_logs

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---- users ----
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="patient"),
        sa.Column("preferred_locale", sa.String(20), server_default="en-IN"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # ---- consent_records ----
    op.create_table(
        "consent_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("hipaa_acknowledged", sa.Boolean(), server_default=sa.false()),
        sa.Column("audio_retention_agreed", sa.Boolean(), server_default=sa.false()),
        sa.Column("research_sft_permitted", sa.Boolean(), server_default=sa.false()),
        sa.Column("consented_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ---- therapy_sessions ----
    op.create_table(
        "therapy_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("therapist_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("target_language", sa.String(20), server_default="hi"),
        sa.Column("status", sa.String(50), server_default="active"),
        sa.Column("clinical_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_therapy_sessions_therapist_id", "therapy_sessions", ["therapist_id"])
    op.create_index("ix_therapy_sessions_patient_id", "therapy_sessions", ["patient_id"])

    # ---- exercise_attempts ----
    op.create_table(
        "exercise_attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("therapy_sessions.id"), nullable=False),
        sa.Column("target_phrase", sa.String(500), nullable=False),
        sa.Column("spoken_phrase", sa.String(500), nullable=True),
        sa.Column("target_phonemes", sa.String(500), nullable=True),
        sa.Column("spoken_phonemes", sa.String(500), nullable=True),
        sa.Column("is_correct", sa.Boolean(), server_default=sa.false()),
        sa.Column("target_achieved", sa.Boolean(), server_default=sa.false()),
        sa.Column("accuracy_score", sa.Float(), server_default="0.0"),
        sa.Column("errors_json", sa.Text(), nullable=True),
        sa.Column("audio_storage_key", sa.String(500), nullable=True),
        sa.Column("source_language", sa.String(20), server_default="hi"),
        sa.Column("translated_text", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_exercise_attempts_session_id", "exercise_attempts", ["session_id"])

    # ---- audit_logs ----
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource", sa.String(255), nullable=False),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("exercise_attempts")
    op.drop_table("therapy_sessions")
    op.drop_table("consent_records")
    op.drop_table("users")
