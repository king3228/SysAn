import os
import requests
from dotenv import load_dotenv

load_dotenv('/Users/p.miroshin/Documents/Masters/2d_year/keys.env')
API_KEY = os.environ.get('API_KEY')

def get_anime_recommendations(api_key, user_data, user_query):
    # URL Yandex GPT API
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    
    # Формируем prompt
    prompt = {
        "modelUri": "gpt://b1g2limvdgt2f168bml3/yandexgpt/latest",  # если используется конкретная модель
        "completionOptions": {
        "stream": false,
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
    

# Пример данных пользователя
user_data = {
    'top_genre': 'Action',
    'median_episodes': 12.0,
    'top_titles': ['Grand Blue', 'Fullmetal Alchemist', 'Fullmetal Alchemist: Brotherhood'],
    'bottom_titles': [
        'Noumin Kanren no Skill bakka Agetetara Nazeka Tsuyoku Natta.',
        'Isekai de Cheat Skill wo Te ni Shita Ore wa, Genjitsu Sekai wo mo Musou Suru: Level Up wa Jinsei wo Kaeta',
        'Tokyo Ghoul √A'
    ]
}

# Запрос пользователя
user_query = "Я люблю динамичные аниме с интересными персонажами, где мало романтики."

# Вызов функции
result = get_anime_recommendations(api_key, user_data, user_query)

# Вывод результата
print(result)