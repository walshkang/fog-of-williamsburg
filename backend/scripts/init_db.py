"""
Initialize the database schema for local development.

Usage:

    python -m backend.scripts.init_db
"""

import asyncio

# Import models so that all tables are registered on Base.metadata
from .. import models  # noqa: F401
from ..database import Base, engine


async def _init() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def main() -> None:
    asyncio.run(_init())


if __name__ == "__main__":
    main()


