from src.settings.settings import settings
from sqlalchemy.orm import declarative_base, validates, relationship
from sqlalchemy import Column, Integer, CheckConstraint, String, ForeignKey, JSON, DateTime, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel
import re

Base = declarative_base()


class User(Base):

    __tablename__ = "Users"

    id = Column(Integer, primary_key=True)
    language = Column(String(2), nullable=False, default="en")

    __table_args__ = (
        CheckConstraint("language IN ('ru', 'en', 'cz')", name="check_language"),
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

    def __mapper_configure__(cls, mapper):
        mapper.order_by = (cls.manufacturer, cls.model)

    @property
    def last_checked_links(self) -> list[str]:
        return self._last_checked_links

    @last_checked_links.setter
    def last_checked_links(self, value: list[str]):
        unique = list(dict.fromkeys(value))
        self._last_checked_links = unique[-50:]


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
    enc_user_id: str

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
    price_range_from = Column(Integer, nullable=True)
    price_range_to = Column(Integer, nullable=True)
    attributes = Column(JSONB, nullable=True) if settings.ENV == 'production' else Column(JSON, nullable=True)
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
            "Year range": f"{self.attributes['input_year_range_from']} - {self.attributes['input_year_range_to']}",
            "Mileage range": f"{self.attributes['input_mileage_range_from']} - {self.attributes['input_mileage_range_to']}",
            "Price range": f"{self.attributes['input_price_range_from']} - {self.attributes['input_price_range_to']}",
        }
        new_attrs.update(
            {
                f"Unique trait #{int(k.split('_')[1]) + 1}": v
                for k, v in self.attributes.items()
                if "attributes_" in k
            }
        )
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
