from fastapi import APIRouter, Depends
from backend.database import get_db
from schemas.rides import RideRequest
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["Ride Requests"],)

@router.post("/ride-requests")
async def create_ride_request(ride_request: RideRequest, db: AsyncSession = Depends(get_db)):
    