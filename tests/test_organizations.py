import pytest
import random


EXPECTED_DATA_FOR_GET_PLACE = [
    {
        "id": 1,
        "organization_id": 1,
        "name": "Test Place",
        "address": "Gorbunova Street, 14, Moscow, 121596",
        "location": {"lon": 55.725934, "lat": 37.374102},
    }
]


@pytest.mark.asyncio
async def test_organization_auth(client):
    types_response = await client.get("/organization/types/available")
    assert types_response.status_code == 200, types_response.json()
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
    assert register_response.status_code == 201, register_response.json()

    login_response = await client.post(
        "/auth/login",
        data={"login": "test@test.com", "password": "Test123$"},
    )

    assert login_response.status_code == 200, login_response.json()

    login_response_json = login_response.json()

    assert login_response_json.get("access_token")
    assert login_response_json.get("refresh_token")

    auth_response = await client.get(
        "/organization/us",
        headers={"Authorization": f"Bearer {login_response_json['access_token']}"},
    )
    assert auth_response.status_code == 200, auth_response.json()


@pytest.mark.asyncio
async def test_places(client, access_data):
    response = await client.get("/organization/places/")
    assert response.status_code == 200, response.json()
    assert response.json() == [], response.json()

    set_response = await client.put(
        "/organization/places/",
        data={"name": "Test Place", "address": "Gorbunova Street, 14, Moscow, 121596"},
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )

    assert set_response.status_code == 200, set_response.json()

    places_response = await client.get("/organization/places/")
    assert (
        places_response.json() == EXPECTED_DATA_FOR_GET_PLACE
    ), f"Response: {places_response.json()}, expected: {EXPECTED_DATA_FOR_GET_PLACE}"

    get_counter_response = await client.get(
        "/organization/places/tests/caching_geopoint",
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )
    assert get_counter_response.status_code == 200, get_counter_response.json()

    counter = get_counter_response.json()["counter"]

    places_response = await client.get("/organization/places/")
    assert (
        places_response.json() == EXPECTED_DATA_FOR_GET_PLACE
    ), f"Response: {places_response.json()}, expected: {EXPECTED_DATA_FOR_GET_PLACE}"

    get_counter_response = await client.get(
        "/organization/places/tests/caching_geopoint",
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )

    assert (
        get_counter_response.status_code == 200
    ), f"Status code: {get_counter_response.status_code}, expected: 200"
    assert (
        get_counter_response.json()["counter"] != counter + 1
    ), f"Counter is: {get_counter_response.json()}, expected: {counter + 1}"
