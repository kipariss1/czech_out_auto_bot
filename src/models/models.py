from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, Enum, Text, ForeignKey, JSON
from pydantic import BaseModel

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

    class Config:
        extra = "allow"


class CarSearch(Base):

    __tablename__ = "Car_Searches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("Users.id"), nullable=False)
    car_model_id = Column(Integer, ForeignKey("Car_Models.id"), nullable=False)
    attributes = Column(JSON, nullable=True)
