## Fog of Williamsburg

Gamified NYC exploration app with a **"fog of war"** mechanic. Users pick a single NYC borough and gradually unveil it by walking, running, or riding through the streets. This repo contains:

- **Backend**: FastAPI + Postgres/PostGIS (geospatial scoring, borough data, activity processing)
- **Frontend**: Expo / React Native app (mobile-first, can also run on web in dev)

The product vision and roadmap live in `prd.md` and `roadmap.json`.

---

## Architecture

- **Backend** (`backend/`)
  - FastAPI app (`backend.main:app`)
  - Async Postgres + PostGIS (via `DATABASE_URL`)
  - Mapbox integration for Map Matching (planned)
- **Database**
  - Postgres + PostGIS, provisioned via `docker-compose.yml`
  - NYC borough GeoJSON in `data/nyc_boroughs.geojson` (import scripts in `backend/scripts/`)
- **Frontend** (`frontend/`)
  - Expo app (React Native) with TypeScript
  - Talks to the FastAPI backend over HTTP

---

## Prerequisites

- **Required**
  - Python 3.13 (or the version used by the provided `venv/`)
  - Node.js + npm (for Expo; recommended: Node 20+)
  - Docker + Docker Compose (for Postgres/PostGIS + backend, or you can run services locally without Docker)
- **Recommended**
  - `expo` CLI installed globally: `npm install -g expo`

---

## Running Everything with Docker (Backend + DB)

From the repo root:

```bash
docker compose up --build
```

This will:

- Start **Postgres/PostGIS** on `localhost:5432`
- Start the **FastAPI backend** on `http://localhost:8000`

The backend container runs:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Environment variables:

- `MAPBOX_SECRET_TOKEN` (optional for now; needed when Map Matching is wired up)
- `MAPBOX_PUBLIC_TOKEN` (for map rendering on the frontend)

You can pass these into Docker via your shell environment (e.g. an `.env` file loaded by your shell) before running `docker compose up`.

---

## Running Backend Locally (Without Docker)

1. **Create / activate virtualenv** (optional if you use the existing `venv/`):

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Start Postgres/PostGIS** (easiest via Docker only for DB):

   ```bash
   docker compose up db
   ```

   This exposes Postgres on `localhost:5432` with:

   - `POSTGRES_DB=fog_of_williamsburg`
   - `POSTGRES_USER=postgres`
   - `POSTGRES_PASSWORD=postgres`

4. **Set backend env (optional, defaults are sensible)**:

   Create a `.env` in the repo root or `backend/` (FastAPI settings look for `.env` via `pydantic-settings`), e.g.:

   ```bash
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/fog_of_williamsburg
   MAPBOX_PUBLIC_TOKEN=your_public_token_here
   MAPBOX_SECRET_TOKEN=your_secret_token_here
   ```

5. **Run the backend** from the repo root:

   ```bash
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

The backend will be available at `http://localhost:8000`.

---

## Running the Frontend (Expo)

1. **Install frontend dependencies**:

   ```bash
   cd frontend
   npm install
   ```

2. **Start Expo**:

   ```bash
   npm run start
   # or
   npm run ios
   npm run android
   npm run web
   ```

3. **Point frontend at backend**:

   - The API client lives in `frontend/api.ts`.
   - Ensure the base URL there matches where your backend is running (e.g. `http://localhost:8000` for simulators / web, or your machine’s LAN IP for physical devices).

---

## Data & Migration Scripts

- **Borough GeoJSON**: `data/nyc_boroughs.geojson`
- **Database init / import scripts** (WIP, but intended usage):
  - `backend/scripts/init_db.py`: create tables, apply basic schema
  - `backend/scripts/load_boroughs.py`: load borough shapes into PostGIS

You can typically run them like:

```bash
python -m backend.scripts.init_db
python -m backend.scripts.load_boroughs
```

Make sure your `DATABASE_URL` is set before running.

---

## Tests

Backend tests live under `tests/` and `notion_sync/`:

```bash
pytest
```

---

## Project Docs

- **Product Requirements**: `prd.md`
- **Roadmap & Epics**: `roadmap.json`

These files describe the long-term vision, phases, and detailed tasks for the fog-of-war exploration experience.

---

## Contributing / Next Steps

- Focus of the current phase: **NYC-only "Solo Explorer" MVP** with:
  - Borough selection
  - Mapbox-backed fog-of-war visualization
  - GPX upload + manual check-ins
  - Core `% of borough explored` scoring
- If you’re picking this up fresh, the quickest way to contribute is:
  1. Get Docker + backend running.
  2. Run the Expo app and hard-code pointing to `localhost:8000`.
  3. Implement one epic/task from `roadmap.json` at a time.
