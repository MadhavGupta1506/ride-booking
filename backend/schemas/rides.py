from pydantic import BaseModel
from typing import Optional

class RideRequest(BaseModel):
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float
    dropoff_lng: float

class RideOut(BaseModel):
    id: int
    rider_id: int
    driver_id: Optional[int]
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float
    dropoff_lng: float
    status: str
    fare: Optional[float]
    distance_km: Optional[float]

    class Config:
        from_attributes = True