from lucette import BaseMessage


class UserCreated(BaseMessage):
    user_id: str
