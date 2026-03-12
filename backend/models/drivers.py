from base import Base
from sqlalchemy import Boolean, Column, Integer, Float, DateTime, ForeignKey, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

class Driver(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"),unique=True)
    is_available = Column(Boolean, default=True)
    current_lat = Column(Float,nullable=True)  
    current_lng = Column(Float,nullable=True)
    vehicle_type = Column(String, default="Car")
    rating = Column(Float, default=5.0)
    total_rides = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="driver")