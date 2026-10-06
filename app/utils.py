from datetime import datetime, timedelta

import jwt

from app.config import security_settings


def generate_access_token(data: dict, expiray: timedelta = timedelta(days=1)) -> str:
    return jwt.encode(
        payload={
            "data": data,
            "exp": datetime.now() + expiray,
        },
        algorithm=security_settings.JWT_ALGORITHM,
        key=security_settings.JWT_SECRET,
    )


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(
            jwt=token,
            key=security_settings.JWT_SECRET,
            algorithms=[security_settings.JWT_ALGORITHM],
        )
    except jwt.PyJWTError:
        return None
