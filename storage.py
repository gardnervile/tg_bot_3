from redis_client import get_redis_client
import os

redis_client = get_redis_client(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    username=os.getenv("REDIS_USERNAME"),
    password=os.getenv("REDIS_PASSWORD"),
    ssl_enabled=os.getenv("REDIS_SSL", "false").lower() in ("1", "true", "yes"),
)

def _make_key(user_id: int, platform: str, suffix: str = "") -> str:
    base = f"{platform}:{user_id}"
    return f"{base}:{suffix}" if suffix else base


def save_question(user_id: int, question: str, platform="tg") -> None:
    key = _make_key(user_id, platform, "question")
    redis_client.set(key, question, ex=24 * 3600)


def load_question(user_id: int, platform="tg") -> str | None:
    key = _make_key(user_id, platform, "question")
    return redis_client.get(key)


def save_qa(user_id: int, question, answer, zachet, platform="tg") -> None:
    key = _make_key(user_id, platform, "qa")
    redis_client.hset(
        key,
        mapping={
            "question": question,
            "answer": answer,
            "zachet": ";".join(zachet),
        },
    )


def load_qa(user_id: int, platform="tg"):
    key = _make_key(user_id, platform, "qa")
    data = redis_client.hgetall(key)
    if not data:
        return None
    return {
        "question": data.get("question"),
        "answer": data.get("answer"),
        "zachet": data.get("zachet", "").split(";") if data.get("zachet") else [],
    }


def clear_qa(user_id: int, platform="tg") -> None:
    key = _make_key(user_id, platform, "qa")
    redis_client.delete(key)