if __name__ == "__main__":
    from app.database.models.user import Role
    from app.database import create_user
    from app.database_initializer import get_db

    username = input("Enter username for admin: ")
    password = input("Enter password for admin: ")

    session = get_db()

    create_user(
        session=session,
        user={
            "username": username,
            "password": password,
        },
        role=Role.admin,
    )
