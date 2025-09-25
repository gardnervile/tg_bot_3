import os
import random
from dataclasses import dataclass
from typing import List
from dotenv import load_dotenv

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.exceptions import ApiError

import storage as store
from quiz_bot import parse_qaz, is_correct
from redis_client import get_redis_client

QUIZ_FOLDER = "quiz-questions"


@dataclass(frozen=True)
class QAEntry:
    question: str
    answer: str
    zachet: List[str]


def build_keyboard() -> VkKeyboard:
    kb = VkKeyboard(one_time=False)
    kb.add_button("Новый вопрос", color=VkKeyboardColor.POSITIVE)
    kb.add_button("Сдаться", color=VkKeyboardColor.NEGATIVE)
    kb.add_line()
    kb.add_button("Мой счёт", color=VkKeyboardColor.PRIMARY)
    return kb


def send_msg(vk, user_id: int, text: str, keyboard: VkKeyboard | None = None) -> None:
    try:
        vk.messages.send(
            user_id=user_id,
            random_id=random.randint(1, 2**31 - 1),
            message=text,
            keyboard=(keyboard.get_keyboard() if keyboard else None),
        )
    except ApiError as e:
        print(f"VK ApiError: {e}")


def load_all_questions(folder: str) -> List[QAEntry]:
    entries: List[QAEntry] = []
    if not os.path.isdir(folder):
        return entries

    files = [
        f for f in os.listdir(folder)
        if not f.startswith(".") and os.path.isfile(os.path.join(folder, f))
    ]
    for name in files:
        path = os.path.join(folder, name)
        try:
            q, a, z = parse_qaz(path)
        except Exception:
            continue
        if q:
            entries.append(QAEntry(q, a or "", z or []))
    return entries


def pick_and_send_new_question(vk, redis_client, user_id: int, pool: List[QAEntry]) -> bool:
    if not pool:
        send_msg(vk, user_id, "Нет доступных вопросов")
        return False
    entry = random.choice(pool)
    store.save_qa(redis_client, user_id, entry.question, entry.answer, entry.zachet, platform="vk")
    send_msg(vk, user_id, entry.question)
    return True


def handle_event(event, vk, redis_client, keyboard: VkKeyboard, pool: List[QAEntry]) -> None:
    text = (event.text or "").strip()
    lower = text.lower()
    user_id = event.user_id

    if lower == "начать":
        send_msg(vk, user_id, "Привет! Вот твои кнопки 👇", keyboard=keyboard)
        return

    if lower == "новый вопрос":
        pick_and_send_new_question(vk, redis_client, user_id, pool)
        return

    if lower == "сдаться":
        current_qa = store.load_qa(redis_client, user_id, platform="vk")
        if not isinstance(current_qa, dict):
            print("DEBUG current_qa type on give_up:", type(current_qa), current_qa)
            send_msg(vk, user_id, "Активного вопроса нет")
            return
        answer_text = current_qa.get("answer") or "(ответ не найден)"
        send_msg(vk, user_id, f"Правильный ответ:\n{answer_text}")
        store.clear_qa(redis_client, user_id, platform="vk")
        pick_and_send_new_question(vk, redis_client, user_id, pool)
        return

    if lower == "мой счёт":
        send_msg(vk, user_id, "Счёт пока не считаем")
        return

    current_qa = store.load_qa(redis_client, user_id, platform="vk")
    if not isinstance(current_qa, dict):
        print("DEBUG current_qa type on answer:", type(current_qa), current_qa)
        send_msg(vk, user_id, "Сначала нажми «Новый вопрос».")
        return

    if is_correct(text, current_qa["answer"], current_qa["zachet"]):
        send_msg(vk, user_id, "Правильно! Для следующего вопроса нажми «Новый вопрос».")
        store.clear_qa(redis_client, user_id, platform="vk")
    else:
        send_msg(vk, user_id, "Неправильно… Попробуешь ещё раз?")


def main():
    load_dotenv()

    vk_session = vk_api.VkApi(token=os.environ["VK_GROUP_TOKEN"])
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    keyboard = build_keyboard()

    redis_client = get_redis_client(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        username=os.getenv("REDIS_USERNAME"),
        password=os.getenv("REDIS_PASSWORD"),
        ssl_enabled=os.getenv("REDIS_SSL", "false").lower() in ("1", "true", "yes"),
    )

    question_pool = load_all_questions(QUIZ_FOLDER)
    if not question_pool:
        print("Внимание: не найдено ни одного валидного вопроса.")

    print("VK-бот запущен…")
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            try:
                handle_event(event, vk, redis_client, keyboard, question_pool)
            except Exception as e:
                print("Error handling event:", e)


if __name__ == "__main__":
    main()