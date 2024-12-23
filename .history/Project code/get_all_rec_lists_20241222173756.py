from object_storage import *


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

def get_all_recommended_lists():
    recommended_lists = read_table_from_s3_csv('recommended_lists.csv')

    if recommended_lists.empty:
        return success_response(data=[], message="Списков нет.", code=200)

    result = recommended_lists.to_dict(orient='records')
    return success_response(data=result)