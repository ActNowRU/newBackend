import pytest
import random
import string


def random_string(length=10):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


@pytest.mark.asyncio
async def test_search_places(client, access_data):
    # Create several organizations
    for i in range(3):
        org_data = {
            "name": f"Test Org {i}",
            "email": f"test_org_{i}@example.com",
            "organization_type": "кафе",
            "password": "Test123$",
            "inn_or_ogrn": f"{random.randint(1000000000, 9999999999)}",
            "legal_address": f"Address {i}",
        }
        response = await client.post("/organization/register", data=org_data)
        assert response.status_code == 201, response.json()

        # Log in to the organization
        login_response = await client.post(
            "/auth/login",
            data={"login": org_data["email"], "password": org_data["password"]},
        )
        assert login_response.status_code == 200, login_response.json()
        org_access_data = login_response.json()

        # Create random goals
        for j in range(5):
            goal_data = {
                "title": f"Goal {j} for Org {i}",
                "description": random_string(),
                "address": f"Address {i}-{j}",
                "cost": random.randint(100, 1000),
                "from_time": "10:00:00",
                "to_time": "12:00:00",
                "dates": ["2023-10-01", "2023-10-02"],
            }
            response = await client.post(
                "/goals/",
                data=goal_data,
                files={"content": random_string().encode()},
                headers={"Authorization": f"Bearer {org_access_data['access_token']}"},
            )
            assert response.status_code == 201, response.json()

    # Test search endpoint
    response = await client.get("/search/places", params={"organization_type": "кафе"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0
