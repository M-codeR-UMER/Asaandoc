import asyncio
from datetime import datetime, timezone
from weakref import WeakKeyDictionary

from redis.asyncio import Redis

from app.config import db_settings

_clients: WeakKeyDictionary[asyncio.AbstractEventLoop, Redis] = WeakKeyDictionary()


def get_redis_client() -> Redis:
    loop = asyncio.get_running_loop()
    client = _clients.get(loop)
    if client is None:
        client = Redis(
            host=db_settings.REDIS_HOST,
            port=db_settings.REDIS_PORT,
            db=0,
        )
        _clients[loop] = client
    return client


async def add_jti_to_blacklist(jti: str, exp: int) -> None:
    ttl = int(exp - datetime.now(timezone.utc).timestamp())
    if ttl > 0:
        client = get_redis_client()
        await client.set(jti, "blacklisted", ex=ttl)


async def is_jti_blacklisted(jti: str) -> bool:
    client = get_redis_client()
    return bool(await client.exists(jti))
