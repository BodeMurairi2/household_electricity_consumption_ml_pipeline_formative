from datetime import datetime
from decimal import Decimal
from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Household(Base):
    __tablename__ = "households"

    household_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    city: Mapped[str] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(100))
    data_start: Mapped[datetime | None]
    data_end: Mapped[datetime | None]


class SubMeter(Base):
    __tablename__ = "sub_meters"

    sub_meter_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.household_id"))
    name: Mapped[str] = mapped_column(String(50))
    appliances: Mapped[str | None] = mapped_column(String(255))


class PowerReading(Base):
    __tablename__ = "power_readings"
    __table_args__ = (UniqueConstraint("household_id", "measured_at", name="uq_household_time"),)

    reading_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.household_id"))
    measured_at: Mapped[datetime]
    global_active_power: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))
    global_reactive_power: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))
    voltage: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))
    global_intensity: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))

    # ORM-level cascade: deleting a reading deletes its sub-meter rows first
    sub_meter_readings: Mapped[list["SubMeterReading"]] = relationship(
        back_populates="reading", cascade="all, delete-orphan", lazy="selectin"
    )


class SubMeterReading(Base):
    __tablename__ = "sub_meter_readings"

    reading_id: Mapped[int] = mapped_column(ForeignKey("power_readings.reading_id"), primary_key=True)
    sub_meter_id: Mapped[int] = mapped_column(ForeignKey("sub_meters.sub_meter_id"), primary_key=True)
    energy_wh: Mapped[Decimal] = mapped_column(Numeric(6, 1))

    reading: Mapped[PowerReading] = relationship(back_populates="sub_meter_readings")


class HourlyPower(Base):
    __tablename__ = "hourly_power"

    household_id: Mapped[int] = mapped_column(ForeignKey("households.household_id"), primary_key=True)
    hour_start: Mapped[datetime] = mapped_column(primary_key=True)
    global_active_power: Mapped[float | None]
    global_reactive_power: Mapped[float | None]
    voltage: Mapped[float | None]
    global_intensity: Mapped[float | None]
    sub_metering_1: Mapped[float | None]
    sub_metering_2: Mapped[float | None]
    sub_metering_3: Mapped[float | None]
