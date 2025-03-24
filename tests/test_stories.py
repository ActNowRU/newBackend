import pytest


@pytest.mark.asyncio
async def test_create_story(client, access_data):
    # Test creating a story without required fields
    response = await client.post(
        "/stories/",
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )
    assert response.status_code == 422, response.json()

    # Test creating a valid story
    response = await client.post(
        "/stories/",
        data={
            "description": "Test Story",
            "is_recommending": True,
            "organization_id": 1,
        },
        files={"content": open("tests/assets/test_image.jpeg", "rb").read()},
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )
    assert response.status_code == 201, response.json()


@pytest.mark.asyncio
async def test_admin_change_story_moderation_state(client, access_data_admin):
    # Test changing the moderation state of a story to make it visible
    moderation_data = {
        "moderation_state": "allowed",
    }
    response = await client.patch(
        "/stories/admin/1",
        params=moderation_data,
        headers={"Authorization": f"Bearer {access_data_admin['access_token']}"},
    )
    assert response.status_code == 200, response.json()


@pytest.mark.asyncio
async def test_get_favorite_stories(client, access_data):
    # Test retrieving favorite stories for the current user
    response = await client.get(
        "/stories/favorite/1",
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )
    assert response.status_code == 200, response.json()
    assert isinstance(response.json(), dict)


@pytest.mark.asyncio
async def test_set_favorite_story_position(client, access_data):
    # Test setting the position of a favorite story
    response = await client.put(
        "/stories/favorite",
        params={"story_id": 1, "position": 1},
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )
    assert response.status_code == 200, response.json()

    # Verify the position is updated
    response = await client.get(
        "/stories/favorite/1",
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )
    assert response.status_code == 200, response.json()
    favorites = response.json()
    assert favorites.get(str(1), None), response.json()


@pytest.mark.asyncio
async def test_get_story_by_id(client, access_data):
    # Test retrieving a story by ID
    response = await client.get(
        "/stories/1", headers={"Authorization": f"Bearer {access_data['access_token']}"}
    )
    assert response.status_code == 200, response.json()
    assert "id" in response.json()


@pytest.mark.asyncio
async def test_get_all_organization_stories(client, access_data):
    # Test retrieving all stories for an organization
    response = await client.get(
        "/stories/organization/1",
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )
    assert response.status_code == 200, response.json()
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_user_stories(client, access_data):
    # Test retrieving stories for a specific user
    response = await client.get(
        "/stories/user/admin1",
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )
    assert response.status_code == 200, response.json()
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_current_user_stories(client, access_data):
    # Test retrieving stories for the current user
    response = await client.get(
        "/stories/me",
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )
    assert response.status_code == 200, response.json()
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_update_story(client, access_data):
    # Test updating a story
    updated_data = {
        "description": "Updated Story",
        "is_recommending": False,
    }
    response = await client.patch(
        "/stories/1",
        data=updated_data,
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )
    assert response.status_code == 200, response.json()


@pytest.mark.asyncio
async def test_delete_story(client, access_data):
    # Test deleting a story
    response = await client.delete(
        "/stories/1", headers={"Authorization": f"Bearer {access_data['access_token']}"}
    )
    assert response.status_code == 200, response.json()

    # Verify the story is deleted
    response = await client.get(
        "/stories/1", headers={"Authorization": f"Bearer {access_data['access_token']}"}
    )
    assert response.status_code == 404, response.json()
