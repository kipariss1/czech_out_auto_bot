from src.settings.settings import settings
from sqlalchemy.orm import declarative_base, validates, relationship
from sqlalchemy import Column, Integer, CheckConstraint, String, ForeignKey, JSON, DateTime, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel
import re

Base = declarative_base()


class User(Base):

    __tablename__ = "Users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


class CarModel(Base):

    __tablename__ = "Car_Models"

    id = Column(Integer, primary_key=True, autoincrement=True)
    manufacturer = Column(String(length=20))
    model = Column(String(length=40))
    _last_checked_links = (
        Column(JSONB, nullable=True)
        if settings.ENV == "production"
        else Column(JSON, nullable=True)
    )
    _last_checked_toped_links = (
        Column(JSONB, nullable=True)
        if settings.ENV == "production"
        else Column(JSON, nullable=True)
    )

    def __mapper_configure__(cls, mapper):
        mapper.order_by = (cls.manufacturer, cls.model)

    @property
    def last_checked_links(self) -> list[str] | None:
        return self._last_checked_links

    @last_checked_links.setter
    def last_checked_links(self, value: list[str]):
        unique = list(dict.fromkeys(value))
        self._last_checked_links = unique[-10:]

    def add_last_checked_link(self, link: str):
        current = self.last_checked_links
        if not current:
            self.last_checked_links = [link]
            return
        self.last_checked_links = current + [link]

    @property
    def last_checked_toped_links(self) -> list[str] | None:
        return self._last_checked_toped_links
    
    @last_checked_toped_links.setter
    def last_checked_toped_links(self, value: list[str]):
        unique = list(dict.fromkeys(value))
        self._last_checked_toped_links = unique[-25:]

    def add_last_checked_toped_link(self, link: str):
        current = self.last_checked_toped_links
        if not current:
            self.last_checked_toped_links = [link]
            return
        self.last_checked_toped_links = current + [link]


class CarSearchCreate(BaseModel):
    manufacturer: str
    model: str
    input_year_range_from: str
    input_year_range_to: str
    input_mileage_range_from: str
    input_mileage_range_to: str
    input_price_range_from: str
    input_price_range_to: str
    psc_code: str
    psc_km_range: str
    telegram_user_id: int

    class Config:
        extra = "allow"


class CarSearch(Base):

    __tablename__ = "Car_Searches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("Users.id"), nullable=False)
    car_model_id = Column(Integer, ForeignKey("Car_Models.id"), nullable=False)
    car_model = relationship("CarModel")
    psc_code = Column(String(6), nullable=True)
    psc_km_range = Column(String(4), nullable=True)
    year_range_from = Column(Integer, nullable=True)
    year_range_to = Column(Integer, nullable=True)
    mileage_range_from = Column(Integer, nullable=True)
    mileage_range_to = Column(Integer, nullable=True)
    price_range_from = Column(Integer, nullable=True)
    price_range_to = Column(Integer, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    @validates("psc_code")
    def validate_psc_code(self, key, address):
        if not re.match("^[0-9\s]{5,}$", address):
            raise ValueError("PSC code is not in right format")
        return address

    @validates("psc_km_range")
    def validate_psc_code(self, key, address):
        if not re.match("^[0-9]{1,4}$", address):
            raise ValueError("PSC km range is not in right format")
        return address

    def _construct_attributes(self):
        new_attrs = {
            "Year range": f"{self.year_range_from} - {self.year_range_to}",
            "Mileage range": f"{self.mileage_range_from} - {self.mileage_range_to}",
            "Price range": f"{self.price_range_from} - {self.price_range_to}",
        }
        return new_attrs

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "car_model_id": self.car_model_id,
            "car_model": f"{self.car_model.manufacturer} {self.car_model.model}",
            "psc_code": self.psc_code,
            "psc_km_range": self.psc_km_range,
            "attributes": self._construct_attributes(),
        }
    
class AdQueue(Base):

    __tablename__ = "Advertisements_Queue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    car_model_id = Column(Integer, ForeignKey("Car_Models.id"), nullable=False)
    queue = Column(JSONB, nullable=True) if settings.ENV == 'production' else Column(JSON, nullable=True)

    __table_args__ = (
        UniqueConstraint("car_model_id", name="uq_car_model_queue"),
    )
