import requests
import os
import json

YANDEX_GPT_API_KEY = ''  # Убедитесь в корректности API-ключа

def send_request_to_gpt(prompt, context):
    """
    Отправляет контекст и промпт в Yandex GPT и получает ответ с рекомендациями аниме.
    """
    prompt = {
        "modelUri": "gpt://b1guhot0ad2pahaud0se/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": "2000"
        },
        "messages": [
            {
                "role": "system",
                "text": ("Ты профессиональный аниме критик, помогающий заказчикам подбирать аниме, подходящее их вкусам. "
                     "Твоя задача - рассмотреть список аниме пользователя и дать рекомендацию в формате JSON. "
                     "Результат должен содержать три объекта [{номер: номер, название: 'название'}].")
            },
            {
                "role": "user",
                "text": f"{context}\n\n{prompt}"
            }
        ]
    }
    prompt_data = {
    "modelUri": "gpt://b1g0ad2pahaud0se/yandexgpt-lite",
    "completionOptions": {
        "stream": False,
        "temperature": 0.6,
        "maxTokens": 2000
    },
    "messages": [
        {
            "role": "system",
            "text": ("Ты профессиональный аниме критик, помогающий заказчикам подбирать аниме, подходящее их вкусам. "
                     "Твоя задача - рассмотреть список аниме пользователя и дать рекомендацию в формате JSON. "
                     "Результат должен содержать три объекта [{номер: номер, название: 'название'}] - то, что ты рекомендуешь и больше ничего .")
        },
        {
            "role": "user",
            "text": f"{context}\n\n{prompt}"
        }
    ]
}

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Api-Key "
    }

    try:
        response = requests.post(url, headers=headers, json=prompt)
        response.raise_for_status()
        result = response.json()
        # Предполагаем, что ответ содержит 'choices', которые нужно обрабатывать
        # recommendations = extract_recommendations_from_response(result)
        return result

    except requests.RequestException as e:
        print(f"Error communicating with Yandex GPT: {e}")
        return None

def extract_recommendations_from_response(response):
    """
    Обрабатывает ответ от Yandex GPT и извлекает список рекомендованных аниме.
    """
    # Проверяем, что в ответе есть ключ 'result' с необходимой структурой
    if 'result' in response and 'alternatives' in response['result']:
        try:
            text_response = response['result']['alternatives'][0]['message']['text']
            # Парсим текст как JSON
            result_json = json.loads(text_response)
            return result_json
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing response: {e}")
            return None
    return None