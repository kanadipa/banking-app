from __future__ import annotations

from tests.conftest import C1, HEADERS


async def test_list_customers(client):
    r = await client.get("/customers", headers=HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 4
    assert len(body["items"]) == 4
    assert body["page"] == 1


async def test_list_customers_pagination(client):
    r = await client.get("/customers?page=1&max_size=2", headers=HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert len(body["items"]) == 2
    assert body["total"] == 4
    assert body["total_pages"] == 2


async def test_get_customer_detail(client):
    r = await client.get(f"/customers/{C1}", headers=HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == C1
    assert body["name"] == "Arisha Barron"
    assert isinstance(body["accounts"], list)


async def test_get_customer_with_account(client):
    await client.post(f"/customers/{C1}/accounts", headers=HEADERS, json={"initial_deposit": "500.00"})
    r = await client.get(f"/customers/{C1}", headers=HEADERS)
    body = r.json()
    assert len(body["accounts"]) == 1
    assert body["accounts"][0]["balance"] == "500.00"
    assert body["accounts"][0]["currency"] == "EUR"


async def test_get_customer_not_found(client):
    r = await client.get("/customers/9999", headers=HEADERS)
    assert r.status_code == 404
    assert r.json()["error"] == "not_found"


async def test_customers_require_auth(client):
    r = await client.get("/customers")
    assert r.status_code == 401
    assert r.json()["error"] == "unauthorized"
