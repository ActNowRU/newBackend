import pytest


@pytest.mark.asyncio
async def test_goals_create(client, access_data):
    response = await client.post("/goals/")
    assert response.status_code == 422

    response = await client.post(
        "/goals/",
        data={
            "title": "Test Goal",
            "description": "Test Description",
            "address": "Gorbunova Street, 14, Moscow, 121596",
            "cost": 1000,
        },
        files={"content": open("tests/test_image.jpeg", "rb").read()},
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )
    assert response.status_code == 201, response.json()

    response = await client.post(
        "/goals/",
        data={
            "title": "Test Goal",
            "description": "Test Description",
            "address": "Gorbunova Street, 14, Moscow, 121596",
            "cost": 1000,
            "from_date": "2023-01-01",
            "from_time": "12:00:00",
            "to_time": "13:00:00",
            "content": open("tests/test_image.jpeg", "rb").read(),
        },
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )

    assert response.status_code == 201, response.json()
