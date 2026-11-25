"""add doctor account fields

Revision ID: 424a2cb4b29f
Revises:
Create Date: 2026-10-29 19:38:03.129369

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "424a2cb4b29f"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "doctor",
        sa.Column("phone_number", sa.String(length=20), nullable=True),
    )

    op.add_column(
        "doctor",
        sa.Column(
            "terms_accepted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "doctor",
        sa.Column("terms_version", sa.String(length=50), nullable=True),
    )

    # Matches the duplicate-email handling from the previous service code.
    op.create_index(
        "uq_doctor_email_lower",
        "doctor",
        [sa.text("lower(email)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_doctor_email_lower", table_name="doctor")
    op.drop_column("doctor", "terms_version")
    op.drop_column("doctor", "terms_accepted_at")
    op.drop_column("doctor", "phone_number")
