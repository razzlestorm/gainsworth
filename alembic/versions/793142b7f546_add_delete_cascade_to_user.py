"""add delete cascade to User

Revision ID: 793142b7f546
Revises: 
Create Date: 2022-06-12 23:16:26.108628

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '793142b7f546'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("users", sa.ForeignKey('exercises', ondelete='CASCADE'))
    op.add_column("users", sa.Column('last_active', sa.DateTime()))


def downgrade() -> None:
    pass
