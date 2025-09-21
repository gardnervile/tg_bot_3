import os

folder = "quiz-questions"

for filename in os.listdir(folder):
    filepath = os.path.join(folder, filename)
    if os.path.isfile(filepath):
        with open(filepath, "r", encoding="KOI8-R") as f:
            print(f.read())

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        States.CHOOSING.value: [
            MessageHandler(Filters.regex("^Новый вопрос$"), handle_new_question_request),
        ],
        States.ANSWERING.value: [
            MessageHandler(Filters.regex("^Сдаться$"), handle_give_up),
            MessageHandler(Filters.text & ~Filters.command, handle_solution_attempt),
        ],
    },
    fallbacks=[],
)

dispatcher.add_handler(conv_handler)