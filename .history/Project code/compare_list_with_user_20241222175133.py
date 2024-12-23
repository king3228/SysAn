from object_storage import *
import json


def parse_event(event):
    """
    Универсальный парсер события.
    :param event: Входное событие (object)
    :return: Словарь с parsed_body, параметры и заголовки
    """
    try:
        # Получаем тело запроса (если это POST/PUT)
        body = json.loads(event.get('body', '{}')) if 'body' in event else {}

        # Извлекаем путь и параметры из event
        query_params = event.get('queryStringParameters', {}) or {}
        path_params = event.get('pathParameters', {}) or {}

        # Заголовки (например, для аутентификации)
        headers = event.get('headers', {}) or {}

        return {
            "body": body,
            "query_params": query_params,
            "path_params": path_params,
            "headers": headers
        }

    except Exception as e:
        print(f"Ошибка парсинга события: {e}")
        return None


def success_response(data=None, message="Успешный запрос.", code=200):
    """
    Формирует успешный JSON-ответ.
    """
    return {
        "status": "success",
        "message": message,
        "data": data,
        "code": code
    }

def error_response(message="Произошла ошибка.", code=400):
    """
    Формирует JSON-ответ при ошибке.
    """
    return {
        "status": "error",
        "message": message,
        "data": None,
        "code": code
    }




def compare_list_with_user(list_id, chat_id):
    user_anime = read_table_from_s3_csv('user_anime.csv')
    recommended_list_items = read_table_from_s3_csv('recommended_list_items.csv')

    # Проверяем существование списка
    list_items = recommended_list_items[recommended_list_items['list_id'] == list_id]
    if list_items.empty:
        return error_response(f"Список с ID '{list_id}' не найден.", code=404)

    list_anime_ids = set(list_items['anime_id'].tolist())

    # Проверяем просмотренные аниме пользователя
    user_anime_list = user_anime[user_anime['chat_id'] == chat_id]
    if user_anime_list.empty:
        return error_response(f"У пользователя с ID '{chat_id}' нет просмотренных аниме.", code=404)

    user_anime_ids = set(user_anime_list['anime_id'].tolist())

    viewed = list(list_anime_ids & user_anime_ids)
    not_viewed = list(list_anime_ids - user_anime_ids)

    return success_response(data={
        "viewed": viewed,
        "not_viewed": not_viewed
    })


def compare_list_handler(event, context):
    parsed = parse_event(event)
    if not parsed:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "status": "error",
                "message": "Некорректный запрос."
            })
        }

    path_params = parsed['path_params']
    body = parsed['body']
    list_id = path_params.get('list_id')
    chat_id = body.get('chat_id')

    if not list_id or not chat_id:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "status": "error",
                "message": "Параметры запроса неполные."
            })
        }

    result = compare_list_with_user(list_id, chat_id)

    return {
        "statusCode": result.pop('code', 200),
        "body": json.dumps(result)
    }