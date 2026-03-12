from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from schemas.drivers import DriverOut, DriverRegister, DriverLocationUpdate
from database import get_db
from models.drivers import Driver
from utils.oauth2 import get_current_user

router = APIRouter(tags=["Drivers"], prefix="/drivers")

@router.post("/register", response_model=DriverOut)
async def register_driver(
    driver: DriverRegister,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = await db.execute(select(Driver).where(Driver.user_id == current_user.id))
    existing_driver = result.scalars().first()
    if existing_driver:
        raise HTTPException(status_code=400, detail="Already registered as a driver")
    new_driver = Driver(
        user_id=current_user.id,
        current_lat=driver.current_lat,
        current_lng=driver.current_lng,
        vehicle_type=driver.vehicle_type
    )
    db.add(new_driver)
    await db.commit()
    await db.refresh(new_driver)
    return new_driver

@router.patch("/location", response_model=DriverOut)
async def update_location(
    location: DriverLocationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = await db.execute(select(Driver).where(Driver.user_id == current_user.id))
    driver = result.scalars().first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver profile not found")
    driver.current_lat = location.current_lat
    driver.current_lng = location.current_lng
    await db.commit()
    await db.refresh(driver)
    return driver