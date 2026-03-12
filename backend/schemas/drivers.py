from pydantic import BaseModel
from typing import Optional

class DriverRegister(BaseModel):
    current_lat: float
    current_lng: float
    vehicle_type: str = "car"

class DriverLocationUpdate(BaseModel):
    current_lat: float
    current_lng: float

class DriverOut(BaseModel):
    id: int
    user_id: int
    current_lat: Optional[float]
    current_lng: Optional[float]
    vehicle_type: str
    rating: float
    total_rides: int

    class Config:
        from_attributes = True