import sqlalchemy as sa

import uuid
from datetime import datetime

from sqlalchemy import Text, Boolean, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import (
    UUID, JSONB, ARRAY, ENUM, TIMESTAMP, NUMERIC
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base
from contracts import OrderStatus, OrderProviderStatus

pg_order_status = sa.Enum(
    OrderStatus,
    name="order_status",
    native_enum=True,
    create_type=True,
    validate_strings=True,
    values_callable=lambda e: [m.value for m in e],
)

pg_order_provider_status = sa.Enum(
    OrderProviderStatus,
    name="order_provider_status",
    create_type=False,
    validate_strings=True,
    values_callable=lambda e: [m.value for m in e],
)

class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    sensor_types: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'::text[]")
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    order_providers = relationship("OrderProvider", back_populates="provider")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    bbox: Mapped[list[float] | None] = mapped_column(ARRAY(NUMERIC(asdecimal=False)))
    start_date: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    end_date: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    status: Mapped[OrderStatus] = mapped_column(
        pg_order_status, nullable=False, default=OrderStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    events = relationship("Event", back_populates="order", cascade="all, delete-orphan")
    order_providers = relationship("OrderProvider", back_populates="order", cascade="all, delete-orphan")


Index("ix_orders_status_created_at", Order.status, Order.created_at)


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict | None] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    order = relationship("Order", back_populates="events")


Index("ix_events_order_id_created_at", Event.order_id, Event.created_at)


class OrderProvider(Base):
    __tablename__ = "order_providers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("providers.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[OrderProviderStatus] = mapped_column(
        pg_order_provider_status, nullable=False, default= OrderProviderStatus.PENDING
    )
    last_error: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict | None] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))

    order = relationship("Order", back_populates="order_providers")
    provider = relationship("Provider", back_populates="order_providers")


Index("ix_order_providers_order_id", OrderProvider.order_id)
Index("ix_order_providers_provider_id", OrderProvider.provider_id)
