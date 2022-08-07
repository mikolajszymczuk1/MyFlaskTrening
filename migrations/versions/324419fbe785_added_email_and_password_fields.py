"""Added email and password fields

Revision ID: 324419fbe785
Revises: bcfb051bc880
Create Date: 2022-08-07 01:22:08.220974

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '324419fbe785'
down_revision = 'bcfb051bc880'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('email', sa.String(length=64), nullable=True))
    op.add_column('users', sa.Column('password_hash', sa.String(length=128), nullable=True))
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_column('users', 'password_hash')
    op.drop_column('users', 'email')
    # ### end Alembic commands ###