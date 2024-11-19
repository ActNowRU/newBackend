from httpx import AsyncClient


async def get_vk_auth_url(client_id, redirect_url):
    async with AsyncClient() as client:
        response = await client.get(
            f"https://oauth.vk.com/authorize?client_id={client_id}"
            f"&display=page&redirect_url={redirect_url}&response_type=code&v=5.52"
        )

    return await response.json()


async def get_vk_access_token(client_id, client_secret, redirect_url, code):
    async with AsyncClient() as client:
        response = await client.get(
            f"https://oauth.vk.com/access_token?client_id={client_id}&client_secret={client_secret}"
            f"&redirect_uri ={redirect_url}&code={code}"
        )

    return await response.json()
