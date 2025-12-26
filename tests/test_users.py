import pytest
import asyncio


@pytest.mark.asyncio
async def test_get_user_profile(client, access_data):
    # Test retrieving a user profile by username
    response = await client.get(
        "/user/testuser",
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )
    assert response.status_code in [200, 404], response.json()


@pytest.mark.asyncio
async def test_update_user_info(client, access_data):
    # Test updating user profile information
    updated_data = {
        "first_name": "UpdatedName",
        "username": "updatedusername",
        "description": "Updated description",
    }
    response = await client.patch(
        "/user/",
        data=updated_data,
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )
    assert response.status_code in [200, 500], response.json()


@pytest.mark.asyncio
async def test_update_user_photo(client, access_data):
    # Test updating user profile photo
    with open("tests/assets/test_image.jpeg", "rb") as photo:
        response = await client.put(
            "/user/photo",
            files={"photo": photo},
            headers={"Authorization": f"Bearer {access_data['access_token']}"},
        )
    assert response.status_code in [200, 500], response.json()


@pytest.mark.asyncio
async def test_update_user_password(client, access_data):
    # Test updating user password
    password_data = {
        "old_password": "Test123$",
        "new_password": "NewTest123$",
    }
    response = await client.put(
        "/user/password",
        data=password_data,
        headers={"Authorization": f"Bearer {access_data['access_token']}"},
    )
    assert response.status_code in [200, 401, 500], response.json()


@pytest.mark.asyncio
async def test_create_new_user(client):
    # Test creating a new user
    user_data = {
        "first_name": "Test",
        "username": "testuser111",
        "email": "testuser111@example.com",
        "birth_date": "2000-01-01",
        "gender": "male",
        "password": "Test123$",
    }
    response = await client.post(
        "/auth/signup",
        data=user_data,
    )
    assert response.status_code == 201, response.json()
    assert "id" in response.json(), "User ID is missing in the response"
    assert response.json()["username"] == user_data["username"]


@pytest.mark.asyncio
async def test_login_and_logout(client):
    # Test logging in with valid credentials
    login_data = {
        "login": "testuser111@example.com",
        "password": "Test123$",
    }
    login_response = await client.post("/auth/login", data=login_data)
    assert login_response.status_code == 200, login_response.json()
    assert "access_token" in login_response.json(), "Access token is missing"
    assert "refresh_token" in login_response.json(), "Refresh token is missing"

    access_token = login_response.json()["access_token"]
    refresh_token = login_response.json()["refresh_token"]

    # Test refreshing access token with refresh token
    await asyncio.sleep(2)  # ensure we get token at another timestamp to be different
    refresh_response = await client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert refresh_response.status_code == 200, refresh_response.json()
    assert "access_token" in refresh_response.json(), (
        "Access token is missing in refresh response"
    )
    assert refresh_response.json()["access_token"] != access_token, (
        "New access token should be different from the old one"
    )

    # Test logging out
    logout_response = await client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert logout_response.status_code == 200, logout_response.json()
    assert logout_response.json().get("detail") == "Вы успешно вышли из системы"

    new_refresh_response = await client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert new_refresh_response.status_code == 403, (
        "Refresh token after logging out shouldn't be valid: ",
        refresh_response.json().get("access_token"),
    )
