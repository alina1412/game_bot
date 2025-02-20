"""initial

Revision ID: 37d8060aa42f
Revises: 
Create Date: 2025-01-29 15:45:26.174650

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37d8060aa42f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from sqlalchemy import engine_from_config
from sqlalchemy.engine import reflection

def _has_table(table_name):
    config = op.get_context().config
    engine = engine_from_config(
        config.get_section(config.config_ini_section), prefix="sqlalchemy."
    )
    inspector = reflection.Inspector.from_engine(engine)
    tables = inspector.get_table_names()
    return table_name in tables




def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('quiz',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('question', sa.String(length=500), nullable=False),
    sa.Column('answer', sa.String(length=50), nullable=False),
    sa.Column('category', sa.Enum('common', 'books', 'tv', 'science', name='categoryenum'), server_default='common', nullable=False),
    sa.Column('price', sa.Integer(), server_default='100', nullable=False),
    sa.PrimaryKeyConstraint('id')
    )

    op.create_table('game',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('chat_id', sa.Integer(), nullable=False),
    sa.Column('finished', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('waiting_user', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )

    op.create_table('user',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('first_name', sa.String(length=50), nullable=False),
    sa.Column('second_name', sa.String(length=50), nullable=False),
    sa.Column('vk_id', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('participant',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('game_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('score', sa.Integer(), server_default='0', nullable=False),
    sa.ForeignKeyConstraint(['game_id'], ['game.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('round',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('game_id', sa.Integer(), nullable=False),
    sa.Column('question_id', sa.Integer(), nullable=False),
    sa.Column('used', sa.String(), nullable=True),
    sa.Column('player_answers', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['game_id'], ['game.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['question_id'], ['quiz.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###
    from tests.test_game.lst_sql import lst
    for sql in lst:
        op.execute(sql)


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('round')
    op.drop_table('participant')
    
    op.drop_table('quiz')
    op.drop_table('game')
    op.drop_table('user')

    from sqlalchemy.dialects import postgresql

    my_enum = postgresql.ENUM(
        "common", "books", "tv", "science", name="categoryenum"
    )
    my_enum.drop(op.get_bind())