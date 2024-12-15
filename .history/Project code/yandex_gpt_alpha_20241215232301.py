import os
import requests
from dotenv import load_dotenv
import json

load_dotenv('/Users/p.miroshin/Documents/Masters/2d_year/keys.env')
API_KEY = os.environ.get('API_KEY')

def get_anime_recommendations(user_data, user_query):
    # URL Yandex GPT API
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    
    # Формируем prompt
    prompt = {
        "modelUri": "gpt://b1g2limvdgt2f168bml3/yandexgpt/latest",  # если используется конкретная модель
        "completionOptions": {
        "stream": False,
        "temperature": 0.6,
        "maxTokens": "2000"
        },
        "messages": [
            {
                "role": "system",
                "text": (
                    "Ты эксперт по аниме. На основе пользовательского запроса и данных, "
                    "предоставленных ниже, порекомендуй три аниме. Данные пользователя включают "
                    "любимый жанр, среднюю длину аниме, список топовых (любимых) и нелюбимых тайтлов. "
                    "Ответ должен строго соответствовать формату JSON, например:\n"
                    "[\n"
                    "    {\"1\": \"Noumin Kanren no Skill bakka Agetetara Nazeka Tsuyoku Natta.\"},\n"
                    "    {\"2\": \"Isekai de Cheat Skill wo Te ni Shita Ore wa, Genjitsu Sekai wo mo Musou Suru: Level Up wa Jinsei wo Kaeta\"},\n"
                    "    {\"3\": \"Sousou no Frieren\"}\n"
                    "]\n"
                    "Указывай рекомендации на романизированном японском языке."
                )
            },
            {
                "role": "user",
                "text": (
                    f"Мои данные: {user_data}\n"
                    f"Мои пожелания: {user_query}"
                )
            }
        ]
    }
    
    # Заголовки для авторизации
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {API_KEY}"
    }
    
    # Выполнение запроса
    response = requests.post(url, json=prompt, headers=headers)
    
    # Проверка успешности ответа
    if response.status_code == 200:
        try:
            recommendations = response.json()
            return recommendations
        except ValueError:
            return {"error": "Ошибка обработки ответа API. Проверь JSON-формат."}
    else:
        return {"error": f"Ошибка запроса: {response.status_code}, {response.text}"}


def format_recommendations(api_response):
    """
    Преобразует ответ от Yandex GPT в нормальный формат, пригодный для использования в Python.
    """
    try:
        # Извлекаем текст ответа ассистента
        gpt_message = api_response.get('result', {}).get('alternatives', [{}])[0].get('message', {}).get('text', '')
        
        # Убираем тройные кавычки (```) и пробелы, если они есть
        gpt_message_clean = gpt_message.strip().strip('```')
        
        # Преобразуем строку в Python-объект (JSON)
        recommendations_raw = json.loads(gpt_message_clean)
        
        # Преобразуем список в требуемый формат с ключом "название"
        recommendations = [{"название": item[str(i + 1)]} for i, item in enumerate(recommendations_raw)]
        
        return recommendations
    except (KeyError, ValueError, IndexError, json.JSONDecodeError) as e:
        # Обработка ошибок, если структура ответа неожиданная
        return None