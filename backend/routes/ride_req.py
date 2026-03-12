from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from database import get_db
from models.drivers import Driver
from models.ride import Ride
from utils.haversine import calculate_fare, haversine
from utils.oauth2 import get_current_user
from schemas.rides import RideRequest, RideOut
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/rides", tags=["Ride Requests"])

@router.post("/request", response_model=RideOut)
async def request_ride(
    ride_request: RideRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = await db.execute(
        select(Driver).where(
            Driver.current_lat.is_not(None),
            Driver.current_lng.is_not(None)
        )
    )
    available_drivers = result.scalars().all()
    if not available_drivers:
        raise HTTPException(status_code=404, detail="No drivers available right now")
    
    nearest_driver = min(
        available_drivers,
        key=lambda d: haversine(ride_request.pickup_lat, ride_request.pickup_lng, d.current_lat, d.current_lng)
    )
    distance_km = haversine(ride_request.pickup_lat, ride_request.pickup_lng, ride_request.dropoff_lat, ride_request.dropoff_lng)
    fare = calculate_fare(distance_km)
    
    ride = Ride(
        rider_id=current_user.id,
        driver_id=nearest_driver.id,
        pickup_lat=ride_request.pickup_lat,
        pickup_lng=ride_request.pickup_lng,
        dropoff_lat=ride_request.dropoff_lat,
        dropoff_lng=ride_request.dropoff_lng,
        status="pending",
        distance_km=round(distance_km, 2),
        fare=fare
    )
    db.add(ride)
    await db.commit()
    await db.refresh(ride)
    return ride

@router.get("/{ride_id}", response_model=RideOut)
async def get_ride(
    ride_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = await db.execute(select(Ride).where(Ride.id == ride_id))
    ride = result.scalar_one_or_none()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    return ride