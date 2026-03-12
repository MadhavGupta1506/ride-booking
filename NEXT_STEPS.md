# ⚡ Next Steps — What To Do Now

> This file tells you exactly what to work on next.
> Update it as you finish each task.

---

## 🟢 Currently Working On: Phase 4 — Real-time Notifications & Acceptance Flow

**Goal:** Add WebSocket support so drivers receive real-time ride request notifications and can accept/reject them.

**Current status:** Phase 3 is complete. All endpoints working with auto-assignment. Now upgrading to real driver acceptance flow.

---

### Step 1 — Install WebSocket dependencies

```bash
pip install websockets
```

---

### Step 2 — Create WebSocket connection manager
**File:** `backend/utils/websocket_manager.py`

This manages active WebSocket connections for drivers and riders.

```python
from typing import Dict
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # driver_id -> WebSocket
        self.driver_connections: Dict[int, WebSocket] = {}
        # ride_id -> WebSocket (for riders)
        self.rider_connections: Dict[int, WebSocket] = {}
    
    async def connect_driver(self, driver_id: int, websocket: WebSocket):
        await websocket.accept()
        self.driver_connections[driver_id] = websocket
    
    async def connect_rider(self, ride_id: int, websocket: WebSocket):
        await websocket.accept()
        self.rider_connections[ride_id] = websocket
    
    def disconnect_driver(self, driver_id: int):
        if driver_id in self.driver_connections:
            del self.driver_connections[driver_id]
    
    def disconnect_rider(self, ride_id: int):
        if ride_id in self.rider_connections:
            del self.rider_connections[ride_id]
    
    async def send_to_driver(self, driver_id: int, message: dict):
        if driver_id in self.driver_connections:
            await self.driver_connections[driver_id].send_json(message)
    
    async def send_to_rider(self, ride_id: int, message: dict):
        if ride_id in self.rider_connections:
            await self.rider_connections[ride_id].send_json(message)

manager = ConnectionManager()
```

---

### Step 3 — Add WebSocket endpoints
**File:** `backend/routes/websocket.py`

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from utils.websocket_manager import manager
from utils.oauth2 import get_current_user_ws
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["WebSocket"])

@router.websocket("/ws/driver/{driver_id}")
async def driver_websocket(
    websocket: WebSocket,
    driver_id: int
):
    await manager.connect_driver(driver_id, websocket)
    try:
        while True:
            # Keep connection alive, receive any messages
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_driver(driver_id)

