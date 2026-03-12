from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["Drivers"],)

@router.get("/drivers")
async def get_drivers():
    return[
  {"id": 1, "name": "Driver A", "lat": 23.2599, "lng": 77.4126},
  {"id": 2, "name": "Driver B", "lat": 23.2610, "lng": 77.4150}
]
