import pytest


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
    assert places_response.json() == EXPECTED_DATA_FOR_GET_PLACE, (
        f"Response: {places_response.json()}, expected: {EXPECTED_DATA_FOR_GET_PLACE}"
    )

    get_counter_response = await client.get(
        "/organization/places/tests/caching_geopoint",
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )
    assert get_counter_response.status_code == 200, get_counter_response.json()

    counter = get_counter_response.json()["counter"]

    places_response = await client.get("/organization/places/")
    assert places_response.json() == EXPECTED_DATA_FOR_GET_PLACE, (
        f"Response: {places_response.json()}, expected: {EXPECTED_DATA_FOR_GET_PLACE}"
    )

    get_counter_response = await client.get(
        "/organization/places/tests/caching_geopoint",
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )

    assert get_counter_response.status_code == 200, (
        f"Status code: {get_counter_response.status_code}, expected: 200"
    )
    assert get_counter_response.json()["counter"] != counter + 1, (
        f"Counter is: {get_counter_response.json()}, expected: {counter + 1}"
    )
