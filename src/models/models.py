from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, Enum, Text

Base = declarative_base()


class User(Base):

    __tablename__ = "Users"

    id = Column(Integer, primary_key=True)
    language = Column(Enum("ru", "en", "cz"), nullable=False, default="en")


class CarModel(Base):

    __tablename__ = "Car model"

    id = Column(Integer, primary_key=True)
    manufacturer = Text(length=20)
    model = Text(length=40)
