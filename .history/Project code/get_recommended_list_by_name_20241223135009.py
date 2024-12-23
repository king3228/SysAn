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
        path_params = event.get('pathParams', {}) or {}

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



ADMINS = [505096036, 123456789]

def get_recommended_list_by_name(name):
    recommended_lists = read_table_from_s3_csv('recommended_lists.csv')
    recommended_list_items = read_table_from_s3_csv('recommended_list_items.csv')

    recommended_list = recommended_lists[recommended_lists['name'] == name]

    if recommended_list.empty:
        return error_response(f"Список с названием '{name}' не найден.", code=404)

    # Извлекаем ID списка и связанные тайтлы
    list_id = recommended_list.iloc[0]['list_id']
    list_items = recommended_list_items[recommended_list_items['list_id'] == list_id]
    anime_ids = list_items['anime_id'].tolist()

    result = {
        "list_id": list_id,
        "name": name,
        "description": recommended_list.iloc[0]['description'],
        "type": recommended_list.iloc[0]['type'],
        "genre": recommended_list.iloc[0]['genre'],
        "year": recommended_list.iloc[0]['year'],
        "anime_ids": anime_ids
    }

    return success_response(data=result)

def get_single_list_handler(event, context):
    parsed = parse_event(event)
    if not parsed:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "status": "error",
                "message": "Некорректный запрос."
            })
        }

    # Получаем ID списка из параметров пути
    path_params = parsed['path_params']
    list_id = path_params.get('list_id')

    if not list_id:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "status": "error",
                "message": "ID списка не указан."
            })
        }

    # Вызов логики получения данных о списке
    result = get_recommended_list_by_name(list_id)

    return {
        "statusCode": result.pop('code', 200),
        "body": json.dumps(result, ensure_ascii=False)
    }