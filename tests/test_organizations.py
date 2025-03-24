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
