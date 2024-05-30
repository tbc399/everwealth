from lucette import BaseMessage, Subscriber

from everwealth import transactions
from everwealth.settings.categories import Category

subscriber = Subscriber()


class CategoryNameUpdated(BaseMessage):
    name: str


@subscriber.subscribe
async def update_category(message: CategoryNameUpdated):
    await transactions.update()
