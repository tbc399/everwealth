from datetime import datetime
from enum import Enum
from typing import List, Optional

from asyncpg import Connection
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field
from shortuuid import uuid


class CategoryType(Enum):
    income = "income"
    expense = "expense"


class Category(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(default_factory=uuid)
    name: str
    type: CategoryType = Field(default=CategoryType.expense)
    user_id: Optional[str] = None
    parent_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @staticmethod
    async def create(
        name: str,
        user_id: str,
        db: Connection,
        type: CategoryType = CategoryType.expense,
        parent_id: Optional[str] = None,
    ) -> "Category":
        existing = await db.fetchrow(
            "SELECT * FROM categories WHERE LOWER(name) = LOWER($1) AND user_id = $2",
            name.strip(),
            user_id,
        )
        if existing:
            if parent_id and not existing["parent_id"]:
                await db.execute(
                    "UPDATE categories SET parent_id = $1, updated_at = $2 WHERE id = $3",
                    parent_id,
                    datetime.utcnow(),
                    existing["id"],
                )
                existing = await db.fetchrow(
                    "SELECT * FROM categories WHERE id = $1",
                    existing["id"],
                )
            return Category.model_validate(dict(existing))
        category = Category(name=name.strip(), user_id=user_id, type=type, parent_id=parent_id)
        await db.execute(
            """
            INSERT INTO categories (id, name, type, user_id, parent_id, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            category.id,
            category.name,
            category.type,
            category.user_id,
            category.parent_id,
            category.created_at,
            category.updated_at,
        )
        return category

    @staticmethod
    async def create_many(categories, db: Connection):
        if not categories:
            return
        async with db.transaction():
            await db.executemany(
                """
                INSERT INTO categories (id, name, type, user_id, parent_id, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                (
                    (
                        category.id,
                        category.name,
                        category.type,
                        category.user_id,
                        category.parent_id,
                        category.created_at,
                        category.updated_at,
                    )
                    for category in categories
                ),
            )

    @staticmethod
    async def fetch(id: str, user_id: str, db: Connection):
        sql = "SELECT * FROM categories WHERE id = $1 AND user_id = $2"
        logger.debug(f"Executing SQL: {sql}")
        record = await db.fetchrow(sql, id, user_id)
        return Category.model_validate(dict(record)) if record else None

    @staticmethod
    async def fetch_many(user_id: str, db: Connection):
        logger.debug(f"Fetching categories for {user_id}")
        records = await db.fetch(
            """
            SELECT *
            FROM categories
            WHERE user_id = $1
            ORDER BY type, parent_id NULLS FIRST, name
            """,
            user_id,
        )
        return [Category.model_validate(dict(x)) for x in records]

    @staticmethod
    async def fetch_grouped(user_id: str, db: Connection):
        categories = await Category.fetch_many(user_id, db)
        children_by_parent = {}
        groups = []

        for category in categories:
            if category.parent_id:
                children_by_parent.setdefault(category.parent_id, []).append(category)

        parent_ids = {category.id for category in categories if not category.parent_id}
        for category in categories:
            if not category.parent_id:
                groups.append(
                    {
                        "parent": category,
                        "children": children_by_parent.get(category.id, []),
                    }
                )
            elif category.parent_id not in parent_ids:
                groups.append({"parent": category, "children": []})

        return groups
