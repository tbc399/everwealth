import asyncio
from datetime import datetime

from asyncpg import Pool
from dateutil.relativedelta import relativedelta
from loguru import logger
from shortuuid import uuid


async def rollover_expired_periods(pool: Pool) -> None:
    async with pool.acquire() as connection:
        periods = await connection.fetch(
            """
            SELECT DISTINCT ON (user_id) *
            FROM budget_periods
            ORDER BY user_id, "end" DESC
            """
        )
        for period in periods:
            if period["end"] >= datetime.utcnow():
                continue
            next_start = period["start"] + relativedelta(months=1)
            next_end = period["end"] + relativedelta(months=1)
            async with connection.transaction():
                existing = await connection.fetchrow(
                    "SELECT id FROM budget_periods WHERE user_id = $1 AND start = $2",
                    period["user_id"],
                    next_start,
                )
                if existing:
                    continue
                new_period_id = uuid()
                await connection.execute(
                    'INSERT INTO budget_periods (id, user_id, start, "end", created_at) VALUES ($1, $2, $3, $4, $5)',
                    new_period_id,
                    period["user_id"],
                    next_start,
                    next_end,
                    datetime.utcnow(),
                )
                await connection.execute(
                    """
                    INSERT INTO budgets (
                        id, period_id, user_id, category_id, amount, rollover,
                        created_at, updated_at
                    )
                    SELECT substr(md5(random()::text), 1, 22), $1, user_id,
                           category_id, amount, rollover, $2, $2
                    FROM budgets
                    WHERE period_id = $3 AND rollover = TRUE
                    """,
                    new_period_id,
                    datetime.utcnow(),
                    period["id"],
                )
                logger.info("Rolled over budget period for user {}", period["user_id"])


async def run_rollover_scheduler(pool: Pool) -> None:
    while True:
        try:
            await rollover_expired_periods(pool)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Budget rollover failed")
        await asyncio.sleep(3600)
