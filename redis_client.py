import os, redis
from dotenv import load_dotenv

def make_redis():
    load_dotenv()
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    password = os.getenv("REDIS_PASSWORD")
    ssl_enabled = os.getenv("REDIS_SSL", "false").lower() in ("1", "true", "yes")

    return redis.Redis(
        host=host,
        port=port,
        username=os.getenv("REDIS_USERNAME"),
        password=password,
        ssl=ssl_enabled,
        decode_responses=True
    )

r = make_redis()
print(r.ping())