# FastAPI Learning Project

A small FastAPI starter project for learning how to build APIs.

The app is organized with a small service layer and routers so you can learn a simple but realistic FastAPI structure.

It now uses PostgreSQL in Docker and Alembic for database migrations.

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

7. Run the tests:

   ```bash
   pytest
   ```

8. Seed demo data:

   ```bash
   python3 scripts/seed_demo_data.py
   ```

### Run everything in Docker

```bash
docker compose up --build
```

The app starts on `http://127.0.0.1:8000` and runs `alembic upgrade head` before launching Uvicorn.

## Try these routes

- `GET /`
- `GET /health`
- `GET /items`
- `POST /items`
- `GET /items/{item_id}`
- `PUT /items/{item_id}`
- `DELETE /items/{item_id}`
- `POST /travel/auth/signup`
- `POST /travel/auth/login`
- `GET /travel/auth/me`
- `GET /travel/users/{user_id}`
- `POST /travel/vehicles`
- `GET /travel/vehicles/{vehicle_id}`
- `POST /travel/trips`
- `GET /travel/trips/{trip_id}`
- `GET /travel/trips/search?departure_province=...&destination_province=...`
- `POST /travel/bookings`
- `GET /travel/bookings/{booking_id}`
- `POST /travel/payments`
- `GET /travel/payments/{payment_id}`
- `GET /passenger/profile/places`
- `PUT /passenger/profile/places/{key}`
- `GET /passenger/trips/search-config`
- `GET /addresses/provinces`
- `GET /addresses/districts/{province_code}`
- `GET /addresses/communes/{district_code}`
- `GET /addresses/villages/{commune_code}`
- `GET /addresses/by-type/{address_type}`
- `GET /addresses/by-parent/{parent_code}`
- `GET /addresses/code/{code}`
- `POST /addresses/forms`

Open `http://127.0.0.1:8000/docs` for interactive API docs.

## Travel auth

The travel API now uses bearer-token authentication.

1. Sign up with `POST /travel/auth/signup`
2. Log in with `POST /travel/auth/login`
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
