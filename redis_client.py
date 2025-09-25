import os
import redis
from dotenv import load_dotenv


def get_redis_client(host: str, port: int, username: str | None, password: str | None, ssl_enabled: bool) -> redis.Redis:
    return redis.Redis(
        host=host,
        port=port,
        username=username,
        password=password,
        ssl=ssl_enabled,
        decode_responses=True,
    )


def main():
    load_dotenv()

    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    username = os.getenv("REDIS_USERNAME")
    password = os.getenv("REDIS_PASSWORD")
    ssl_enabled = os.getenv("REDIS_SSL", "false").lower() in ("1", "true", "yes")

    redis_client = get_redis_client(host, port, username, password, ssl_enabled)
    print("Redis connected:", redis_client.ping())


if __name__ == "__main__":
    main()