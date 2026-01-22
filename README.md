# Fog of War (NYC)

> **"Civilization VI meets Strava."**

Gamifying fitness through exploration. Fog of War tracks your movement (running, cycling, walking) and unveils a "fog of war" map of your city, incentivizing you to take new routes and explore every corner of your neighborhood.

![Project Status: Phase 1](https://img.shields.io/badge/Status-Phase_1_MVP-blue)
![Stack: Expo + FastAPI + PostGIS](https://img.shields.io/badge/Stack-Expo_|_FastAPI_|_PostGIS-black)
![Platform: Web](https://img.shields.io/badge/Platform-Web_(Desktop_&_Mobile)-green)

---

## The Concept

Most fitness apps focus on *performance* (speed, heart rate, PRs).  
**Fog of War focuses on *exploration*.**

1. **Select your battleground:** Choose a borough (e.g., Brooklyn).
2. **Move:** Run or walk your usual route—or try a new one.
3. **Upload:** Sync your activity (GPX file).
4. **Reveal:** Watch the fog lift from the map.
5. **Conquer:** Increase your "Exploration Score" until you've uncovered 100% of the borough.

---

## Tech Stack

- **Platform:** Web browser (desktop & mobile) — native apps are out of scope for MVP
- **Frontend:** [Expo](https://expo.dev/) (React Native for Web/TypeScript)
- **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **Database:** PostgreSQL + [PostGIS](https://postgis.net/)
- **Auth:** [Supabase Auth](https://supabase.com/auth) (planned)
- **Maps:** [Mapbox GL JS](https://docs.mapbox.com/mapbox-gl-js/api/)
- **Geospatial Logic:** PostGIS spatial operations (buffer, union, intersection)

---

## Architecture (MVP)

We use **PostGIS polygon operations** for spatial tracking:

1. **Input:** User uploads a `.gpx` file.
2. **Processing (Backend):**
   - Trace is snapped to roads via Mapbox Map Matching API.
   - Route is buffered by 25m to create a "revealed" polygon.
   - New polygon is merged with the user's existing "unveiled area" using `ST_Union`.
3. **Storage:** The merged polygon geometry is stored per user/borough.
4. **Scoring:** Exploration % = `ST_Area(unveiled) / ST_Area(borough) * 100`
5. **Rendering:** Frontend fetches the polygon as GeoJSON and renders it as a "hole" in the fog overlay.

---

## Getting Started

### Prerequisites

- Python 3.13+
- Node.js 20+ and npm
- Docker + Docker Compose (for Postgres/PostGIS)
- A [Mapbox](https://mapbox.com) account (free tier is fine)

### Quick Start (Docker)

```bash
# Start backend + database
docker compose up --build
```

This starts:
- **Postgres/PostGIS** on `localhost:5432`
- **FastAPI backend** on `http://localhost:8000`

### Manual Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/yourusername/fog-of-williamsburg.git
   cd fog-of-williamsburg
   ```

2. **Start the database**
   ```bash
   docker compose up db
   ```

3. **Backend setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Environment variables**
   
   Create `.env` in repo root:
   ```bash
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/fog_of_williamsburg
   MAPBOX_PUBLIC_TOKEN=pk.eyJ...
   MAPBOX_SECRET_TOKEN=sk.eyJ...
   ```

5. **Initialize database**
   ```bash
   python -m backend.scripts.init_db
   python -m backend.scripts.load_boroughs
   ```

6. **Run backend**
   ```bash
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Frontend setup**
   ```bash
   cd frontend
   npm install
   npm run web
   ```

   This launches the app in your browser at `http://localhost:8081`. Update the API base URL in `frontend/api.ts` to point to your backend.

---

## Roadmap: Phase 1 (MVP)

- [x] FastAPI backend with PostGIS
- [x] Borough boundary data imported
- [x] Unveiled area data model
- [x] Core score calculation endpoint
- [ ] Supabase Auth integration
- [ ] Mapbox map rendering
- [ ] GPX file upload + Map Matching
- [ ] Fog overlay rendering
- [ ] Unveiling animation

See `roadmap.json` for detailed task breakdown and `prd.md` for product requirements.

---

## Project Structure

```
fog-of-williamsburg/
├── backend/           # FastAPI app
│   ├── main.py        # App entry point
│   ├── models.py      # SQLAlchemy models
│   ├── routes/        # API endpoints
│   └── scripts/       # DB init & data loading
├── frontend/          # Expo app (web target for MVP)
│   ├── App.tsx        # Main app component
│   ├── api.ts         # Backend API client
│   └── storage.ts     # Local storage helpers
├── data/              # Static data files
│   └── nyc_boroughs.geojson
├── docker-compose.yml
├── roadmap.json       # Project roadmap
└── prd.md             # Product requirements
```

---

## Contributing

This is currently a solo project focused on the NYC MVP. Contributions and feedback welcome!

## License

MIT
