import pytest


@pytest.mark.asyncio
async def test_goals_create(client):
    response = await client.post("/goals/")
    assert response.status_code == 401
