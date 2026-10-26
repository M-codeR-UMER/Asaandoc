from redis.asyncio import Redis

from app.config import db_settings

_token_blacklist = Redis(
    host=db_settings.REDIS_HOST,
    port=db_settings.REDIS_PORT,
    db=0,    
)

async def add_jti_to_blacklist(jti: str):
    await _token_blacklist.set(jti, "blacklisted", ex=3600)  # Set the JTI in Redis with an expiration time of 1 hour
    
    
async def is_jti_blacklisted(jti: str) -> bool:
    return await _token_blacklist.exists(jti) 