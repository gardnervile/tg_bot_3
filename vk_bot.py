import os
import random
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from storage import save_qa, load_qa, clear_qa
from quiz_bot import parse_qaz, is_correct


def build_keyboard():
    kb = VkKeyboard(one_time=False)
    kb.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
    kb.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    kb.add_line()
    kb.add_button('Мой счёт', color=VkKeyboardColor.PRIMARY)
    return kb


def pick_and_send_new_question(vk, user_id):
    folder = "quiz-questions"

    files = [f for f in os.listdir(folder)
             if not f.startswith('.') and os.path.isfile(os.path.join(folder, f))]
    if not files:
        vk.messages.send(
            user_id=user_id,
            random_id=random.randint(1, 10**9),
            message="Нет файлов с вопросами"
        )
        return False

    filepath = os.path.join(folder, random.choice(files))
    try:
        q, a, z = parse_qaz(filepath)
    except Exception:
        vk.messages.send(
            user_id=user_id,
            random_id=random.randint(1, 10**9),
            message="Не удалось извлечь вопрос"
        )
        return False

    if not q:
        vk.messages.send(
            user_id=user_id,
            random_id=random.randint(1, 10**9),
            message="Не удалось извлечь вопрос"
        )
        return False

    save_qa(user_id, q, a, z)
    vk.messages.send(
        user_id=user_id,
        random_id=random.randint(1, 10**9),
        message=q
    )
    return True


def handle_event(event, vk, keyboard):
    text = (event.text or "").strip()
    lower = text.lower()
    user_id = event.user_id

    if lower == "начать":
        vk.messages.send(user_id=user_id, random_id=0,
                         message="Привет! Вот твои кнопки 👇",
                         keyboard=keyboard.get_keyboard())
        return

    if lower == "новый вопрос":
        pick_and_send_new_question(vk, user_id)
        return

    if lower == "сдаться":
        data = load_qa(user_id)
        if not data:
            vk.messages.send(user_id=user_id, random_id=0, message="Активного вопроса нет")
            return
        ans = data.get("answer") or "(ответ не найден)"
        vk.messages.send(user_id=user_id, random_id=0, message=f"Правильный ответ:\n{ans}")
        clear_qa(user_id)
        pick_and_send_new_question(vk, user_id)
        return

    if lower == "мой счёт":
        vk.messages.send(user_id=user_id, random_id=0, message="Счёт пока не считаем")
        return

    data = load_qa(user_id)
    if not data:
        vk.messages.send(user_id=user_id, random_id=0,
                         message="Сначала нажми «Новый вопрос».")
        return

    if is_correct(text, data["answer"], data["zachet"]):
        vk.messages.send(user_id=user_id, random_id=0,
                         message="Правильно! Поздравляю! 🎉 Для следующего вопроса нажми «Новый вопрос».")
        clear_qa(user_id)
    else:
        vk.messages.send(user_id=user_id, random_id=0,
                         message="Неправильно… Попробуешь ещё раз?")

def main():
    vk_session = vk_api.VkApi(token=os.environ["VK_GROUP_TOKEN"])
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    keyboard = build_keyboard()
    
    print("VK-бот запущен…")
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            try:
                handle_event(event, vk, keyboard)
            except Exception as e:
                print("Error handling event:", e)

if __name__ == "__main__":
    main()