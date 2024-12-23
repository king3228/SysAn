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

def create_recommended_list(chat_id, name, description, list_type, genre, year, anime_ids, created_by):
    """
    Создание нового рекомендованного списка.
    """

    # Проверяем права администратора
    if not is_admin_user(chat_id):
        return error_response("У вас нет прав для выполнения этой операции.", code=401)

    # Загружаем данные
    recommended_lists = read_table_from_s3_csv('recommended_lists.csv')
    recommended_list_items = read_table_from_s3_csv('recommended_list_items.csv')

    # Проверяем дублирование имени
    if not recommended_lists.empty and (recommended_lists['name'] == name).any():
        return error_response(f"Список с названием '{name}' уже существует.", code=409)

    # Создаем новый список
    list_id = generate_id()
    new_list = pd.DataFrame([{
        'list_id': list_id,
        'name': name,
        'description': description,
        'type': list_type,
        'genre': genre,
        'year': year,
        'created_by': created_by,
        'created_at': get_current_timestamp().isoformat(),
        'updated_at': get_current_timestamp().isoformat()
    }])
    recommended_lists = pd.concat([recommended_lists, new_list], ignore_index=True)

    # Добавляем элементы списка
    new_items = pd.DataFrame([{
        'list_id': list_id,
        'anime_id': anime_id
    } for anime_id in anime_ids])
    recommended_list_items = pd.concat([recommended_list_items, new_items], ignore_index=True)

    # Сохраняем изменения
    write_table_to_s3_csv(recommended_lists, 'recommended_lists.csv')
    write_table_to_s3_csv(recommended_list_items, 'recommended_list_items.csv')

    return success_response(
        message=f"Список '{name}' успешно создан.",
        data={"list_id": list_id},
        code=201
    )

def create_list_handler(event, context):
    parsed = parse_event(event)

    # Проверяем, удалось ли корректно парсить event
    if not parsed:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "status": "error",
                "message": "Некорректный запрос."
            })
        }

    # Достаём данные из тела запроса
    body = parsed['body']
    auth_key = body.get('auth_key')

    if not auth_key:
        return {
            "statusCode": 401,
            "body": json.dumps({
                "status": "error",
                "message": "Отсутствует ключ аутентификации."
            })
        }

    # Вызываем логику создания списка
    result = create_recommended_list(
        chat_id=auth_key,  # Аутентификация
        name=body.get('name'),
        description=body.get('description'),
        list_type=body.get('type'),
        genre=body.get('genre'),
        year=body.get('year'),
        anime_ids=body.get('anime_ids', []),
        created_by=body.get('created_by')
    )

    return {
        "statusCode": result.pop('code', 200),  # Код ответа из логики
        "body": json.dumps(result)
    }