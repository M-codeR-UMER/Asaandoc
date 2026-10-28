from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt

from app.config import security_settings


def generate_access_token(
    data: dict,
    expiray: timedelta = timedelta(hours=1),
) -> str:
    return jwt.encode(
        payload={
            **data, # Unpacking a dict
            "jti":uuid4().hex, 
            "exp": datetime.now(timezone.utc) + expiray,
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
