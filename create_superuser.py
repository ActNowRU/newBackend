import asyncio

from app.models.user import Role, User
from app.database_initializer import get_db


async def create_superuser():
    username = input("Enter username for admin: ")
    password = input("Enter password for admin: ")

    session = await get_db()

    await User.create(
        session=session(),
        user_schema={
            "username": username,
            "password": password,
        },
        role=Role.admin,
    )


if __name__ == "__main__":
    asyncio.run(create_superuser())
