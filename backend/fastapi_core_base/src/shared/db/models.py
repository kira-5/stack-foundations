# app/db/models.py
from sqlalchemy import Column, Integer, String

from app.db.base import Base


class SomeModel(Base):
    __tablename__ = "some_table"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
