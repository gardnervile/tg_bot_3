from redis_client import r

def save_question(user_id: int, question: str) -> None:
    r.set(f"quiz:{user_id}:current_question", question, ex=24*3600)

def load_question(user_id: int) -> str | None:
    return r.get(f"quiz:{user_id}:current_question")

def save_qa(user_id: int, question: str, answer: str, zachet: list[str] | None = None) -> None:
    key = f"quiz:{user_id}:current"
    r.hset(key, mapping={
        "question": question,
        "answer": answer,
        "zachet": "|||".join(zachet or []),
    })
    r.expire(key, 24*3600)

def load_qa(user_id: int):
    key = f"quiz:{user_id}:current"
    data = r.hgetall(key)
    if not data:
        return None
    z = data.get("zachet") or ""
    return {
        "question": data.get("question", ""),
        "answer": data.get("answer", ""),
        "zachet": [p for p in z.split("|||") if p],
    }

def clear_qa(user_id: int) -> None:
    r.delete(f"quiz:{user_id}:current")