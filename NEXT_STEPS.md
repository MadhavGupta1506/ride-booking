# ⚡ Next Steps — What To Do Now

> This file tells you exactly what to work on next.
> Update it as you finish each task.

---

## 🟢 Currently Working On: Phase 3 — Ride Booking Core

**Goal:** Understand how a ride is requested and how the nearest driver is found.
Three endpoints, one utility function. That's it.

---

### Step 1 — Haversine utility
**File:** `backend/utils/haversine.py`

This function takes two GPS coordinates and returns the straight-line distance i### Step 5 — After migration: Start Phase 3

Once models are in the DB, move to:
- `POST /drivers/register`
- `PATCH /drivers/availability`
- `PATCH /drivers/location`
- `POST /rides/request` (find nearest available driver using Haversine)
n km.
It is used by `POST /rides/request` to rank all drivers by distance from the pickup point.

```python
from math import radians, sin, cos, sqrt, atan2

def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Returns distance in km between two GPS coordinates."""
    R = 6371
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

BASE_FARE = 2.0       # flat charge just for booking (dollars)
RATE_PER_KM = 1.5     # dollars per km

def calculate_fare(distance_km: float) -> float:
    return round(BASE_FARE + RATE_PER_KM * distance_km, 2)
```

---

### Step 2 — Driver schemas
**File:** `backend/schemas/drivers.py`

```python
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
```

---

### Step 3 — Ride schemas
**File:** `backend/schemas/rides.py`

```python
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
```

---

### Step 4 — Driver routes
**File:** `backend/routes/drivers.py`

Two endpoints:
- `POST /drivers/register` — logged-in user becomes a driver; saves their starting location.
- `PATCH /drivers/location` — update driver's GPS (use this in Swagger to move drivers around for testing).

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models.drivers import Driver
from schemas.drivers import DriverRegister, DriverLocationUpdate, DriverOut
from utils.oauth2 import get_current_user

router = APIRouter(prefix="/drivers", tags=["Drivers"])

@router.post("/register", response_model=DriverOut)
async def register_driver(
    data: DriverRegister,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Prevent duplicate registration
    result = await db.execute(select(Driver).where(Driver.user_id == current_user.id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already registered as a driver")

    driver = Driver(
        user_id=current_user.id,
        current_lat=data.current_lat,
        current_lng=data.current_lng,
        vehicle_type=data.vehicle_type,
    )
    db.add(driver)
    await db.commit()
    await db.refresh(driver)
    return driver


@router.patch("/location", response_model=DriverOut)
async def update_location(
    data: DriverLocationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Driver).where(Driver.user_id == current_user.id))
    driver = result.scalar_one_or_none()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver profile not found")

    driver.current_lat = data.current_lat
    driver.current_lng = data.current_lng
    await db.commit()
    await db.refresh(driver)
    return driver
```

---

### Step 5 — Ride routes
**File:** `backend/routes/ride_req.py`

This is the core of the system.
`POST /rides/request` does:
1. Fetch all drivers that have a location set
2. Run Haversine for every driver against the pickup point
3. Pick the closest one
4. Calculate fare from pickup → dropoff distance
5. Create the ride row and return it

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models.ride import Ride
from models.drivers import Driver
from schemas.rides import RideRequest, RideOut
from utils.oauth2 import get_current_user
from utils.haversine import haversine, calculate_fare

router = APIRouter(prefix="/rides", tags=["Rides"])

@router.post("/request", response_model=RideOut)
async def request_ride(
    data: RideRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # 1. Fetch all drivers that have a location
    result = await db.execute(
        select(Driver).where(
            Driver.current_lat.is_not(None),
            Driver.current_lng.is_not(None),
        )
    )
    drivers = result.scalars().all()

    if not drivers:
        raise HTTPException(status_code=404, detail="No drivers available right now")

    # 2. Find the nearest driver using Haversine
    nearest = min(
        drivers,
        key=lambda d: haversine(data.pickup_lat, data.pickup_lng, d.current_lat, d.current_lng),
    )

    # 3. Calculate fare and distance (pickup → dropoff)
    distance_km = haversine(data.pickup_lat, data.pickup_lng, data.dropoff_lat, data.dropoff_lng)
    fare = calculate_fare(distance_km)

    # 4. Create the ride
    ride = Ride(
        rider_id=current_user.id,
        driver_id=nearest.id,
        pickup_lat=data.pickup_lat,
        pickup_lng=data.pickup_lng,
        dropoff_lat=data.dropoff_lat,
        dropoff_lng=data.dropoff_lng,
        status="pending",
        distance_km=round(distance_km, 2),
        fare=fare,
    )
    db.add(ride)
    await db.commit()
    await db.refresh(ride)
    return ride


@router.get("/{ride_id}", response_model=RideOut)
async def get_ride(
    ride_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(Ride).where(Ride.id == ride_id))
    ride = result.scalar_one_or_none()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    return ride
```

---

### Step 6 — Register routers in `main.py`

Make sure `backend/main.py` includes both routers:

```python
from routes.drivers import router as drivers_router
from routes.ride_req import router as rides_router

app.include_router(drivers_router)
app.include_router(rides_router)
```

---

### How to test it end-to-end

1. **Register two users** via `POST /auth/register` — one will be the driver, one the rider.
2. **Login as the driver**, call `POST /drivers/register` with a lat/lng (e.g. `28.6139, 77.2090`).
3. **Login as the rider**, call `POST /rides/request` with pickup and dropoff coords.
4. The response shows the assigned `driver_id`, the `distance_km`, and the calculated `fare`.
5. Use `PATCH /drivers/location` to move the driver to a different position and request again to see a different result.

---

## ✅ Done

- [x] FastAPI setup
- [x] Async DB with asyncpg + Supabase
- [x] Alembic configured
- [x] User model
- [x] JWT Auth (register + login)
- [x] OAuth2PasswordRequestForm
