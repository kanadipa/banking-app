from __future__ import annotations

import asyncio

from tests.conftest import C1, C2, C3, HEADERS


async def _make_account(client, customer_id: str, amount: str = "100.00") -> str:
    r = await client.post(f"/customers/{customer_id}/accounts", headers=HEADERS, json={"initial_deposit": amount})
    assert r.status_code == 201
    return r.json()["id"]


async def test_concurrent_transfers_do_not_overdraw(client):
    src = await _make_account(client, C1, "50.00")
    dst_a = await _make_account(client, C2, "10.00")
    dst_b = await _make_account(client, C3, "10.00")

    async def do_transfer(dst):
        return await client.post("/transfers", headers=HEADERS, json={
            "from_account_id": src, "to_account_id": dst, "amount": "40.00",
        })

    r1, r2 = await asyncio.gather(do_transfer(dst_a), do_transfer(dst_b))
    statuses = sorted([r1.status_code, r2.status_code])
    assert statuses == [201, 409]

    bal = await client.get(f"/accounts/{src}/balance", headers=HEADERS)
    assert bal.json()["balance"] == "10.00"
