"""
Initialize the database schema for local development.

Usage:

    python -m backend.scripts.init_db
"""

import asyncio

from ..database import Base, engine


async def _init() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def main() -> None:
    asyncio.run(_init())


if __name__ == "__main__":
    main()


