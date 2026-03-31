from __future__ import annotations

from tests.conftest import C1, HEADERS


async def test_create_account_and_balance(client):
    r = await client.post(f"/customers/{C1}/accounts", headers=HEADERS, json={"initial_deposit": "1250.00"})
    assert r.status_code == 201
    account = r.json()
    assert account["customer_id"] == C1
    assert account["balance"] == "1250.00"
    assert account["currency"] == "EUR"
    assert account["id"] == 1

    balance = await client.get(f"/accounts/{account['id']}/balance", headers=HEADERS)
    assert balance.status_code == 200
    b = balance.json()
    assert b["balance"] == "1250.00"
    assert b["customer_id"] == C1


async def test_create_account_rejects_zero_deposit(client):
    r = await client.post(f"/customers/{C1}/accounts", headers=HEADERS, json={"initial_deposit": "0.00"})
    assert r.status_code == 422


async def test_create_account_rejects_missing_requested_by(client):
    r = await client.post(f"/customers/{C1}/accounts", headers={"X-API-Key": "test-key"}, json={"initial_deposit": "100.00"})
    assert r.status_code == 400
    assert "X-Requested-By" in r.json()["detail"]


async def test_create_account_unknown_customer(client):
    r = await client.post(
        "/customers/9999/accounts",
        headers=HEADERS,
        json={"initial_deposit": "100.00"},
    )
    assert r.status_code == 404


async def test_balance_not_found(client):
    r = await client.get("/accounts/9999/balance", headers=HEADERS)
    assert r.status_code == 404
