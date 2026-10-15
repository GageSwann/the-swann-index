"""team ratings basis: `season` vs `predictive` sets (decision #23)

Adds basis (part of the primary key), games_played, and provisional to
team_ratings. Hand-written because autogenerate doesn't detect primary-key
changes. Existing rows (none yet) would become basis='season'.

Revision ID: 3478ef401c1d
Revises: f8bb7edbc93b
Create Date: 2026-10-14 23:00:27.855836

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3478ef401c1d"
down_revision: str | Sequence[str] | None = "f8bb7edbc93b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "team_ratings", sa.Column("basis", sa.String(), server_default="season", nullable=False)
    )
    op.add_column(
        "team_ratings", sa.Column("games_played", sa.Integer(), server_default="0", nullable=False)
    )
    op.add_column(
        "team_ratings",
        sa.Column("provisional", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    # Naming convention adds the "ck_team_ratings_" prefix (-> ck_team_ratings_basis).
    op.create_check_constraint("basis", "team_ratings", "basis IN ('season', 'predictive')")
    op.drop_constraint("pk_team_ratings", "team_ratings", type_="primary")
    op.create_primary_key(
        "pk_team_ratings", "team_ratings", ["run_id", "team_id", "basis", "variant"]
    )


def downgrade() -> None:
    op.execute("DELETE FROM team_ratings WHERE basis <> 'season'")
    op.drop_constraint("pk_team_ratings", "team_ratings", type_="primary")
    op.create_primary_key("pk_team_ratings", "team_ratings", ["run_id", "team_id", "variant"])
    op.drop_constraint(op.f("ck_team_ratings_basis"), "team_ratings", type_="check")
    op.drop_column("team_ratings", "provisional")
    op.drop_column("team_ratings", "games_played")
    op.drop_column("team_ratings", "basis")
