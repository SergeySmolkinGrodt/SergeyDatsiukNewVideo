import time
import telegram
from facebook_scraper import get_posts
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# --- НАСТРОЙКИ ---
FACEBOOK_USER_URL = os.getenv('FACEBOOK_USER_URL')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
CHECK_INTERVAL_SECONDS = 3600  # Интервал проверки в секундах (3600 = 1 час)
# -----------------

# Файл для хранения ID последнего обработанного поста
LAST_POST_ID_FILE = 'last_post_id.txt'

def send_telegram_notification(bot, post):
    """Отправляет уведомление в Telegram."""
    message = f"Новый пост от {post['username']}!\n\n"
    if post['text']:
        message += f"{post['text']}\n\n"
    if post['link']:
        message += f"Ссылка в посте: {post['link']}\n"
    message += f"Ссылка на пост: {post['post_url']}"

    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print("Уведомление в Telegram отправлено.")
    except Exception as e:
        print(f"Ошибка при отправке уведомления в Telegram: {e}")

def get_last_post_id():
    """Читает ID последнего поста из файла."""
    try:
        with open(LAST_POST_ID_FILE, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def set_last_post_id(post_id):
    """Записывает ID последнего поста в файл."""
    with open(LAST_POST_ID_FILE, 'w') as f:
        f.write(str(post_id))

def main():
    """Основная функция мониторинга."""
    if not all([FACEBOOK_USER_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
        print("Ошибка: Отсутствуют необходимые переменные окружения. Убедитесь, что .env файл настроен корректно.")
        return

    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    last_post_id = get_last_post_id()

    print("Запуск мониторинга...")

    while True:
        try:
            print(f"Проверка новых постов для пользователя: {FACEBOOK_USER_URL}")
            
            # Получаем посты, используя итератор
            posts_iterator = get_posts(FACEBOOK_USER_URL, pages=5, cookies="cookies.txt")
            
            latest_post = None
            try:
                # Пытаемся получить первый пост из итератора
                latest_post = next(posts_iterator)
            except StopIteration:
                print("Не удалось получить посты. Возможно, нужно обновить cookies или Facebook изменил верстку.")
                time.sleep(CHECK_INTERVAL_SECONDS)
                continue

            if latest_post:
                latest_post_id = latest_post['post_id']

                if latest_post_id != last_post_id:
                    print(f"Найден новый пост! ID: {latest_post_id}")
                    if latest_post['link'] or ('http' in (latest_post['text'] or '')):
                        send_telegram_notification(bot, latest_post)
                    else:
                        print("В новом посте нет ссылки, уведомление не отправлено.")
                    
                    set_last_post_id(latest_post_id)
                    last_post_id = latest_post_id
                else:
                    print("Новых постов нет.")
            else:
                print("Не удалось получить информацию о последнем посте.")

        except Exception as e:
            print(f"Произошла ошибка: {e}")
            time.sleep(CHECK_INTERVAL_SECONDS * 2)

        print(f"Следующая проверка через {CHECK_INTERVAL_SECONDS / 60} минут.")
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == '__main__':
    main()