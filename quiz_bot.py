import logging
import os
import random
import re
from telegram.ext import ConversationHandler

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from storage import save_question, load_question, save_qa, load_qa, clear_qa
from enum import Enum

class States(Enum):
    CHOOSING = 1   # ждём, пока пользователь попросит новый вопрос
    ANSWERING = 2  # ждём ответ на текущий вопрос

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext):
    user = update.effective_user
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text(
        f'Привет, {user.first_name}!',
        reply_markup=reply_markup
    )
    return States.CHOOSING


def handle_new_question_request(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    folder = "quiz-questions"
    files = [f for f in os.listdir(folder)
             if not f.startswith('.') and os.path.isfile(os.path.join(folder, f))]
    if not files:
        update.message.reply_text("Нет файлов с вопросами 😕")
        return States.CHOOSING

    filepath = os.path.join(folder, random.choice(files))
    question, answer, zachet = parse_qaz(filepath)
    if not question:
        update.message.reply_text("Не удалось извлечь вопрос 😕")
        return States.CHOOSING

    save_qa(user_id, question, answer, zachet)
    update.message.reply_text(question)
    return States.ANSWERING


def handle_solution_attempt(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    data = load_qa(user_id)
    if not data:
        update.message.reply_text("Сначала нажми «Новый вопрос».")
        return States.CHOOSING

    if is_correct(update.message.text, data["answer"], data["zachet"]):
        update.message.reply_text("Правильно! 🎉 Для следующего вопроса нажми «Новый вопрос».")
        clear_qa(user_id)
        return States.CHOOSING
    else:
        update.message.reply_text("Неправильно… Попробуешь ещё раз?")
        return States.ANSWERING


def handle_give_up(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    data = load_qa(user_id)
    if not data:
        update.message.reply_text("Активного вопроса нет 🙂")
        return States.CHOOSING

    ans = data["answer"] or "(ответ не найден)"
    update.message.reply_text(f"Правильный ответ:\n{ans}")

    clear_qa(user_id)

    folder = "quiz-questions"
    files = [f for f in os.listdir(folder)
             if not f.startswith('.') and os.path.isfile(os.path.join(folder, f))]
    if not files:
        update.message.reply_text("Нет файлов с вопросами 😕")
        return States.CHOOSING

    filepath = os.path.join(folder, random.choice(files))
    question, answer, zachet = parse_qaz(filepath)
    if not question:
        update.message.reply_text("Не удалось извлечь вопрос 😕")
        return States.CHOOSING

    save_qa(user_id, question, answer, zachet)
    update.message.reply_text(f"Следующий вопрос:\n{question}")
    return States.ANSWERING


def parse_qaz(filepath: str):
    with open(filepath, "r", encoding="KOI8-R", errors="ignore") as f:
        lines = [ln.rstrip() for ln in f.read().splitlines()]

    q, a, z = [], [], []
    rq = ra = rz = False

    for line in lines:
        s = (line or "").strip()
        if s.startswith("Вопрос"):
            rq, ra, rz = True, False, False
            q.append(line); continue
        if s.startswith("Ответ:"):
            rq, ra, rz = False, True, False
            continue
        if s.startswith("Зачет:"):
            rq, ra, rz = False, False, True
            continue
        if s.startswith("Комментарий:") or s.startswith("Источник:") or s.startswith("Автор:"):
            break

        if rq: q.append(line)
        elif ra: a.append(line)
        elif rz: z.append(line)

    question = "\n".join([ln for ln in q if ln.strip()]).strip()
    answer   = " ".join([ln for ln in a if ln.strip()]).strip()
    zachet_raw = " ".join([ln for ln in z if ln.strip()]).strip()
    zachet = [p.strip() for p in zachet_raw.split(";") if p.strip()] if zachet_raw else []
    return question, answer, zachet


_PUNCT_RE = re.compile(r"[^\wа-яё\- ]+", flags=re.IGNORECASE)

def _base_answer(s: str) -> str:
    cut = s.split(".", 1)[0]
    cut = cut.split("(", 1)[0]
    return cut.strip()

def _norm(s: str) -> str:
    s = s.strip().lower().replace("ё", "е")
    s = _PUNCT_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s)
    return s

def is_correct(user_text: str, answer: str, zachet: list[str]) -> bool:
    u = _norm(user_text)
    candidates = []

    if answer:
        candidates.append(_norm(_base_answer(answer)))
        candidates.append(_norm(answer))

    for zt in zachet or []:
        candidates.append(_norm(_base_answer(zt)))
        candidates.append(_norm(zt))

    return any(u == c or u in c or c in u for c in candidates if c)


def main() -> None:
    load_dotenv()
    telegram_token = os.environ['TG_BOT_TOKEN']

    updater = Updater(telegram_token)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            States.CHOOSING: [
                MessageHandler(Filters.regex("^Новый вопрос$"), handle_new_question_request),
            ],
            States.ANSWERING: [
                MessageHandler(Filters.regex("^Сдаться$"), handle_give_up),
                MessageHandler(Filters.text & ~Filters.command, handle_solution_attempt),
            ],
        },
        fallbacks=[],
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()