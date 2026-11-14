"""Add administrator permission

Revision ID: ae60c6e143a5
Revises: 59879220f3a0
"""

from alembic import op
import sqlalchemy as sa


revision = "ae60c6e143a5"
down_revision = "59879220f3a0"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_admin",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false()
            )
        )


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("is_admin")
