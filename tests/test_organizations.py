import pytest
import random
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_organization_auth(client: AsyncClient):
    types_response = await client.get("/organization/types/available")
    assert types_response.status_code == 200
    types = types_response.json()
    register_response = await client.post(
        "/organization/register",
        data={
            "name": "Test Org",
            "email": "test@test.com",
            "organization_type": random.choice(types),
            "password": "Test123$",
            "inn_or_ogrn": "1234567890",
            "legal_address": "Gorbunova Street, 14, Moscow, 121596",
        },
    )
    assert register_response.status_code == 201

    login_response = await client.post(
        "/auth/login",
        data={"login": "test@test.com", "password": "Test123$"},
    )

    assert login_response.status_code == 200

    login_response_json = login_response.json()

    assert login_response_json.get("access_token")
    assert login_response_json.get("refresh_token")

    auth_response = await client.get(
        "/organization/us",
        headers={"Authorization": f"Bearer {login_response_json['access_token']}"},
    )
    assert auth_response.status_code == 200


@pytest.mark.asyncio
async def test_places(client, access_data):
    response = await client.get("/organization/places/")
    assert response.status_code == 200
    assert response.json() == []

    set_response = await client.put(
        "/organization/places/",
        data={"name": "Test Place", "address": "Gorbunova Street, 14, Moscow, 121596"},
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )

    assert set_response.status_code == 200

    response = await client.get("/organization/places/")
    assert response.json() == [
        {
            "id": 1,
            "organization_id": 1,
            "name": "Test Place",
            "address": "Gorbunova Street, 14, Moscow, 121596",
            "location": {"lon": 55.725934, "lat": 37.374102},
        }
    ]

    get_counter_response = await client.get(
        "/organization/places/tests/caching_geopoint",
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )
    assert get_counter_response.status_code == 200

    counter = get_counter_response.json()["counter"]

    response = await client.get("/organization/places/")
    assert response.json() == [
        {
            "id": 1,
            "organization_id": 1,
            "name": "Test Place",
            "address": "Gorbunova Street, 14, Moscow, 121596",
            "location": {"lon": 55.725934, "lat": 37.374102},
        }
    ]

    get_counter_response = await client.get(
        "/organization/places/tests/caching_geopoint",
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )

    assert get_counter_response.status_code == 200
    assert get_counter_response.json()["counter"] != counter + 1