@router.websocket("/ws/ride/{ride_id}")
async def ride_websocket(
    websocket: WebSocket,
    ride_id: int
):
    await manager.connect_rider(ride_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_rider(ride_id)
```

---

### Step 4 — Update Ride model to track notification attempts
**File:** `backend/models/ride.py`

Add these fields:

```python
notified_driver_ids = Column(String, nullable=True)  # comma-separated list of driver IDs already notified
notification_attempt = Column(Integer, default=0)
```

Then create and run migration:
```bash
alembic revision --autogenerate -m "add notification tracking to rides"
alembic upgrade head
```

---

### Step 5 — Modify ride request endpoint
**File:** `backend/routes/ride_req.py`

Update `POST /rides/request` to:
1. Create ride with `driver_id=null` and `status="pending"`
2. Find nearest driver
3. Send WebSocket notification
4. Return ride immediately (driver will accept later)

```python
@router.post("/request", response_model=RideOut)
async def request_ride(
    ride_request: RideRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Find all available drivers
    result = await db.execute(
        select(Driver).where(
            Driver.current_lat.is_not(None),
            Driver.current_lng.is_not(None)
        )
    )
    available_drivers = result.scalars().all()
    if not available_drivers:
        raise HTTPException(status_code=404, detail="No drivers available right now")
    
    # Rank by distance
    sorted_drivers = sorted(
        available_drivers,
        key=lambda d: haversine(ride_request.pickup_lat, ride_request.pickup_lng, d.current_lat, d.current_lng)
    )
    
    # Calculate fare
    distance_km = haversine(
        ride_request.pickup_lat, ride_request.pickup_lng,
        ride_request.dropoff_lat, ride_request.dropoff_lng
    )
    fare = calculate_fare(distance_km)
    
    # Create ride WITHOUT assigning driver yet
    ride = Ride(
        rider_id=current_user.id,
        driver_id=None,  # No driver assigned yet
        pickup_lat=ride_request.pickup_lat,
        pickup_lng=ride_request.pickup_lng,
        dropoff_lat=ride_request.dropoff_lat,
        dropoff_lng=ride_request.dropoff_lng,
        status="pending",
        distance_km=round(distance_km, 2),
        fare=fare,
        notified_driver_ids="",
        notification_attempt=0
    )
    db.add(ride)
    await db.commit()
    await db.refresh(ride)
    
    # Notify nearest driver via WebSocket
    nearest_driver = sorted_drivers[0]
    await manager.send_to_driver(nearest_driver.id, {
        "type": "ride_request",
        "ride_id": ride.id,
        "pickup_lat": ride.pickup_lat,
        "pickup_lng": ride.pickup_lng,
        "dropoff_lat": ride.dropoff_lat,
        "dropoff_lng": ride.dropoff_lng,
        "fare": ride.fare,
        "distance_km": ride.distance_km
    })
    
    # Track that we notified this driver
    ride.notified_driver_ids = str(nearest_driver.id)
    ride.notification_attempt = 1
    await db.commit()
    
    return ride
```

---

### Step 6 — Add driver acceptance endpoints
**File:** `backend/routes/drivers.py`

Add these two new endpoints:

```python
@router.post("/accept-ride/{ride_id}", response_model=RideOut)
async def accept_ride(
    ride_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Get driver profile
    result = await db.execute(select(Driver).where(Driver.user_id == current_user.id))
    driver = result.scalars().first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver profile not found")
    
    # Get ride
    result = await db.execute(select(Ride).where(Ride.id == ride_id))
    ride = result.scalar_one_or_none()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    if ride.status != "pending":
        raise HTTPException(status_code=400, detail="Ride is no longer available")
    
    # Assign driver and update status
    ride.driver_id = driver.id
    ride.status = "accepted"
    await db.commit()
    await db.refresh(ride)
    
    # Notify rider via WebSocket
    await manager.send_to_rider(ride.id, {
        "type": "ride_accepted",
        "driver_id": driver.id,
        "status": "accepted"
    })
    
    return ride


@router.post("/reject-ride/{ride_id}")
async def reject_ride(
    ride_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Get driver profile
    result = await db.execute(select(Driver).where(Driver.user_id == current_user.id))
    driver = result.scalars().first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver profile not found")
    
    # Get ride
    result = await db.execute(select(Ride).where(Ride.id == ride_id))
    ride = result.scalar_one_or_none()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    # Find next nearest driver who hasn't been notified yet
    notified_ids = [int(x) for x in ride.notified_driver_ids.split(",") if x]
    
    result = await db.execute(
        select(Driver).where(
            Driver.current_lat.is_not(None),
            Driver.current_lng.is_not(None),
            ~Driver.id.in_(notified_ids)
        )
    )
    remaining_drivers = result.scalars().all()
    
    if not remaining_drivers:
        # No more drivers available
        ride.status = "cancelled"
        await db.commit()
        await manager.send_to_rider(ride.id, {
            "type": "ride_cancelled",
            "reason": "No drivers available"
        })
        return {"message": "No more drivers available, ride cancelled"}
    
    # Sort by distance and notify next one
    sorted_drivers = sorted(
        remaining_drivers,
        key=lambda d: haversine(ride.pickup_lat, ride.pickup_lng, d.current_lat, d.current_lng)
    )
    next_driver = sorted_drivers[0]
    
    # Send notification
    await manager.send_to_driver(next_driver.id, {
        "type": "ride_request",
        "ride_id": ride.id,
        "pickup_lat": ride.pickup_lat,
        "pickup_lng": ride.pickup_lng,
        "dropoff_lat": ride.dropoff_lat,
        "dropoff_lng": ride.dropoff_lng,
        "fare": ride.fare,
        "distance_km": ride.distance_km
    })
    
    # Update tracking
    ride.notified_driver_ids = f"{ride.notified_driver_ids},{next_driver.id}"
    ride.notification_attempt += 1
    await db.commit()
    
    return {"message": f"Notified next driver (ID: {next_driver.id})"}
```

---

### Step 7 — Register WebSocket router in main.py

**File:** `backend/main.py`

```python
from routes import websocket

app.include_router(websocket.router)
```

---

### How to test the new flow

1. **Start server**: `uvicorn backend.main:app --reload`
2. **Open WebSocket client** (use a tool like Postman or a browser WebSocket client)
3. **Connect driver**: `ws://localhost:8000/ws/driver/1` (replace 1 with actual driver ID)
4. **Request ride** as a rider via REST API
5. **Driver receives notification** in WebSocket connection
6. **Driver accepts** via `POST /drivers/accept-ride/{ride_id}`
7. **Rider gets notified** via their WebSocket connection

---

### Optional: Add timeout mechanism

Create a background task that checks for pending rides older than 30 seconds and auto-notifies the next driver. This requires celery or similar, which can be Phase 5.

---

## ✅ Done

- [x] FastAPI setup
- [x] Async DB with asyncpg + Supabase
- [x] Alembic configured
- [x] User model
- [x] JWT Auth (register + login)
- [x] OAuth2PasswordRequestForm
- [x] Driver and Ride models
- [x] Alembic migrations for drivers and rides tables
- [x] Haversine distance calculation utility
- [x] Fare calculation (base + per-km rate)
- [x] Driver registration endpoint
- [x] Driver location update endpoint
- [x] Ride request endpoint with nearest-driver matching
- [x] Get ride details endpoint
- [x] Phase 3: Ride Booking Core complete

