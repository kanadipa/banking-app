from __future__ import annotations

from tests.conftest import C1, C2, HEADERS


async def _make_account(client, customer_id: str, amount: str = "100.00") -> str:
    r = await client.post(f"/customers/{customer_id}/accounts", headers=HEADERS, json={"initial_deposit": amount})
    assert r.status_code == 201
    return r.json()["id"]


async def test_transfer_happy_path(client):
    src = await _make_account(client, C1, "100.00")
    dst = await _make_account(client, C2, "10.00")

    r = await client.post("/transfers", headers=HEADERS, json={
        "from_account_id": src, "to_account_id": dst, "amount": "25.50", "reference": "rent-split",
    })
    assert r.status_code == 201
    body = r.json()
    assert body["amount"] == "25.50"
    assert body["type"] == "transfer"
    assert body["requested_by"] == "test-runner"
    assert body["balance_after"] == "74.50"
    assert body["id"] == 9

    src_bal = await client.get(f"/accounts/{src}/balance", headers=HEADERS)
    dst_bal = await client.get(f"/accounts/{dst}/balance", headers=HEADERS)
    assert src_bal.json()["balance"] == "74.50"
    assert dst_bal.json()["balance"] == "35.50"


async def test_transfer_idempotency(client):
    src = await _make_account(client, C1, "100.00")
    dst = await _make_account(client, C2, "10.00")
    payload = {"from_account_id": src, "to_account_id": dst, "amount": "20.00", "reference": "idem-test"}

    r1 = await client.post("/transfers", headers=HEADERS, json=payload)
    r2 = await client.post("/transfers", headers=HEADERS, json=payload)
    assert r1.status_code == 201
    assert r2.status_code == 409
    assert "duplicate or conflicting request." in r2.json()["detail"].lower()

    bal = await client.get(f"/accounts/{src}/balance", headers=HEADERS)
    assert bal.json()["balance"] == "80.00"


async def test_transfer_self_transfer_rejected(client):
    src = await _make_account(client, C1, "100.00")
    r = await client.post("/transfers", headers=HEADERS, json={
        "from_account_id": src, "to_account_id": src, "amount": "1.00",
    })
    assert r.status_code == 422


async def test_transfer_insufficient_funds(client):
    src = await _make_account(client, C1, "10.00")
    dst = await _make_account(client, C2, "10.00")
    r = await client.post("/transfers", headers=HEADERS, json={
        "from_account_id": src, "to_account_id": dst, "amount": "50.00",
    })
    assert r.status_code == 409
    assert "insufficient" in r.json()["detail"].lower()


async def test_transfer_missing_account(client):
    src = await _make_account(client, C1, "100.00")
    r = await client.post("/transfers", headers=HEADERS, json={
        "from_account_id": src, "to_account_id": "9999", "amount": "1.00",
    })
    assert r.status_code == 404


async def test_transfer_negative_amount(client):
    src = await _make_account(client, C1, "100.00")
    dst = await _make_account(client, C2, "10.00")
    r = await client.post("/transfers", headers=HEADERS, json={
        "from_account_id": src, "to_account_id": dst, "amount": "-1.00",
    })
    assert r.status_code == 422


async def test_transfer_requires_requested_by(client):
    src = await _make_account(client, C1, "100.00")
    dst = await _make_account(client, C2, "10.00")
    r = await client.post("/transfers", headers={"X-API-Key": "test-key"}, json={
        "from_account_id": src, "to_account_id": dst, "amount": "1.00",
    })
    assert r.status_code == 400


async def test_transfer_history(client):
    src = await _make_account(client, C1, "100.00")
    dst = await _make_account(client, C2, "10.00")

    for amt in ("1.00", "2.00", "3.00"):
        await client.post("/transfers", headers=HEADERS, json={
            "from_account_id": src, "to_account_id": dst, "amount": amt,
        })

    r = await client.get(f"/accounts/{src}/transfers?page=1&max_size=2", headers=HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 3
    assert len(body["items"]) == 2
    assert body["page"] == 1
    item = body["items"][0]
    assert item["direction"] == "outgoing"
    assert "balance_after" in item
    assert "counterparty_account_id" in item
    assert "counterparty_customer_id" in item
