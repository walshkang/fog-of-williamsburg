import enum
from datetime import datetime
from typing import Annotated

from geoalchemy2 import Geometry
from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

UUIDStr = Annotated[str, mapped_column(UUID(as_uuid=False), primary_key=True)]


class ActivityType(str, enum.Enum):
    GPX = "gpx"
    CHECKIN = "checkin"


class Borough(Base):
    __tablename__ = "boroughs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    geometry = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=False)
    total_area: Mapped[float] = mapped_column(Float, nullable=False)

    unveiled_areas: Mapped[list["UnveiledArea"]] = relationship(
        "UnveiledArea", back_populates="borough"
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    chosen_borough_id: Mapped[int | None] = mapped_column(
        ForeignKey("boroughs.id"), nullable=True
    )

    chosen_borough: Mapped[Borough | None] = relationship("Borough")
    unveiled_areas: Mapped[list["UnveiledArea"]] = relationship(
        "UnveiledArea", back_populates="user"
    )
    activities: Mapped[list["Activity"]] = relationship(
        "Activity", back_populates="user"
    )


class UnveiledArea(Base):
    __tablename__ = "unveiled_areas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    borough_id: Mapped[int] = mapped_column(ForeignKey("boroughs.id"), nullable=False)
    geometry = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped[User] = relationship("User", back_populates="unveiled_areas")
    borough: Mapped[Borough] = relationship("Borough", back_populates="unveiled_areas")


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    borough_id: Mapped[int] = mapped_column(ForeignKey("boroughs.id"), nullable=False)
    type: Mapped[ActivityType] = mapped_column(Enum(ActivityType), nullable=False)
    raw_gpx_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_location = Column(
        Geometry(geometry_type="POINT", srid=4326), nullable=True
    )  # for check-ins
    processed_geometry = Column(
        Geometry(geometry_type="MULTILINESTRING", srid=4326), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    user: Mapped[User] = relationship("User", back_populates="activities")
    borough: Mapped[Borough] = relationship("Borough")


