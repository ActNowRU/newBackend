import pytest


@pytest.mark.asyncio
async def test_goals_create(client, access_data):
    response = await client.post(
        "/goals/", headers={"Authorization": f"Bearer {access_data['access_token']}"}
    )
    assert response.status_code == 422, response.json()

    response = await client.post(
        "/goals/",
        data={
            "title": "Test Goal",
            "description": "Test Description",
            "address": "Gorbunova Street, 14, Moscow, 121596",
            "cost": 1000,
            "from_time": "12:00:00",
            "to_time": "13:00:00",
            "dates": ["2017-02-02", "2017-03-02"],
        },
        files={"content": open("tests/assets/test_image.jpeg", "rb").read()},
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )

    assert response.status_code == 201, response.json()


@pytest.mark.asyncio
async def test_get_all_goals(client, access_data):
    response = await client.get(
        "/goals/", headers={"Authorization": f"Bearer {access_data['access_token']}"}
    )
    assert response.status_code == 200, response.json()
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_goal_by_id(client, access_data):
    response = await client.get(
        "/goals/1", headers={"Authorization": f"Bearer {access_data['access_token']}"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_goal(client, access_data):
    updated_data = {
        "title": "Updated Goal",
        "description": "Updated Description",
        "address": "Updated Address",
        "cost": 2000,
        "from_time": "14:00:00",
        "to_time": "15:00:00",
        "dates": ["2017-04-02", "2017-05-02"],
    }
    response = await client.patch(
        "/goals/1",
        data=updated_data,
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )
    assert response.status_code == 200, response.json()


@pytest.mark.asyncio
async def test_delete_goal(client, access_data):
    response = await client.delete(
        "/goals/1", headers={"Authorization": f"Bearer {access_data['access_token']}"}
    )
    assert response.status_code == 204

    # Verify the goal is deleted
    response = await client.get(
        "/goals/1", headers={"Authorization": f"Bearer {access_data['access_token']}"}
    )
    assert response.status_code == 404, response.json()
