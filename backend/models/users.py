from database import Base
from sqlalchemy import Column, Integer, String, DateTime

from sqlalchemy.sql import func

class role:
    RIDER="rider"
    DRIVER="driver"
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default=role.RIDER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
        