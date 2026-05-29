"""initial schema

Revision ID: 20260101_0001
Revises:
Create Date: 2026-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "20260101_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    user_role = sa.Enum("admin", "professeur", "assistant", name="user_role")
    exam_status = sa.Enum(
        "draft", "rubric_pending", "rubric_ready", "grading", "closed",
        name="exam_status",
    )
    copy_status = sa.Enum(
        "uploaded", "extracted", "graded", "reviewed", "failed",
        name="copy_status",
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "exams",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False, server_default=""),
        sa.Column("owner_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", exam_status, nullable=False),
        sa.Column("rubric_source_path", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "rubric_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("exam_id", sa.Integer, sa.ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("question_number", sa.String(32), nullable=False),
        sa.Column("intitule", sa.Text, nullable=False, server_default=""),
        sa.Column("expected_answer", sa.Text, nullable=False, server_default=""),
        sa.Column("points_max", sa.Float, nullable=False, server_default="0"),
        sa.Column("ordre", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "grading_policies",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("exam_id", sa.Integer, sa.ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("condition_description", sa.Text, nullable=False, server_default=""),
        sa.Column("fraction_points", sa.Float, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "student_copies",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("exam_id", sa.Integer, sa.ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("student_identifier", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("page_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", copy_status, nullable=False),
        sa.Column("error_message", sa.String(1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "question_grades",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("copy_id", sa.Integer, sa.ForeignKey("student_copies.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("rubric_item_id", sa.Integer, sa.ForeignKey("rubric_items.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("applied_policy_id", sa.Integer, sa.ForeignKey("grading_policies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("extracted_text", sa.Text, nullable=False, server_default=""),
        sa.Column("proposed_points", sa.Float, nullable=False, server_default="0"),
        sa.Column("applied_fraction", sa.Float, nullable=False, server_default="0"),
        sa.Column("justification", sa.Text, nullable=False, server_default=""),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0"),
        sa.Column("needs_human_review", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("final_points", sa.Float, nullable=True),
        sa.Column("validated_by", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("entity", sa.String(64), nullable=False, index=True),
        sa.Column("entity_id", sa.Integer, nullable=False, index=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("old_value", sa.Text, nullable=True),
        sa.Column("new_value", sa.Text, nullable=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("question_grades")
    op.drop_table("student_copies")
    op.drop_table("grading_policies")
    op.drop_table("rubric_items")
    op.drop_table("exams")
    op.drop_table("users")
    sa.Enum(name="copy_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="exam_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="user_role").drop(op.get_bind(), checkfirst=True)
