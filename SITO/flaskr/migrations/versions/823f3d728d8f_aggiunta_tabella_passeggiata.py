"""Aggiunta tabella passeggiata

Revision ID: 823f3d728d8f
Revises: 
Create Date: 2022-05-06 12:56:52.575679

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '823f3d728d8f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('dog_owner',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('first_name', sa.String(), nullable=True),
    sa.Column('last_name', sa.String(), nullable=True),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('address', sa.String(), nullable=True),
    sa.Column('phone', sa.String(), nullable=True),
    sa.Column('password', sa.String(), nullable=True),
    sa.Column('authenticated', sa.Boolean(), nullable=True),
    sa.Column('telegram_chat_id', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('dog',
    sa.Column('uuid', sa.String(), autoincrement=False, nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('breed', sa.String(), nullable=True),
    sa.Column('color', sa.String(), nullable=True),
    sa.Column('user', sa.Integer(), nullable=False),
    sa.Column('state', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('bridge_paired', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['user'], ['dog_owner.id'], ),
    sa.PrimaryKeyConstraint('uuid')
    )
    op.create_table('habits',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('dog', sa.String(), nullable=False),
    sa.Column('morning', sa.Time(timezone=True), nullable=True),
    sa.Column('afternoon', sa.Time(timezone=True), nullable=True),
    sa.Column('evening', sa.Time(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['dog'], ['dog.uuid'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('walk',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('dog', sa.String(), nullable=False),
    sa.Column('time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('day_slot', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['dog'], ['dog.uuid'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('walk')
    op.drop_table('habits')
    op.drop_table('dog')
    op.drop_table('dog_owner')
    # ### end Alembic commands ###
