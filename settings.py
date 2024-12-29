import os
import secrets

from dotenv import load_dotenv
from fastapi import HTTPException, status


def generate_secret_key(length=32) -> str:
    # Generate a secret key of length 32
    return secrets.token_urlsafe(length)


# Load environment variables from .env file
load_dotenv()

# =========================================================================================================
# General settings

# Check if SECRET_KEY is None and generate a new key if needed
if not os.getenv("SECRET_KEY"):
    new_secret_key = generate_secret_key()
    try:
        # Read the existing content of the .env file
        with open(".env", "r") as f:
            file_content = f.read()

        if "SECRET_KEY=" in file_content:
            # Update the SECRET_KEY value in the file content
            updated_content = file_content.replace(
                "SECRET_KEY=",
                "SECRET_KEY=" + new_secret_key,
            )
        else:
            # Append the new key to the file content
            updated_content = file_content + "\nSECRET_KEY=" + new_secret_key
        # Write the updated content back to the .env file
        with open(".env", "w") as f:
            f.write(updated_content)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=".env file not found",
        )

SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = True

# =========================================================================================================
# JWT settings

ACCESS_TOKEN_EXPIRE_TIME = 60 * 60  # 1 hour
REFRESH_TOKEN_EXPIRE_TIME = 60 * 60 * 24 * 30  # 30 days

# =========================================================================================================
# Redis settings

REDIS_LOGOUT_VALUE = "logged_out"
REDIS_HOST = "redis://localhost:6379"

# =========================================================================================================
# Database settings

if DEBUG:
    SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///test.sqlite3"
else:
    SQLALCHEMY_DATABASE_URL = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    )

# =========================================================================================================
# External services settings
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
