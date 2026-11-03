import asyncio
from datetime import datetime

from asyncpg import Connection, Pool
from dateutil.relativedelta import relativedelta
from loguru import logger

from everwealth.budgets.models.budgets import BudgetPeriod


async def ensure_current_period(
    user_id: str, connection: Connection, now: datetime | None = None
) -> BudgetPeriod:
    """Initialize each month once, including periods created by the old page path."""
    now = now or datetime.utcnow()
    target = BudgetPeriod.for_month(user_id, now.year, now.month)
    async with connection.transaction():
        # Serialize the scheduler and page requests for the same user.
        await connection.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended($1, 0))", f"budget-rollover:{user_id}"
        )
        current = await BudgetPeriod.fetch_for_month(user_id, now.year, now.month, connection)
        if current and current.rollover_completed:
            return current

        # Skip legacy empty periods, but respect an initialized empty period:
        # the user may have intentionally deleted its budgets.
        previous = await connection.fetchrow(
            """
            SELECT p.* FROM budget_periods p
            WHERE p.user_id = $1 AND p.start < $2
              AND (p.rollover_completed OR EXISTS (
                  SELECT 1 FROM budgets b WHERE b.period_id = p.id AND b.user_id = $1
              ))
            ORDER BY p.start DESC LIMIT 1
            """,
            user_id,
            target.start,
        )
        source = BudgetPeriod.model_validate(dict(previous)) if previous else None
        next_start = source.start + relativedelta(months=1) if source else target.start
        while next_start <= target.start:
            period = await BudgetPeriod.fetch_for_month(
                user_id, next_start.year, next_start.month, connection
            )
            if period is None:
                period = await BudgetPeriod.for_month(
                    user_id, next_start.year, next_start.month
                ).save(connection)
            if not period.rollover_completed:
                # Older rollovers added a month to the previous end date, which
                # can leave March (for example) ending on the 28th.
                period.end = BudgetPeriod.for_month(
                    user_id, period.start.year, period.start.month
                ).end
                if source:
                    await connection.execute(
                        """
                        INSERT INTO budgets (
                            id, period_id, user_id, category_id, amount,
                            created_at, updated_at
                        )
                        SELECT substr(md5(random()::text), 1, 22), $1, b.user_id,
                               b.category_id, b.amount, $2, $2
                        FROM budgets b
                        WHERE b.period_id = $3 AND b.user_id = $4
                          AND NOT EXISTS (
                              SELECT 1 FROM budgets existing
                              WHERE existing.period_id = $1
                                AND existing.category_id = b.category_id
                          )
                        """,
                        period.id,
                        now,
                        source.id,
                        user_id,
                    )
                await connection.execute(
                    'UPDATE budget_periods SET rollover_completed = TRUE, "end" = $2 WHERE id = $1',
                    period.id,
                    period.end,
                )
                period.rollover_completed = True
                logger.info("Initialized budget period {} for user {}", period.start, user_id)
            source = period
            next_start = period.start + relativedelta(months=1)
        return source


async def rollover_expired_periods(pool: Pool) -> None:
    now = datetime.utcnow()
    async with pool.acquire() as connection:
        users = await connection.fetch("SELECT DISTINCT user_id FROM budget_periods")
        for user in users:
            try:
                await ensure_current_period(user["user_id"], connection, now)
            except Exception:
                # One user's failure must not prevent rollover for everyone else.
                logger.exception("Budget rollover failed for user {}", user["user_id"])


async def run_rollover_scheduler(pool: Pool) -> None:
    while True:
        try:
            await rollover_expired_periods(pool)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Budget rollover failed")
        await asyncio.sleep(3600)
