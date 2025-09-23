import logging
import os
import random
import re
from enum import Enum

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

from storage import save_qa, load_qa, clear_qa


QUIZ_FOLDER = "quiz-questions"
_NON_WORDS_RE = re.compile(r"[^\wа-яё\- ]+", flags=re.IGNORECASE)


def _take_base_answer(text: str) -> str:
    head = text.split(".", 1)[0]
    head = head.split("(", 1)[0]
    return head.strip()

def _normalize(text: str) -> str:
    norm = text.strip().lower().replace("ё", "е")
    norm = _NON_WORDS_RE.sub(" ", norm)
    norm = re.sub(r"\s+", " ", norm)
    return norm

def parse_qaz(filepath: str):
    with open(filepath, "r", encoding="KOI8-R", errors="ignore") as f:
        lines = [line.rstrip() for line in f.read().splitlines()]

    question_lines, answer_lines, accept_lines = [], [], []
    in_question = in_answer = in_accept = False

    for line in lines:
        stripped = (line or "").strip()

        if stripped.startswith("Вопрос"):
            in_question, in_answer, in_accept = True, False, False
            question_lines.append(line)
            continue
        if stripped.startswith("Ответ:"):
            in_question, in_answer, in_accept = False, True, False
            continue
        if stripped.startswith("Зачет:"):
            in_question, in_answer, in_accept = False, False, True
            continue
        if stripped.startswith(("Комментарий:", "Источник:", "Автор:")):
            break

        if in_question:
            question_lines.append(line)
        elif in_answer:
            answer_lines.append(line)
        elif in_accept:
            accept_lines.append(line)

    question_text = "\n".join(l for l in question_lines if l.strip()).strip()
    answer_text   = " ".join(l for l in answer_lines   if l.strip()).strip()
    accept_raw    = " ".join(l for l in accept_lines   if l.strip()).strip()
    accept_list   = [p.strip() for p in accept_raw.split(";") if p.strip()] if accept_raw else []
    return question_text, answer_text, accept_list

def is_correct(user_answer: str, correct_answer: str, accept_list: list[str]) -> bool:
    user_norm = _normalize(user_answer)
    candidates: list[str] = []
    if correct_answer:
        candidates.append(_normalize(_take_base_answer(correct_answer)))
        candidates.append(_normalize(correct_answer))
    for acc in accept_list or []:
        candidates.append(_normalize(_take_base_answer(acc)))
        candidates.append(_normalize(acc))
    return any(user_norm == c or user_norm in c or c in user_norm for c in candidates if c)

def _pick_random_qafile(folder: str = QUIZ_FOLDER) -> str | None:
    files = [f for f in os.listdir(folder) if not f.startswith('.') and os.path.isfile(os.path.join(folder, f))]
    if not files:
        return None
    return os.path.join(folder, random.choice(files))


class States(Enum):
    CHOOSING = 1
    ANSWERING = 2


logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext):
    logger.info("Команда /start от %s", update.effective_user.id)
    keyboard = ReplyKeyboardMarkup([['Новый вопрос', 'Сдаться'], ['Мой счет']], resize_keyboard=True)
    update.message.reply_text(f"Привет, {update.effective_user.first_name}!", reply_markup=keyboard)
    return States.CHOOSING

def handle_new_question_request(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    filepath = _pick_random_qafile()
    if not filepath:
        update.message.reply_text("Нет файлов с вопросами")
        return States.CHOOSING

    question, answer, accept = parse_qaz(filepath)
    if not question:
        update.message.reply_text("Не удалось извлечь вопрос")
        return States.CHOOSING

    save_qa(user_id, question, answer, accept)
    update.message.reply_text(question)
    return States.ANSWERING

def handle_solution_attempt(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    data = load_qa(user_id)
    if not data:
        update.message.reply_text("Сначала нажми «Новый вопрос».")
        return States.CHOOSING

    if is_correct(update.message.text, data["answer"], data["zachet"]):
        update.message.reply_text("Правильно! Для следующего вопроса нажми «Новый вопрос».")
        clear_qa(user_id)
        return States.CHOOSING
    else:
        update.message.reply_text("Неправильно… Попробуешь ещё раз?")
        return States.ANSWERING

def handle_give_up(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    data = load_qa(user_id)
    if not data:
        update.message.reply_text("Активного вопроса нет")
        return States.CHOOSING

    answer = data["answer"] or "(ответ не найден)"
    update.message.reply_text(f"Правильный ответ:\n{answer}")
    clear_qa(user_id)

    filepath = _pick_random_qafile()
    if not filepath:
        update.message.reply_text("Нет файлов с вопросами")
        return States.CHOOSING

    question, corr_answer, accept = parse_qaz(filepath)
    if not question:
        update.message.reply_text("Не удалось извлечь вопрос")
        return States.CHOOSING

    save_qa(user_id, question, corr_answer, accept)
    update.message.reply_text(f"Следующий вопрос:\n{question}")
    return States.ANSWERING


def main() -> None:
    logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
    load_dotenv()
    token = os.environ["TG_BOT_TOKEN"]

    updater = Updater(token)
    dp = updater.dispatcher

    conv = ConversationHandler(
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
    dp.add_handler(conv)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()