"""Add isauth

Revision ID: 4e0a44c9d9f3
Revises: 97980ed47ae3
Create Date: 2024-12-02 20:00:42.185205

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4e0a44c9d9f3'
down_revision = '97980ed47ae3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_authorized', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('is_authorized')

    # ### end Alembic commands ###