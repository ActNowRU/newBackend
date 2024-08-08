from datetime import datetime, timedelta

import bcrypt
import jwt

from settings import (SECRET_KEY, TOKEN_EXPIRE_TIME)


def hash_password(password) -> bytes:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())


def validate_password(self, password) -> bool:
    return bcrypt.checkpw(password.encode(), self.hashed_password)


def generate_token(self) -> dict:
    token = jwt.encode(
        {"user_name": self.user_name, "id": self.id,
         "exp": datetime.utcnow() + timedelta(seconds=int(TOKEN_EXPIRE_TIME))},
        SECRET_KEY
    )

    return {"token": token}
