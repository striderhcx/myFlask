"""Add avatar

Revision ID: 2c4f11e52d72
Revises: d3ecf3077637
Create Date: 2017-05-01 10:50:49.111743

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2c4f11e52d72'
down_revision = 'd3ecf3077637'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('real_avatar', sa.String(length=128), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'real_avatar')
    # ### end Alembic commands ###
