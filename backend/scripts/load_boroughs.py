"""
One-time loader for NYC Borough GeoJSON into the PostGIS `boroughs` table.

Usage (example):

    python -m backend.scripts.load_boroughs path/to/nyc_boroughs.geojson
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import SessionLocal


async def load_boroughs(geojson_path: Path) -> None:
    if not geojson_path.exists():
        raise SystemExit(f"GeoJSON file not found: {geojson_path}")

    data = json.loads(geojson_path.read_text())
    features = data.get("features", [])
    if not features:
        raise SystemExit("No features found in GeoJSON.")

    async with SessionLocal() as session:  # type: AsyncSession
        for feature in features:
            props = feature.get("properties", {})
            # NYC open data sometimes uses different keys; support a few.
            name = (
                props.get("boro_name")
                or props.get("boroname")
                or props.get("name")
            )
            geom = json.dumps(feature.get("geometry"))
            if not name or not geom:
                continue

            # Insert or update borough using PostGIS functions.
            stmt = text(
                """
                INSERT INTO boroughs (name, geometry, total_area)
                VALUES (
                    :name,
                    ST_SetSRID(ST_GeomFromGeoJSON(:geom)::geometry, 4326),
                    ST_Area(
                        ST_Transform(
                            ST_SetSRID(ST_GeomFromGeoJSON(:geom)::geometry, 4326),
                            3857
                        )
                    )
                )
                ON CONFLICT (name) DO UPDATE
                SET
                    geometry = EXCLUDED.geometry,
                    total_area = EXCLUDED.total_area;
                """
            )
            await session.execute(stmt, {"name": name, "geom": geom})

        await session.commit()


def main(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        raise SystemExit("Usage: python -m backend.scripts.load_boroughs path/to/file.geojson")

    geojson_path = Path(argv[0]).expanduser().resolve()
    asyncio.run(load_boroughs(geojson_path))


if __name__ == "__main__":
    main()


