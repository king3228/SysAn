import requests
import os
import json
from dotenv import load_dotenv

load_dotenv('/Users/p.miroshin/Documents/Masters/2d_year/keys.env')
BOT_TOKEN = os.environ.get('TMP_TELEGRAM_TOKEN')
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_message(chat_id, text, photo_url=None, command_buttons=None, inline_button_text=None, inline_button_url=None):
    # Подготовка клавиатуры для команд, если переданы соответствующие параметры
    reply_markup = None

    if command_buttons:
        keyboard = [[{'text': cmd}] for cmd in command_buttons]
        markup = {"keyboard": keyboard, "resize_keyboard": True, "one_time_keyboard": True}
    else:
        markup = {}

    # Подготовка встроенной клавиатуры, если переданы параметры для ссылки
    if inline_button_text and inline_button_url:
        inline_markup = {
            "inline_keyboard": [[{"text": inline_button_text, "url": inline_button_url}]]
        }
        reply_markup = inline_markup
    else:
        reply_markup = markup if command_buttons else None

    # Подготовка данных и файлов для запроса
    if photo_url:
        url = f"{BASE_URL}/sendPhoto"
        data = {'chat_id': chat_id, 'caption': text, 'reply_markup': json.dumps(reply_markup) if reply_markup else None}
        files = {'photo': requests.get(photo_url).content}
    else:
        url = f"{BASE_URL}/sendMessage"
        data = {'chat_id': chat_id, 'text': text, 'reply_markup': json.dumps(reply_markup) if reply_markup else None}
        files = None

    try:
        response = requests.post(url, data=data, files=files)
        response.raise_for_status()  # Проверка наличия HTTP ошибок
    except requests.RequestException as e:
        print(f"Error sending message: {e}")

    return response.json()

    
def handler(event, context):
    from main import handle_message
    try:
        body = json.loads(event['body'])
        print(f"Received event body: {body}")  # Логирование входящего тела

        message = body.get('message', {})
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text', '')

        handle_message(chat_id, text)

        return {'statusCode': 200, 'body': 'OK'}
        
    except Exception as e:
        print(f"Error handling message: {e}")
        return {'statusCode': 500, 'body': 'Internal Server Error'}