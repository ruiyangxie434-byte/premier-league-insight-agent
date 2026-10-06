"""Add persistent accounts and revocable, hashed sessions."""
from alembic import op
import sqlalchemy as sa
revision = '20261006_0005'
down_revision = '20260811_0004'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('accounts', sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('username', sa.String(32), nullable=False),
                    sa.Column('password_hash', sa.String(256), nullable=False))
    op.create_index('ix_accounts_username', 'accounts', ['username'], unique=True)
    op.create_table('account_sessions', sa.Column('token_hash', sa.String(64), primary_key=True),
                    sa.Column('account_id', sa.Integer(), sa.ForeignKey('accounts.id', ondelete='CASCADE'), nullable=False),
                    sa.Column('expires_at', sa.Integer(), nullable=False))
    op.create_index('ix_account_sessions_account_id', 'account_sessions', ['account_id'])
    op.create_index('ix_account_sessions_expires_at', 'account_sessions', ['expires_at'])


def downgrade():
    op.drop_table('account_sessions')
    op.drop_table('accounts')
