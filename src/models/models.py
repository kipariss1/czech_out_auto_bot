from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, Enum

Base = declarative_base()


class User(Base):

    __tablename__ = "Users"

    user_id = Column(Integer, primary_key=True)
    language = Column(Enum("ru", "en", "cz"), nullable=False, default="en")
