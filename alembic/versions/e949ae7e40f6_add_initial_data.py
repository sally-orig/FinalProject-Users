"""add initial data

Revision ID: e949ae7e40f6
Revises: fc22a1ec36e7
Create Date: 2025-06-02 17:06:00.908745

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, DateTime
from datetime import datetime


# revision identifiers, used by Alembic.
revision: str = 'e949ae7e40f6'
down_revision: Union[str, None] = 'fc22a1ec36e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    user = table('user',
                column('email', String(255)),
                column('mobile', String(11)),
                column('firstName', String(255)),
                column('middleName', String(255)),
                column('lastName', String(255)),
                column('role', String(50)),
                column('status', String(50)),
                column('created_at', DateTime)
                )
    
    op.bulk_insert(user, [
    {
      "email": "alice@example.com",
      "mobile": "0911111111",
      "firstName": "Jane",
      "middleName": "Alice",
      "lastName": "Doe",
      "role": "App dev 1",
      "status": "active",
      "created_at": datetime.fromisoformat("2025-06-02T06:38:14.837311")
    },
    {
      "email": "test@hotmail.com",
      "mobile": "09111111890",
      "firstName": "Alice",
      "middleName": "In",
      "lastName": "Wonderland",
      "role": "Senior App dev 1",
      "status": "active",
      "created_at": datetime.fromisoformat("2025-06-02T06:39:04.032062")
    },
    {
      "email": "test@gmil.com",
      "mobile": "09231111890",
      "firstName": "Speak",
      "middleName": "Li",
      "lastName": "Brown",
      "role": "App dev 2",
      "status": "active",
      "created_at": datetime.fromisoformat("2025-06-02T06:40:10.269640")
    },
    {
      "email": "sample@gmil.com",
      "mobile": "09231111890",
      "firstName": "Test",
      "middleName": "T",
      "lastName": "Testings",
      "role": "HR",
      "status": "active",
      "created_at": datetime.fromisoformat("2025-06-02T06:41:35.501301")
    },
    {
      "email": "call@gmil.com",
      "mobile": "09231111890",
      "firstName": "Call",
      "middleName": "Me",
      "lastName": "Maybe",
      "role": "HR",
      "status": "inactive",
      "created_at": datetime.fromisoformat("2025-06-02T06:41:56.367050")
    }
    ])


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM user")
