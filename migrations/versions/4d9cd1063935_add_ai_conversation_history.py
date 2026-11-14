"""Add AI conversation history

Revision ID: 4d9cd1063935
Revises: 64de107d19ac
"""

from alembic import op
import sqlalchemy as sa

revision = '4d9cd1063935'
down_revision = '64de107d19ac'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'ai_conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(
        'ix_ai_conversations_user_id',
        'ai_conversations',
        ['user_id'],
        unique=False
    )

    op.create_table(
        'ai_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ['conversation_id'],
            ['ai_conversations.id']
        ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(
        'ix_ai_messages_conversation_id',
        'ai_messages',
        ['conversation_id'],
        unique=False
    )


def downgrade():
    op.drop_index(
        'ix_ai_messages_conversation_id',
        table_name='ai_messages'
    )
    op.drop_table('ai_messages')

    op.drop_index(
        'ix_ai_conversations_user_id',
        table_name='ai_conversations'
    )
    op.drop_table('ai_conversations')
