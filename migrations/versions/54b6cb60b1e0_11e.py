"""11e

Revision ID: 54b6cb60b1e0
Revises: d867d1ac7588
Create Date: 2017-03-29 19:11:41.493986

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '54b6cb60b1e0'
down_revision = 'd867d1ac7588'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('posts', sa.Column('body_html', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('posts', 'body_html')
    # ### end Alembic commands ###