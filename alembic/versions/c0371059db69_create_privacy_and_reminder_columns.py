"""create privacy and reminder columns

Revision ID: c0371059db69
Revises: 793142b7f546
Create Date: 2022-07-08 16:56:15.671666

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c0371059db69'
down_revision = '793142b7f546'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column('auto_remove', sa.Boolean(), nullable=True))
    op.add_column("users", sa.Column('reminder_interval', sa.Integer()))
    op.execute("UPDATE users SET auto_remove = true")
    op.alter_column("users", "auto_remove", nullable=False)


def downgrade() -> None:
    op.drop_column("users", "auto_remove")
    op.drop_column("users", "reminder_interval")
