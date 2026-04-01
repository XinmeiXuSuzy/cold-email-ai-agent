"""
Smoke tests for the prospects API endpoints.
"""
import pytest


@pytest.mark.asyncio
async def test_health(client):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_create_prospect(client):
    res = await client.post(
        "/prospects",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "role": "CTO",
            "company": "TestCo",
            "industry": "SaaS",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "test@example.com"
    assert data["outreach_status"] == "new"
    return data["id"]


@pytest.mark.asyncio
async def test_duplicate_email_rejected(client):
    await client.post(
        "/prospects",
        json={"name": "Dup User", "email": "dup@example.com"},
    )
    res = await client.post(
        "/prospects",
        json={"name": "Dup User 2", "email": "dup@example.com"},
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_list_prospects(client):
    res = await client.get("/prospects")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_prospect(client):
    create_res = await client.post(
        "/prospects",
        json={"name": "Get Test", "email": "gettest@example.com"},
    )
    pid = create_res.json()["id"]

    res = await client.get(f"/prospects/{pid}")
    assert res.status_code == 200
    assert res.json()["id"] == pid


@pytest.mark.asyncio
async def test_update_prospect(client):
    create_res = await client.post(
        "/prospects",
        json={"name": "Update Test", "email": "updatetest@example.com"},
    )
    pid = create_res.json()["id"]

    res = await client.patch(
        f"/prospects/{pid}",
        json={"company": "NewCo", "outreach_status": "researched"},
    )
    assert res.status_code == 200
    assert res.json()["company"] == "NewCo"
    assert res.json()["outreach_status"] == "researched"


@pytest.mark.asyncio
async def test_delete_prospect(client):
    create_res = await client.post(
        "/prospects",
        json={"name": "Delete Test", "email": "deletetest@example.com"},
    )
    pid = create_res.json()["id"]

    res = await client.delete(f"/prospects/{pid}")
    assert res.status_code == 204

    res = await client.get(f"/prospects/{pid}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_search_prospects(client):
    await client.post(
        "/prospects",
        json={"name": "Searchable Person", "email": "searchable@example.com", "company": "UniqueCompanyXYZ"},
    )

    res = await client.get("/prospects?search=UniqueCompanyXYZ")
    assert res.status_code == 200
    assert res.json()["total"] >= 1


@pytest.mark.asyncio
async def test_analytics(client):
    res = await client.get("/analytics")
    assert res.status_code == 200
    data = res.json()
    assert "total_prospects" in data
    assert "reply_rate" in data
