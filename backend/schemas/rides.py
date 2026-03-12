from pydantic import BaseModel

class Driver(BaseModel):
    id: int
    name: str
    lat: float
    lng: float

class RideRequest(BaseModel):
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float
    dropoff_lng: float