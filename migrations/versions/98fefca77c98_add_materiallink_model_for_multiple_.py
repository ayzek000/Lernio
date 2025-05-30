"""Add MaterialLink model for multiple links

Revision ID: 98fefca77c98
Revises: 93ba0945b877
Create Date: 2025-05-25 21:26:56.607477

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '98fefca77c98'
down_revision = '93ba0945b877'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('material_links',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('material_id', sa.Integer(), nullable=False),
    sa.Column('url', sa.String(length=255), nullable=False),
    sa.Column('title', sa.String(length=140), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('activity_log')
    op.drop_table('courses')
    op.drop_table('transversal_assessment')
    with op.batch_alter_table('glossary_items', schema=None) as batch_op:
        batch_op.alter_column('definition_ru',
               existing_type=sa.TEXT(),
               type_=sa.String(length=100),
               nullable=True)
        batch_op.alter_column('definition_uz',
               existing_type=sa.TEXT(),
               type_=sa.String(length=100),
               nullable=True)
        batch_op.alter_column('wrong_option1',
               existing_type=sa.TEXT(),
               type_=sa.String(length=100),
               existing_nullable=True)
        batch_op.alter_column('wrong_option2',
               existing_type=sa.TEXT(),
               type_=sa.String(length=100),
               existing_nullable=True)
        batch_op.alter_column('wrong_option3',
               existing_type=sa.TEXT(),
               type_=sa.String(length=100),
               existing_nullable=True)
        batch_op.create_index(batch_op.f('ix_glossary_items_word'), ['word'], unique=False)

    with op.batch_alter_table('materials', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_materials_position'), ['position'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('materials', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_materials_position'))

    with op.batch_alter_table('glossary_items', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_glossary_items_word'))
        batch_op.alter_column('wrong_option3',
               existing_type=sa.String(length=100),
               type_=sa.TEXT(),
               existing_nullable=True)
        batch_op.alter_column('wrong_option2',
               existing_type=sa.String(length=100),
               type_=sa.TEXT(),
               existing_nullable=True)
        batch_op.alter_column('wrong_option1',
               existing_type=sa.String(length=100),
               type_=sa.TEXT(),
               existing_nullable=True)
        batch_op.alter_column('definition_uz',
               existing_type=sa.String(length=100),
               type_=sa.TEXT(),
               nullable=False)
        batch_op.alter_column('definition_ru',
               existing_type=sa.String(length=100),
               type_=sa.TEXT(),
               nullable=False)

    op.create_table('transversal_assessment',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.INTEGER(), nullable=True),
    sa.Column('course_id', sa.INTEGER(), nullable=True),
    sa.Column('communication_score', sa.INTEGER(), nullable=True),
    sa.Column('teamwork_score', sa.INTEGER(), nullable=True),
    sa.Column('problem_solving_score', sa.INTEGER(), nullable=True),
    sa.Column('creativity_score', sa.INTEGER(), nullable=True),
    sa.Column('adaptability_score', sa.INTEGER(), nullable=True),
    sa.Column('comments', sa.TEXT(), nullable=True),
    sa.Column('assessed_at', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('courses',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('title', sa.VARCHAR(length=100), nullable=False),
    sa.Column('description', sa.TEXT(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.Column('updated_at', sa.DATETIME(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('activity_log',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.INTEGER(), nullable=True),
    sa.Column('action', sa.VARCHAR(length=100), nullable=False),
    sa.Column('entity_type', sa.VARCHAR(length=50), nullable=True),
    sa.Column('entity_id', sa.INTEGER(), nullable=True),
    sa.Column('timestamp', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('material_links')
    # ### end Alembic commands ###
