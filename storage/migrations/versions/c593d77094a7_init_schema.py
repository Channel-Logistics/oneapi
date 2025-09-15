"""init schema

Revision ID: c593d77094a7
Revises: 
Create Date: 2025-09-15 09:35:09.266437

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision: str = 'c593d77094a7'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    order_status = sa.Enum(
        "pending",
        "processing",
        "done",
        "failed",
        name="order_status",
        create_type=False,
    )
    order_provider_status = sa.Enum(
        "pending",
        "processing",
        "done",
        "failed",
        name="order_provider_status",
        create_type=False,
    )

    # --- Enum types ---
    op.execute("CREATE TYPE order_status AS ENUM ('pending','processing','done','failed');")
    op.execute("CREATE TYPE order_provider_status AS ENUM ('pending','processing','done','failed');")

    # --- Tables ---

    # PROVIDERS
    op.create_table(
        "providers",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("slug", sa.Text(), nullable=False, unique=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("sensor_types", pg.ARRAY(sa.Text()), nullable=False, server_default=sa.text("'{}'::text[]")),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("created_at", pg.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # ORDERS
    op.create_table(
        "orders",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("bbox", pg.ARRAY(sa.Numeric()), nullable=True),  # numeric[]; si prefieres double precision[] usa pg.ARRAY(sa.Float())
        sa.Column("start_date", pg.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("end_date", pg.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("status", sa.Enum(name="order_status", create_type=False), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("created_at", pg.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", pg.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # EVENTS
    op.create_table(
        "events",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("order_id", pg.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("data", pg.JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", pg.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # ORDER_PROVIDERS
    op.create_table(
        "order_providers",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("order_id", pg.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider_id", pg.UUID(as_uuid=True), sa.ForeignKey("providers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.Enum(name="order_provider_status", create_type=False), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("meta", pg.JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb")),
    )

    # I
    op.create_index("ix_providers_slug", "providers", ["slug"], unique=True)
    op.create_index("ix_events_order_id_created_at", "events", ["order_id", "created_at"])
    op.create_index("ix_order_providers_order_id", "order_providers", ["order_id"])
    op.create_index("ix_order_providers_provider_id", "order_providers", ["provider_id"])
    op.create_index("ix_orders_status_created_at", "orders", ["status", "created_at"])

    # Trigger to update updated_at on orders table
    op.execute("""
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
        NEW.updated_at = now();
        RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER trg_orders_set_updated_at
        BEFORE UPDATE ON orders
        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """)



def downgrade():
    # Inverse delete operations
    op.drop_index("ix_orders_status_created_at", table_name="orders")
    op.drop_index("ix_order_providers_provider_id", table_name="order_providers")
    op.drop_index("ix_order_providers_order_id", table_name="order_providers")
    op.drop_index("ix_events_order_id_created_at", table_name="events")
    op.drop_index("ix_providers_slug", table_name="providers")

    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS trg_orders_set_updated_at ON orders;")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at;")

    op.drop_table("order_providers")
    op.drop_table("events")
    op.drop_table("orders")
    op.drop_table("providers")

    op.execute("DROP TYPE IF EXISTS order_provider_status;")
    op.execute("DROP TYPE IF EXISTS order_status;")
