from sqlalchemy.orm import declarative_base, validates, relationship
from sqlalchemy import Column, Integer, Enum, Text, ForeignKey, JSON
from pydantic import BaseModel
import re

Base = declarative_base()


class User(Base):

    __tablename__ = "Users"

    id = Column(Integer, primary_key=True)
    language = Column(Enum("ru", "en", "cz"), nullable=False, default="en")


class CarModel(Base):

    __tablename__ = "Car_Models"

    id = Column(Integer, primary_key=True, autoincrement=True)
    manufacturer = Column(Text(length=20))
    model = Column(Text(length=40))


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
    psc_code = Column(Text(6), nullable=True)
    psc_km_range = Column(Text(4), nullable=True)
    attributes = Column(JSON, nullable=True)

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
                f"Unique trait #{k.split('_')[1]}": v
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
