from lucette import Subscriber
from everwealth.auth.events import UserCreated
from loguru import logger
from everwealth.settings.categories import Category
#from everwealth.settings import categories


sub = Subscriber()


@sub.subscribe
async def create_default_categories(message: UserCreated):
    logger.info(f"Creating default categories for user {message.user_id}")
    cats = [
        Category(name="Mortgage", user_id=message.user_id),
    ]
    print(cats)
    #categories.bulk_create(cats, db)


