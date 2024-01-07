from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel


class Budget(BaseModel):
    month = datetime


class Category(BaseModel):
    budget = Budget
    name = str
    total = float
    frequency = "monthly" | "yearly"
    rollover = bool




class ConnectedAccount(BaseModel):
    pass

class AccountTransaction(BaseModel):
    account = ConnectedAccount


class User:
    pass
