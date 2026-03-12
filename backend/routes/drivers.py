from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from backend.schemas.rides import Driver

router = APIRouter(tags=["Drivers"],)

@router.get("/drivers")
async def get_drivers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Driver).where(Driver.is_available == True))
    drivers = result.scalars().all()
    return drivers
@router.patch("/drivers/{driver_id}/availability")
async def update_driver_availability(driver_id: int, is_available: bool, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Driver).where(Driver.id == driver_id))
    driver = result.scalar_one_or_none()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    driver.is_available = is_available
    await db.commit()
    await db.refresh(driver)
    return driver

@router.patch("/drivers/{driver_id}/location")
async def update_driver_location(driver_id: int, current_lat: float, current_lng: float, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Driver).where(Driver.id == driver_id))
    driver = result.scalar_one_or_none()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    driver.current_lat = current_lat
    driver.current_lng = current_lng
    await db.commit()
    await db.refresh(driver)
    return driver

")