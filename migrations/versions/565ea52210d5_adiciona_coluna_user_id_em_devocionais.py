from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '565ea52210d5'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Adiciona a coluna user_id na tabela devocionais
    with op.batch_alter_table('devocionais', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=False))
        # Cria a chave estrangeira com um nome explícito
        batch_op.create_foreign_key('fk_user_devocionais', 'user', ['user_id'], ['id'])

def downgrade():
    # Remove a chave estrangeira e a coluna
    with op.batch_alter_table('devocionais', schema=None) as batch_op:
        batch_op.drop_constraint('fk_user_devocionais', type_='foreignkey')
        batch_op.drop_column('user_id')
