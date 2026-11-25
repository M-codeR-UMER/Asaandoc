"""phase0_patient_phone_and_refresh_tokens

Revision ID: 089afe852019
Revises: 424a2cb4b29f
Create Date: 2026-11-26 00:07:51.229387

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '089afe852019'
down_revision: Union[str, Sequence[str], None] = '424a2cb4b29f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('token_hash', sa.String(length=128), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('max_expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'], unique=True)
    op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)

    op.add_column('doctor', sa.Column('email_verified', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('doctor', sa.Column('mfa_enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False))
    op.add_column('doctor', sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False))
    op.add_column('doctor', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.execute('CREATE UNIQUE INDEX IF NOT EXISTS ix_doctor_email ON doctor (email)')

    op.add_column('patient', sa.Column('phone_number', sa.String(length=20), nullable=True))
    op.execute(
        """
        WITH numbered AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY id) AS rn
            FROM patient
            WHERE phone_number IS NULL
        )
        UPDATE patient p
        SET phone_number = '+92399' || LPAD(numbered.rn::text, 7, '0')
        FROM numbered
        WHERE p.id = numbered.id
        """
    )
    op.alter_column('patient', 'phone_number', nullable=False)
    op.add_column('patient', sa.Column('city', sa.String(length=50), server_default=sa.text("'Lahore'"), nullable=False))
    op.add_column('patient', sa.Column('terms_accepted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('patient', sa.Column('terms_version', sa.String(length=50), nullable=True))
    op.add_column('patient', sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False))
    op.add_column('patient', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.alter_column(
        'patient',
        'email',
        existing_type=sa.VARCHAR(),
        nullable=True,
    )
    op.execute('DROP INDEX IF EXISTS ix_patient_email')
    op.execute('ALTER TABLE patient DROP CONSTRAINT IF EXISTS patient_email_key')
    op.create_index(op.f('ix_patient_phone_number'), 'patient', ['phone_number'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_patient_phone_number'), table_name='patient')
    op.alter_column(
        'patient',
        'email',
        existing_type=sa.VARCHAR(),
        nullable=False,
    )
    op.drop_column('patient', 'created_at')
    op.drop_column('patient', 'is_active')
    op.drop_column('patient', 'terms_version')
    op.drop_column('patient', 'terms_accepted_at')
    op.drop_column('patient', 'city')
    op.drop_column('patient', 'phone_number')
    op.execute('DROP INDEX IF EXISTS ix_doctor_email')
    op.drop_column('doctor', 'created_at')
    op.drop_column('doctor', 'is_active')
    op.drop_column('doctor', 'mfa_enabled')
    op.drop_column('doctor', 'email_verified')
    op.drop_index(op.f('ix_refresh_tokens_user_id'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_token_hash'), table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
