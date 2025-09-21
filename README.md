# Quiz Bot (Telegram + VK)

Два чат-бота (для Telegram и ВКонтакте), которые задают вопросы викторины из текстовых файлов.
## Ссылки
Телеграмм - https://t.me/quizovich_bot
VK - https://vk.ru/club232796003
## Стек
- Python 3.12
- [python-telegram-bot==13.15](https://pypi.org/project/python-telegram-bot/13.15/)  
- [vk_api==11.10.0](https://pypi.org/project/vk-api/)  
- Redis (для хранения состояния)  
- systemd (для автозапуска на сервере)  

## Установка

```bash
# Клонируем проект
git clone <url> /opt/quiz_bot
cd /opt/quiz_bot/tg_bot_3

# Создаём виртуальное окружение
python3.12 -m venv /opt/quiz_bot/.venv
source /opt/quiz_bot/.venv/bin/activate

# Устанавливаем зависимости
pip install -r requirements.txt
```
# Конфигурация

В корне проекта (/opt/quiz_bot/tg_bot_3/.env) создайте файл с токенами:
```
TG_BOT_TOKEN=ТОКЕН_БОТА_ТГ
REDIS_HOST=ХОСТ_РЭДИС
REDIS_PORT=ПОРТ_РЭДИС
REDIS_USERNAME=default
REDIS_PASSWORD=ПАРОЛЬ
REDIS_SSL=false
VK_GROUP_TOKEN=ТОКЕН_ГРУППЫ
```
# Запуск вручную
```
# Telegram бот
python quiz_bot.py

# VK бот
python vk_bot.py
```
# Запуск через systemd

Файлы сервисов:
	•	/etc/systemd/system/quiz-bot.service
	•	/etc/systemd/system/vk-bot.service

Применить и включить:
```
systemctl daemon-reload
systemctl enable quiz-bot vk-bot
systemctl start quiz-bot vk-bot
```
Проверка логов:
```
journalctl -u quiz-bot -n 50 -l --no-pager
journalctl -u vk-bot -n 50 -l --no-pager
```
