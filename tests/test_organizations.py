import pytest


@pytest.mark.asyncio
async def test_update_organization(client, access_data):
    # Test updating organization with valid data
    updated_data = {
        "name": "Updated Org",
        "description": "Updated Description",
        "legal_address": "Updated Address",
        "common_discount": 5.0,
        "max_discount": 20.0,
        "step_amount": 2,
        "days_to_step_back": 7,
    }
    response = await client.patch(
        "/organization/",
        data=updated_data,
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )

    assert response.status_code == 200, response.json()


@pytest.mark.asyncio
async def test_get_current_organization(client, access_data):
    # Test retrieving the current organization info
    response = await client.get(
        "/organization/us",
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )
    assert response.status_code == 200, response.json()
    assert "id" in response.json(), "Organization ID is missing in the response"
    assert "name" in response.json(), "Organization name is missing in the response"


@pytest.mark.asyncio
async def test_get_organization_by_id(client, access_data):
    # Test retrieving organization info by ID
    response = await client.get(
        "/organization/1",
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )
    assert response.status_code in [200, 404], response.json()
    if response.status_code == 200:
        assert "id" in response.json(), "Organization ID is missing in the response"
        assert "name" in response.json(), "Organization name is missing in the response"


@pytest.mark.asyncio
async def test_update_organization_photo(client, access_data):
    # Test updating organization photo
    with open("tests/assets/test_image.jpeg", "rb") as photo:
        response = await client.put(
            "/organization/photo",
            files={"photo": photo},
            headers={"Authorization": f"Bearer {access_data['access_token']}"},
        )
    assert response.status_code == 200, response.json()
    assert response.json().get("detail") == "Фото организации успешно обновлено"
