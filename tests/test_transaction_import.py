from datetime import date
from unittest.mock import AsyncMock

import httpx
import pytest

from everwealth.transactions import Transaction
from everwealth.transactions.csv_import import parse_transactions, transaction_direction


UFCU_SAMPLE = (
    "\ufeffAccount name,Amount,Credit/debit indicator,Book date,Description,Category\r\n"
    "CHECKING,140.15,Debit,10/30/2026,Insurance,Financial\r\n"
    "CHECKING,5574.30,Credit,10/30/2026,Payroll,Income\r\n"
).encode("utf-8")
MAPPING = {
    "date": "Book date",
    "description": "Description",
    "amount": "Amount",
    "direction": "Credit/debit indicator",
}


def test_ufcu_mapping_with_unsigned_amounts():
    transactions = parse_transactions(UFCU_SAMPLE, MAPPING, "user", "checking")
    assert [item.amount for item in transactions] == [-14015, 557430]
    assert transactions[0].date == date(2026, 10, 30)
    assert transactions[0].description == "Insurance"
    assert transactions[0].account_id == "checking"


@pytest.mark.parametrize(
    "value", ["CREDIT", "Direct Deposit", "ACH credit", "refund", "Income", "CR"]
)
def test_incoming_direction(value):
    assert transaction_direction(value) == 1


@pytest.mark.parametrize("value", ["Debit", "Withdrawal", "ACH payment", "expense", "DR"])
def test_outgoing_direction(value):
    assert transaction_direction(value) == -1


@pytest.mark.parametrize("value", ["", "transfer", "Credit / Debit Card", "notcredit"])
def test_unknown_or_ambiguous_direction(value):
    with pytest.raises(ValueError, match="credit/debit"):
        transaction_direction(value)


def test_template_retains_signs_and_handles_quoted_fields():
    content = (
        b'Date,Description,Amount\n2026-10-30,"Store, Inc.","-$1,234.56"\n2026-10-30,Pay,500\n'
    )
    transactions = parse_transactions(content, {}, "user", "checking")
    assert [item.amount for item in transactions] == [-123456, 50000]
    assert transactions[0].description == "Store, Inc."


def test_direction_overrides_original_amount_sign():
    transactions = parse_transactions(
        UFCU_SAMPLE.replace(b"5574.30", b"-5574.30"), MAPPING, "user", "checking"
    )
    assert transactions[1].amount == 557430


@pytest.mark.parametrize(
    "content, mapping, message",
    [
        (b"Date,Description,Amount\n", {}, "no transactions"),
        (b"Date,Date,Amount\n", {}, "unique"),
        (b"\xff", {}, "UTF-8"),
        (b"", {}, "header row"),
        (UFCU_SAMPLE, {**MAPPING, "date": "Missing"}, "missing"),
        (UFCU_SAMPLE, {**MAPPING, "date": "Amount"}, "different"),
        (UFCU_SAMPLE.replace(b"Debit", b"Transfer"), MAPPING, "row 2"),
        (UFCU_SAMPLE.replace(b"140.15", b"NaN"), MAPPING, "row 2"),
        (UFCU_SAMPLE.replace(b"140.15", b"12.345"), MAPPING, "row 2"),
        (UFCU_SAMPLE.replace(b"10/30/2026", b"invalid"), MAPPING, "row 2"),
        (b"Date,Description,Amount\n2026-10-30,Missing amount\n", {}, "row 2"),
    ],
)
def test_invalid_imports(content, mapping, message):
    with pytest.raises(ValueError, match=message):
        parse_transactions(content, mapping, "user", "checking")


@pytest.mark.asyncio
async def test_header_discovery_suggests_ufcu_mapping(ui_app):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=ui_app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/transactions/upload/headers", files={"file": ("bank.csv", UFCU_SAMPLE, "text/csv")}
        )
    assert response.status_code == 200
    assert response.json()["mapping"] == MAPPING
    assert response.json()["headers"][0] == "Account name"


@pytest.mark.asyncio
async def test_mapped_upload_and_invalid_row_do_not_partially_save(ui_app, monkeypatch):
    create = AsyncMock()
    monkeypatch.setattr(Transaction, "create_many", create)
    data = {"account": "checking", **{f"{key}_column": value for key, value in MAPPING.items()}}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=ui_app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/transactions/upload", data=data, files={"file": ("bank.csv", UFCU_SAMPLE)}
        )
        assert response.status_code == 303
        assert [item.amount for item in create.call_args.args[0]] == [-14015, 557430]
        create.reset_mock()
        response = await client.post(
            "/transactions/upload",
            data=data,
            files={"file": ("bank.csv", UFCU_SAMPLE.replace(b"Credit,", b"Transfer,"))},
        )
        assert response.status_code == 400
        assert "row 3" in response.json()["detail"]
        create.assert_not_awaited()


@pytest.mark.asyncio
async def test_upload_rejects_another_users_account(ui_app, monkeypatch):
    from everwealth.db import get_connection

    connection = AsyncMock()
    connection.fetchval.return_value = False

    async def override():
        yield connection

    ui_app.dependency_overrides[get_connection] = override
    create = AsyncMock()
    monkeypatch.setattr(Transaction, "create_many", create)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=ui_app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/transactions/upload",
            data={"account": "someone-else"},
            files={"file": ("bank.csv", UFCU_SAMPLE)},
        )
    assert response.status_code == 400
    create.assert_not_awaited()
