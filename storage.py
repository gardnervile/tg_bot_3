from __future__ import annotations
from typing import Dict, Optional, List, Any


def _make_key(user_id: int, platform: str, suffix: str = "") -> str:
    base = f"{platform}:{user_id}"
    return f"{base}:{suffix}" if suffix else base


def save_question(redis_client, user_id: int, question: str, platform: str = "tg") -> None:
    key = _make_key(user_id, platform, "question")
    redis_client.set(key, question, ex=24 * 3600)


def load_question(redis_client, user_id: int, platform: str = "tg") -> Optional[str]:
    key = _make_key(user_id, platform, "question")
    return redis_client.get(key)


def save_qa(
    redis_client,
    user_id: int,
    question: str,
    answer: str,
    zachet: List[str],
    platform: str = "tg",
) -> None:
    key = _make_key(user_id, platform, "qa")
    redis_client.hset(
        key,
        mapping={
            "question": question,
            "answer": answer,
            "zachet": ";".join(zachet or []),
        },
    )


def load_qa(redis_client, user_id: int, platform: str = "tg") -> Optional[Dict[str, Any]]:
    key = _make_key(user_id, platform, "qa")
    qa_record = redis_client.hgetall(key)
    if not qa_record:
        return None
    return {
        "question": qa_record.get("question"),
        "answer": qa_record.get("answer"),
        "zachet": qa_record.get("zachet", "").split(";") if qa_record.get("zachet") else [],
    }


def clear_qa(redis_client, user_id: int, platform: str = "tg") -> None:
    key = _make_key(user_id, platform, "qa")
    redis_client.delete(key)


def main() -> None:
    pass


if __name__ == "__main__":
    main()