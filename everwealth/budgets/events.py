from loguru import logger
from lucette import Subscriber

from everwealth import db
from everwealth.auth.events import UserCreated

from . import Category, CategoryType

sub = Subscriber()


async def create_category_tree(
    connection,
    user_id: str,
    category_type: CategoryType,
    category_groups,
):
    for parent_name, child_names in category_groups:
        parent = await Category.create(
            name=parent_name,
            user_id=user_id,
            db=connection,
            type=category_type,
        )
        for child_name in child_names:
            await Category.create(
                name=child_name,
                user_id=user_id,
                db=connection,
                type=category_type,
                parent_id=parent.id,
            )


@sub.subscribe
async def create_default_categories(message: UserCreated):
    logger.info(f"Creating default categories for user {message.user_id}")
    expense_categories = (
        (
            "Home",
            [
                "Mortgage",
                "Rent",
                "Home Insurance",
                "Rental Insurance",
                "HOA Dues",
                "Home Supplies",
                "Home Maintenance",
                "Flood Insurance",
                "Furnishings",
            ],
        ),
        (
            "Auto",
            [
                "Car Payment",
                "Car Insurance",
                "Car Maintenance",
                "Gas & Fuel",
                "Car Wash",
                "Toll",
                "Inspection & Registration",
                "Public Transportation",
                "Rideshare",
                "Parking",
            ],
        ),
        (
            "Food",
            [
                "Groceries",
                "Restaurants",
                "Fast Food",
                "Coffee Shop",
            ],
        ),
        (
            "Education",
            [
                "Tuition",
                "Student Loan",
                "Books & Supplies",
            ],
        ),
        # Cash & ATM
        ("Cash & ATM", []),
        # Charity
        ("Charity & Donations", []),
        # Entertainment
        (
            "Entertainment",
            [
                "Movies",
                "Family Night",
                "Date Night",
            ],
        ),
        # Financial
        (
            "Financial",
            [
                "Life Insurance",
                "Retirement Savings",
                "Investments",
            ],
        ),
        # Fitness
        (
            "Fitness",
            [
                "Gym Membership",
                "Personal Training",
            ],
        ),
        # Health
        (
            "Health",
            [
                "Suppliments",
                "Doctor",
                "Dentist",
                "Health Insurance",
                "Health Share",
                "Eyecare",
                "Pharmacy",
            ],
        ),
        # Gifts
        ("Gifts", []),
        # Kids
        (
            "Kids",
            [
                "Child Care",
                "Child Clothing",
                "Babysitter",
                "Diapers",
                "Formula",
                "Toys",
            ],
        ),
        # Personal Care
        (
            "Personal Care",
            [
                "Salon",
                "Barber",
                "Spa",
                "Laundry",
            ],
        ),
        # Savings
        (
            "Savings",
            [
                "Emergency Fund",
                "Vacation Fund",
                "Car Fund",
            ],
        ),
        # Pets
        (
            "Pets",
            [
                "Veterinary",
                "Pet Food",
                "Pet Grooming",
                "Pet Boarding",
            ],
        ),
        # Shopping
        (
            "Shopping",
            [
                "Electronics",
                "Clothing",
                "Books",
            ],
        ),
        # Travel
        (
            "Travel",
            [
                "Airfare",
                "Rental Cars",
                "Hotels",
            ],
        ),
        # Utilities
        (
            "Utilities",
            [
                "Electricity",
                "Water",
                "Gas",
                "Internet & Cable",
                "Phone",
                "Trash",
            ],
        ),
    )
    income_categories = [
        (
            "Income",
            [
                "Paycheck",
                "Bonus",
                "Tax Refund",
                "Earned Interest",
                "Dividends",
                "Rental Income",
            ],
        ),
    ]

    async with db.pool.acquire() as connection:
        async with connection.transaction():
            await create_category_tree(
                connection,
                message.user_id,
                CategoryType.expense,
                expense_categories,
            )
            await create_category_tree(
                connection,
                message.user_id,
                CategoryType.income,
                income_categories,
            )
