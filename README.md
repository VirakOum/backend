# FastAPI Learning Project

A small FastAPI starter project for learning how to build APIs.

The app is organized with a small service layer and routers so you can learn a simple but realistic FastAPI structure.

It now uses PostgreSQL in Docker and Alembic for database migrations.

## Active backend paths

Use these directories as the backend source of truth:

- `app/`
- `alembic/`
- `tests/`
- `scripts/`

The previous nested checkout under `python/` was removed after being identified as a stale duplicate with divergent history.

## Run it

1. Create a virtual environment:

   ```bash
   /usr/local/bin/python3 -m venv .venv
   ```

2. Activate it:

   ```bash
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Start the app:

   ```bash
   uvicorn app.main:app --reload
   ```

5. Start PostgreSQL with Docker:

   ```bash
   docker compose up -d db
   ```

6. Run the first migration:

   ```bash
   alembic upgrade head
   ```

7. To access from other devices on your WiFi (e.g. Flutter app on a phone):

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

   Find your local IP with `ifconfig` (e.g. `192.168.1.x`) and use that in your app's API config.

8. Run the tests:

   ```bash
   pytest
   ```

8. Seed demo data:

   ```bash
   python3 scripts/seed_demo_data.py
   ```

### Run with Docker

#### Local Development Mode
For local development, run Docker Compose with default host port bindings (`http://localhost:8000` for FastAPI and `5433` for PostgreSQL):

```bash
docker compose up --build
```

#### Production / Coolify Deployment Mode
For production deployment behind Coolify / Traefik reverse proxy (to prevent host port 8000 collisions):

Set **Docker Compose Location** in Coolify settings to:
```
/docker-compose.prod.yml
```

Or run manually with the production compose file:
```bash
docker compose -f docker-compose.prod.yml up -d --build
```


## Web Interfaces & System Endpoints

- **Public Landing Website**: `https://mytravel.taxi` (`GET /`)
  - Modern bilingual (English & Khmer) showcase for MyTravel inter-city taxi & ride-hailing services.
  - Interactive Cambodia province route fare estimator, passenger & driver app feature showcases, national emergency numbers (117, 118, 119), live stats counter, and FAQ accordion.
  - Frontend structure in `app/static/site/` (MVC: `js/models/data.js`, `css/style.css`, `js/controllers/main.js`).

- **Admin Command Portal**: `https://mytravel.taxi/admin/mytravel` (`GET /admin/mytravel/`)
  - Fleet management, driver verification, debt limits, revenue analytics, system announcements, and banner ad management.
  - Accessing `GET /admin` or `GET /admin/` automatically redirects to `/admin/mytravel/`.
  - Static dashboard files located in `app/static/admin/`.

- **API Base Path**: `https://mytravel.taxi/v1/api` (`GET /v1/api`)
  - All backend endpoints are mounted under the unified `/v1/api` prefix.
  - Interactive Swagger Docs: `https://mytravel.taxi/v1/api/docs` or `http://localhost:8000/v1/api/docs` (also available via `/docs`).
  - OpenAPI Specification: `https://mytravel.taxi/v1/api/openapi.json` or `http://localhost:8000/v1/api/openapi.json`.

## Try these routes

- `GET /` - Public Showcase Landing Website
- `GET /admin/mytravel` - Admin Control Dashboard
- `GET /v1/api` - API Base Information
- `GET /v1/api/health` or `GET /health` - Service Health Check
- `GET /v1/api/items`
- `POST /v1/api/items`
- `GET /v1/api/items/{item_id}`
- `PUT /v1/api/items/{item_id}`
- `DELETE /v1/api/items/{item_id}`
- `POST /v1/api/travel/auth/signup`
- `POST /v1/api/travel/auth/login`
- `GET /v1/api/travel/auth/me`
- `GET /v1/api/travel/users/{user_id}`
- `POST /v1/api/travel/vehicles`
- `GET /v1/api/travel/vehicles/{vehicle_id}`
- `POST /v1/api/travel/trips`
- `GET /v1/api/travel/trips/{trip_id}`
- `GET /v1/api/travel/trips/search?departure_province=...&destination_province=...`
- `POST /v1/api/travel/bookings`
- `GET /v1/api/travel/bookings/{booking_id}`
- `POST /v1/api/travel/payments`
- `GET /v1/api/travel/payments/{payment_id}`
- `GET /v1/api/passenger/profile/places`
- `PUT /v1/api/passenger/profile/places/{key}`
- `GET /v1/api/passenger/trips/search-config`
- `GET /v1/api/addresses/provinces`
- `GET /v1/api/addresses/districts/{province_code}`
- `GET /v1/api/addresses/communes/{district_code}`
- `GET /v1/api/addresses/villages/{commune_code}`
- `GET /v1/api/addresses/by-type/{address_type}`
- `GET /v1/api/addresses/by-parent/{parent_code}`
- `GET /v1/api/addresses/code/{code}`
- `POST /v1/api/addresses/forms`

Open `http://127.0.0.1:8000/v1/api/docs` (or `/docs`) for interactive API docs.

## Travel auth

The travel API uses bearer-token authentication under `/v1/api/travel/auth/`.

1. Sign up with `POST /v1/api/travel/auth/signup`
2. Log in with `POST /v1/api/travel/auth/login`
3. Send the returned token in `Authorization: Bearer <token>`

Signup body example:

```json
{
  "phone": "012345678",
  "full_name": "Sok Dara",
  "role": "driver",
  "password": "strongpass123",
  "avatar_url": null
}
```

After login/signup, authenticated routes derive the acting user from the token:

- vehicle creation uses the logged-in driver as `owner_id`
- trip creation uses the logged-in driver as `driver_id`
- booking creation uses the logged-in passenger as `passenger_id`

Demo seed accounts after running `python3 scripts/seed_demo_data.py`:

- driver: `012345678` / `strongpass123`
- passenger: `099887766` / `strongpass123`

## Database and migrations

The default database connection comes from `DATABASE_URL`. For local development with Docker, the app container uses the hostname `db`.

Useful Alembic commands:

```bash
alembic revision --autogenerate -m "add design travel"
alembic upgrade head
alembic downgrade -1
```

The `addresses` table is seeded automatically from [`addresses.json`](addresses.json) when you run `alembic upgrade head`.
## add a reusable generator script that creates model + route + CRUD wiring in your exact project style

Example:
python scripts/generate_crud.py Category --fields name:str:100 description:str?:300
alembic revision --autogenerate -m "create categories table"
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 
c:\Users\USer\Documents\Github\Mytravel\backend_repo\.venv\Scripts\Activate.ps1
git push upstream main