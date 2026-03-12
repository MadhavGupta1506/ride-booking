# 🚗 Uber Clone — Project Roadmap

> Track overall project progress phase by phase.

---

## ✅ Phase 1 — Project Foundation
> _Status: Complete_

- [x] FastAPI project scaffolded with modular route structure
- [x] Async PostgreSQL connection via asyncpg + SQLAlchemy
- [x] Supabase database configured (PgBouncer `statement_cache_size=0` fix applied)
- [x] Alembic set up for database migrations
- [x] `User` model with `id`, `name`, `email`, `password`, `role`, `created_at`, `updated_at`
- [x] Auth routes — `POST /auth/register`, `POST /auth/login`
- [x] JWT token generation & validation
- [x] OAuth2PasswordRequestForm wired (Swagger UI Authorize button works)
- [x] CORS middleware configured
- [x] `backend/__init__.py` sys.path fix for package-style running

---

## ✅ Phase 2 — Core Database Models
> _Status: Complete_

- [x] `Driver` model — `user_id (FK → users)`, `current_lat`, `current_lng`, `vehicle_type`, `rating`, `total_rides`
- [x] `Ride` model — `rider_id (FK)`, `driver_id (FK, nullable)`, `pickup_lat`, `pickup_lng`, `dropoff_lat`, `dropoff_lng`, `status`, `fare`, `distance_km`, `created_at`, `updated_at`
- [x] `RideStatus` enum — `pending` / `accepted` / `completed` / `cancelled`
- [x] Added models to `alembic/env.py` imports
- [x] `base.py` extracted so Alembic imports don't trigger async engine
- [x] Migration generated & applied — `drivers` and `rides` tables live in Supabase

---

## 🔲 Phase 3 — Ride Booking Core
> _Status: Up Next_

**Goal:** Understand how ride requests work and how the nearest driver is found.

### Driver Endpoints (`/drivers`)
- [ ] `POST /drivers/register` — register a driver profile (with starting `current_lat` / `current_lng`)
- [ ] `PATCH /drivers/location` — update driver's GPS position (useful for local testing)

### Rider Endpoints (`/rides`)
- [ ] `POST /rides/request` — submit pickup + dropoff coords → Haversine finds nearest driver → ride row created & assigned
- [ ] `GET /rides/{id}` — check ride details and assigned driver

### Haversine Utility (`backend/utils/haversine.py`)
- [ ] `haversine(lat1, lng1, lat2, lng2) -> float` — returns distance in km
- [ ] Fare calculation — `base_fare + (rate_per_km × distance_km)`
- [ ] Nearest-driver query — fetch all drivers, compute distance from pickup, return closest

---

## 🔲 Phase 4 — Real-time (WebSockets)
> _Status: Not Started_

- [ ] WebSocket connection manager (manage active connections per ride/user)
- [ ] `WS /ws/ride/{ride_id}` — rider receives live driver location + status changes
- [ ] `WS /ws/driver/{driver_id}` — driver receives incoming ride request notifications
- [ ] Broadcast ride status changes to connected clients

---

## 🔲 Phase 5 — Auth & Security Hardening
> _Status: Not Started_

- [ ] `GET /auth/me` — return currently authenticated user
- [ ] Role-based route guards (`rider_required`, `driver_required` dependencies)
- [ ] Refresh token endpoint
- [ ] Block duplicate driver registration
- [ ] Rate limiting on `/auth/login` and `/auth/register`

---

## 🔲 Phase 6 — Frontend
> _Status: Not Started_

- [ ] Auth pages — Login / Register with role selection
- [ ] Map integration (Leaflet.js — already has `index.html` + `script.js`)
- [ ] Rider flow — pick pickup/dropoff on map → request ride → see assigned driver
- [ ] Driver flow — set location → see assigned rides
- [ ] Ride history page

---

## 🔲 Phase 7 — Production Readiness
> _Status: Not Started_

- [ ] Pydantic Settings with `.env` validation
- [ ] Structured JSON logging
- [ ] Global exception handler
- [ ] `Dockerfile` + `docker-compose.yml`
- [ ] Deploy backend to Railway / Render
- [ ] Deploy frontend to Vercel / Netlify
- [ ] Set up environment secrets in hosting platform

---

## 📊 Overall Progress

| Phase | Description              | Status         |
|-------|--------------------------|----------------|
| 1     | Foundation               | ✅ Complete    |
| 2     | Core Models & Migrations | ✅ Complete    |
| 3     | Ride Booking Core        | 🔲 Up Next     |
| 4     | Real-time WebSockets     | 🔲 Not Started |
| 5     | Auth & Security          | 🔲 Not Started |
| 6     | Frontend                 | 🔲 Not Started |
| 7     | Production Readiness     | 🔲 Not Started |
