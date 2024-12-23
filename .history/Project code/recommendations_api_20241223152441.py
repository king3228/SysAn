import requests
import json


# Базовый URL API Gateway
BASE_URL = "https://d5de4233mi7e427khfjs.i99u1wfk.apigw.yandexcloud.net/recommendations"

# Ключ администратора (для запросов, где нужен auth_key)
ADMIN_KEY = "admin_key_123"

# Функция для парсинга и форматированного вывода ошибок
def handle_error(response):
    try:
        error_data = response.json()
    except:
        error_data = {"status": "error", "message": "Неизвестная ошибка."}
    print(f"Ошибка: {error_data.get('message', 'Неизвестная ошибка')} (HTTP {response.status_code})")
    return error_data


# 1. Получить все списки
def get_all_lists():
    url = f"{BASE_URL}/lists"
    response = requests.get(url)

    if response.status_code == 200:
        # Парсим названия и описания из списка
        all_lists = response.json().get("data", [])
        result = [
            f"• {item['name']}: {item['description']}" for item in all_lists
        ]
        print("\n".join(result))
        return all_lists
    else:
        return handle_error(response)


# 2. Получить один список
def get_single_list(list_id):
    url = f"{BASE_URL}/lists/{list_id}"
    response = requests.get(url)

    if response.status_code == 200:
        # Парсим и возвращаем данные списка
        list_data = response.json().get("data", {})
        return list_data
    else:
        return handle_error(response)


# Вспомогательная функция: Получить данные аниме по ID через Shikimori API
def get_anime_details_from_shikimori(anime_id):
    base_shikimori_url = "https://shikimori.me/api"
    url = f"{base_shikimori_url}/animes/{anime_id}"
    response = requests.get(url)

    if response.status_code == 200:
        anime_data = response.json()
        details = {
            "title": anime_data.get("name", "NaN"),
            "link": f"https://shikimori.me{anime_data.get('url', '')}"
        }
        return details
    else:
        return {"title": "NaN", "link": None}


# 2. Получить список с названиями аниме
def get_detailed_single_list(list_id):
    # Получаем данные списка через API
    list_data = get_single_list(list_id)

    if not list_data or "anime_ids" not in list_data:
        print("Ошибка или пустой список.")
        return None

    anime_titles = []
    for anime_id in list_data["anime_ids"]:
        # Запрашиваем название и ссылку через Shikimori
        details = get_anime_details_from_shikimori(anime_id)
        anime_titles.append(f"{details['title']} - {details['link']}")

    # Форматируем итоговый список для вывода
    result = {
        "name": list_data.get("name"),
        "description": list_data.get("description"),
        "type": list_data.get("type"),
        "genre": list_data.get("genre"),
        "year": list_data.get("year"),
        "anime_titles": anime_titles
    }
    return result


# 3. Сравнить список с просмотренным
def compare_list_with_watched(list_id, chat_id):
    url = f"{BASE_URL}/lists/{list_id}/compare"
    data = {"chat_id": chat_id}

    response = requests.post(url, json=data)

    if response.status_code == 200:
        # Делим аниме на просмотренные и непросмотренные
        data = response.json().get("data", {})
        viewed = data.get("viewed", [])
        not_viewed = data.get("not_viewed", [])

        result = {
            "viewed": [get_anime_details_from_shikimori(anime_id)["title"] for anime_id in viewed],
            "not_viewed": [get_anime_details_from_shikimori(anime_id)["title"] for anime_id in not_viewed]
        }
        return result
    else:
        return handle_error(response)