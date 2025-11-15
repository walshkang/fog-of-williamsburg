## 🗺️ PRD: "Project Fog of War" (MVP)

### 1. Objective
To create a gamified mobile app that motivates users to explore their city by foot, bike, or run. The MVP will use a "fog of war" mechanic, allowing users to "unveil" a map of their chosen NYC borough, with the primary goal of reaching 100% exploration.

### 2. Target User
* **The "Completionist":** A runner, walker, or cyclist who is motivated by stats, achievements, and "completing" a challenge.
* **The "Explorer":** A new or long-time NYC resident who wants a fun, game-like incentive to discover new streets and neighborhoods.

### 3. Core User Stories (The "Epics")

**Onboarding:**
* As a new user, I want to choose one (and only one) NYC borough to be my "focus area" (e.g., "Brooklyn") so that the app is personalized to my primary goal.

**Main Dashboard:**
* As a user, I want to see a map of my chosen borough with a "fog of war" overlay showing my explored vs. unexplored areas.
* As a user, I want to see a single, large score at all times: **`XX.XX% of [My Borough] Explored`**.

**Activity Import (MVP v1.0):**
* As a user, I want to be able to manually upload a `.gpx` file from my computer or phone.
* As a user, I want to manually "check in" at my current location to unveil a 100m radius, so I can get credit for places I visit without an active workout.

**The "Magic Moment" (The Unveiling):**
* As a user, immediately after an import, I want to see a "replay" animation of my route being drawn on the map.
* As a user, during the replay, I want to hear a satisfying "loading" or "unveiling" sound, ending with a "ding" when complete.
* As a user, after the animation, I want to see a full-screen summary that shows:
    1.  `+[New % Explored]`
    2.  `+[#] of New Streets Visited`
    3.  `+[#] of New City Blocks Visited`

**Gamification (Missions):**
* As a user, I want to see a list of simple missions related to **discovery** (e.g., "Explore 3 new streets in Brooklyn") and **completion** (e.g., "Reach 5% exploration of your borough").

### 4. Technical & Data Requirements

* **Mapping Provider:** **Mapbox**. It will be used for the base map tiles and all map-related logic.
* **Map Cleaning:** All GPS tracks (from `.gpx`, Strava, etc.) **must** be processed by the **Mapbox Map Matching API**. This will "snap" the messy GPS data to the actual road network, ensuring clean, accurate buffers that don't cut across buildings.
* **Borough Data:** The "fog of war" boundary for the MVP will be the official **NYC Borough Boundaries GeoJSON file**. The best source for this is from NYC Planning: [Borough Boundaries GeoJSON Download Page](https://www.nyc.gov/content/planning/pages/resources/datasets/borough-boundaries).
* **Core Logic:** The app will calculate the geospatial `intersection` of the user's "unveiled polygons" (25m buffer for routes, 100m for check-ins) with the chosen borough's polygon. The score is `(Area_of_Intersection / Total_Area_of_Borough) * 100`.

### 5. Out of Scope (For "Phase 2")
* **No Social:** All leaderboards, friend activity, and social sharing are out of scope for the MVP.
* **No Other Cities:** The data logic will be hard-coded for NYC boroughs only.
* **No Automatic Import (v1.0):** Strava and Apple HealthKit integrations will be a "fast follow" after the core `.gpx` logic is proven.

---

This PRD gives us a rock-solid blueprint. The next logical step is to create the visual design, or "wireframes," for the app.

Would you like to start by designing the two most important screens: the **Main Dashboard** and the **"Unveiling" Summary Screen**?