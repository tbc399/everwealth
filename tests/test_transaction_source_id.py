import os
import subprocess
import sys
from datetime import date

import pytest

from everwealth.transactions import Transaction


def transaction(**changes):
    return Transaction(**{
        "user_id": "user", "account_id": "account", "date": date(2026, 11, 7),
        "description": "Coffee", "amount": -450, **changes,
    })


def test_source_id_is_stable_across_processes():
    script = """
from datetime import date
from everwealth.transactions import Transaction
t = Transaction(user_id='user', account_id='account', date=date(2026, 11, 7),
                description='Coffee', amount=-450)
t.prepare_originals()
print(t.source_id)
"""
    ids = [subprocess.check_output(
        [sys.executable, "-c", script], env={**os.environ, "PYTHONHASHSEED": seed}, text=True,
    ).strip() for seed in ("1", "2")]
    current = transaction()
    current.prepare_originals()
    assert ids == [current.source_id, current.source_id]
    assert len(bytes.fromhex(current.source_id)) == 32


@pytest.mark.parametrize("changes", [
    {"user_id": "other"}, {"account_id": "other"}, {"date": date(2026, 11, 8)},
    {"description": "Other"}, {"amount": 450},
])
def test_csv_identity_includes_original_fields(changes):
    original, different = transaction(), transaction(**changes)
    original.prepare_originals()
    different.prepare_originals()
    assert original.source_id != different.source_id


def test_edits_preserve_source_id_and_original_zero_amount():
    original = transaction(amount=0)
    original.prepare_originals()
    source_id = original.source_id
    original.description = "Edited"
    original.amount = 500
    original.date = date(2026, 11, 8)
    original.prepare_originals()
    assert original.source_id == source_id
    # Recomputing from the stored originals gives the same identity.
    original.source_id = None
    original.prepare_originals()
    assert original.source_id == source_id
    assert original.orig_amount == 0


def test_plaid_identity_survives_bank_corrections():
    original = transaction(plaid_transaction_id="bank-1")
    corrected = transaction(plaid_transaction_id="bank-1", amount=-500, description="Corrected")
    separate = transaction(plaid_transaction_id="bank-2")
    csv = transaction()
    for item in (original, corrected, separate, csv):
        item.prepare_originals()
    assert original.source_id == corrected.source_id
    assert len({original.source_id, separate.source_id, csv.source_id}) == 3
