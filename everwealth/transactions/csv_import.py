"""CSV header discovery and transaction normalization, shared by both upload steps."""

import csv
import re
from decimal import Decimal, InvalidOperation
from io import StringIO

from dateutil import parser

from everwealth.transactions import Transaction


HEADER_ALIASES = {
    "date": ("date", "book date", "transaction date", "posting date", "posted date"),
    "description": ("description", "memo", "payee", "merchant", "transaction description"),
    "amount": ("amount", "transaction amount", "value"),
    "direction": (
        "credit/debit indicator",
        "credit debit",
        "debit credit",
        "direction",
        "transaction group",
        "transaction type",
        "type",
    ),
}
INCOMING = {
    "credit",
    "credits",
    "cr",
    "deposit",
    "deposits",
    "incoming",
    "income",
    "refund",
    "refunds",
    "inflow",
}
OUTGOING = {
    "debit",
    "debits",
    "dr",
    "withdrawal",
    "withdrawals",
    "withdraw",
    "outgoing",
    "expense",
    "expenses",
    "payment",
    "payments",
    "outflow",
}


def csv_reader(content: bytes) -> csv.DictReader:
    try:
        reader = csv.DictReader(StringIO(content.decode("utf-8-sig")), strict=True)
        headers = reader.fieldnames
    except (UnicodeDecodeError, csv.Error) as error:
        raise ValueError("Please choose a valid UTF-8 CSV file.") from error
    if not headers or any(not name.strip() for name in headers):
        raise ValueError("CSV needs a header row with non-empty column names.")
    if len(set(headers)) != len(headers):
        raise ValueError("CSV column names must be unique.")
    return reader


def suggest_mapping(headers: list[str]) -> dict[str, str]:
    normalized = {re.sub(r"[^a-z0-9]+", " ", name.lower()).strip(): name for name in headers}
    return {
        field: next(
            (
                normalized[key]
                for alias in aliases
                if (key := re.sub(r"[^a-z0-9]+", " ", alias).strip()) in normalized
            ),
            "",
        )
        for field, aliases in HEADER_ALIASES.items()
    }


def transaction_direction(value: str) -> int:
    words = set(re.findall(r"[a-z]+", value.casefold()))
    incoming, outgoing = bool(words & INCOMING), bool(words & OUTGOING)
    if incoming == outgoing:
        raise ValueError("unrecognized or ambiguous credit/debit value")
    return 1 if incoming else -1


def parse_transactions(
    content: bytes, mapping: dict[str, str | None], user_id: str, account_id: str
) -> list[Transaction]:
    reader = csv_reader(content)
    # Keep existing template uploads working when no explicit mapping was sent.
    defaults = {name.strip().lower(): name for name in reader.fieldnames}
    columns = {
        field: mapping.get(field) if mapping.get(field) is not None else defaults.get(field)
        for field in ("date", "description", "amount")
    }
    columns["direction"] = mapping.get("direction") or None
    selected = [name for name in columns.values() if name]
    if any(not columns[field] for field in ("date", "description", "amount")):
        raise ValueError("Select columns for Date, Description, and Amount.")
    if any(name not in reader.fieldnames for name in selected):
        raise ValueError("A selected column is missing from this CSV. Please check the mapping.")
    if len(set(selected)) != len(selected):
        raise ValueError("Choose a different CSV column for each mapped field.")

    transactions = []
    try:
        for row in reader:
            row_number = reader.line_num
            try:
                if None in row or any(value is None for value in row.values()):
                    raise ValueError("column count does not match the header")
                raw_amount = row[columns["amount"]].strip().replace(",", "").replace("$", "")
                if raw_amount.startswith("(") and raw_amount.endswith(")"):
                    raw_amount = "-" + raw_amount[1:-1]
                amount = Decimal(raw_amount) * 100
                if not amount.is_finite() or amount != amount.to_integral_value():
                    raise ValueError(
                        "amount must be a finite number with at most two decimal places"
                    )
                amount = int(amount)
                if columns["direction"]:
                    amount = abs(amount) * transaction_direction(row[columns["direction"]])
                trans_date = parser.parse(row[columns["date"]]).date()
                description = row[columns["description"]].strip()
                if not description:
                    raise ValueError("description is empty")
            except (InvalidOperation, ValueError, TypeError, OverflowError) as error:
                raise ValueError(f"Invalid CSV row {row_number}: {error}") from error
            transactions.append(
                Transaction(
                    user_id=user_id,
                    account_id=account_id,
                    description=description,
                    amount=amount,
                    date=trans_date,
                )
            )
    except csv.Error as error:
        raise ValueError(f"Invalid CSV near row {reader.line_num}: {error}") from error
    if not transactions:
        raise ValueError("CSV contains no transactions.")
    return transactions
