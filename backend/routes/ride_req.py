from fastapi import APIRouter, Depends
from backend.database import get_db
from schemas.rides import RideRequest
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["Ride Requests"],)
