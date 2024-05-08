from lucette import Subscriber, BaseMessage

from everwealth.settings.categories import Category
from everwealth import transactions

subscriber = Subscriber()


class CategoryNameUpdated(BaseMessage):
    name: str


@subscriber.subscribe
async def update_category(message: CategoryNameUpdated):
    await transactions.update()
