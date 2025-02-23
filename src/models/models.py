from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, Enum, Text, ForeignKey, JSON

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


class CarSearch(Base):

    __tablename__ = "Car_Searches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("Users.id"), nullable=False)
    car = Column(Text(length=100), nullable=False)
    attributes = Column(JSON, nullable=True)
