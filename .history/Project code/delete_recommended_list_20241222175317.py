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



ADMINS = [505096036, 123456789]


def is_admin_user(chat_id):
    """
    Проверяет, является ли пользователь администратором.
    """
    return chat_id in ADMINS


def delete_recommended_list(chat_id, list_id):
    """
    Удаление рекомендованного списка.
    """

    # Проверяем права администратора
    if not is_admin_user(chat_id):
        return error_response("У вас нет прав для выполнения этой операции.", code=401)

    # Загружаем данные
    recommended_lists = read_table_from_s3_csv('recommended_lists.csv')
    recommended_list_items = read_table_from_s3_csv('recommended_list_items.csv')

    # Проверяем существование списка
    if list_id not in recommended_lists['list_id'].values:
        return error_response(f"Список с ID '{list_id}' не найден.", code=404)

    # Удаляем список и связанные элементы
    recommended_lists = recommended_lists[recommended_lists['list_id'] != list_id]
    recommended_list_items = recommended_list_items[recommended_list_items['list_id'] != list_id]

    # Сохраняем изменения
    write_table_to_s3_csv(recommended_lists, 'recommended_lists.csv')
    write_table_to_s3_csv(recommended_list_items, 'recommended_list_items.csv')

    return success_response(message=f"Список с ID '{list_id}' успешно удалён.")


def delete_list_handler(event, context):
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
    auth_key = body.get('auth_key')

    if not auth_key:
        return {
            "statusCode": 401,
            "body": json.dumps({
                "status": "error",
                "message": "Отсутствует ключ аутентификации."
            })
        }

    if not list_id:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "status": "error",
                "message": "ID списка не указан."
            })
        }

    # Вызов логики удаления
    result = delete_recommended_list(auth_key, list_id)

    return {
        "statusCode": result.pop('code', 200),
        "body": json.dumps(result)
    }