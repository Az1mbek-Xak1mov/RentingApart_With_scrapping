from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BIGINT, String, Text, Integer, DECIMAL, Boolean, TIMESTAMP, ForeignKey, Enum
from sqlalchemy.sql import func
from db.engine import Base
from decimal import Decimal
from db.engine import engine


class ApartmentImage(Base):
    __tablename__ = "apartment_images"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    apartment_id: Mapped[int] = mapped_column(
        BIGINT, ForeignKey("apartments.id", ondelete="CASCADE"), nullable=False
    )
    original_url: Mapped[str] = mapped_column(String(500), nullable=True)
    local_path: Mapped[str] = mapped_column(String(500), nullable=False)
    telegram_file_id: Mapped[str] = mapped_column(String(200), nullable=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.now())
    apartment = relationship("Apartment", back_populates="images_list")

    def __repr__(self):
        return f"<ApartmentImage(id={self.id}, apartment_id={self.apartment_id}, local_path={self.local_path})>"


class Apartment(Base):
    __tablename__ = "apartments"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    owner_name: Mapped[str] = mapped_column(String(100), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    floor: Mapped[int] = mapped_column(Integer, nullable=False)
    total_storeys: Mapped[int] = mapped_column(Integer, nullable=False)
    area: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    rooms: Mapped[int] = mapped_column(Integer, nullable=False)
    is_furnished: Mapped[bool] = mapped_column(Boolean, nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(50), nullable=True)
    building_type: Mapped[str] = mapped_column(String(50), nullable=True)
    repair: Mapped[str] = mapped_column(String(50), nullable=True)
    map_link: Mapped[str] = mapped_column(String(500), nullable=True)
    latitude: Mapped[Decimal] = mapped_column(DECIMAL(9, 6), nullable=True)
    longitude: Mapped[Decimal] = mapped_column(DECIMAL(9, 6), nullable=True)
    scraped_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.now())
    status: Mapped[str] = mapped_column(String(50), nullable=True)
    url_id: Mapped[int] = mapped_column(
        ForeignKey("apartmenturls.id"),
        nullable=False,
        unique=True
    )
    url: Mapped["ApartmentUrl"] = relationship(
        "ApartmentUrl",
        back_populates="apartment",
        uselist=False
    )

    images_list = relationship(
        "ApartmentImage",
        back_populates="apartment",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return (
            f"<Apartment(id={self.id}, title={self.title!r}, price={self.price}, "
            f"area={self.area}, rooms={self.rooms}, floor={self.floor}/{self.total_storeys})>"
        )



url_status = Enum(
    "new",        # never scraped
    "in_progress",# currently being scraped
    "done",       # scraped successfully
    "error",      # scraped but failed
    name="url_status",
)

class ApartmentUrl(Base):
    __tablename__ = "apartmenturls"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(
        url_status,
        default="new",
        nullable=False,
    )
    apartment: Mapped[Apartment] = relationship(
        "Apartment",
        back_populates="url",
        uselist=False
    )

#Blocked phone numbers or real estate agent's phone number If phone number already in db then it should be added to blocked phone numbers and will be deleted from apartments
class AgentPhoneNumber(Base):
    __tablename__ = "agentphonenumbers"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(50), nullable=True)
