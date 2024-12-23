from recommendations_api import get_all_lists, get_detailed_single_list, compare_list_with_watched
from tg_controller import *

# Пример функций для бота

# Функция: Посмотреть все списки
def handle_get_all_lists(chat_id):
    all_lists = get_all_lists()
    if all_lists:
        response = "Доступные списки:\n\n" + "\n".join(
            [f"• {item['name']}: {item['description']}" for item in all_lists]
        )
    else:
        response = "Не удалось получить списки."
    # Отправляем результат в чат пользователю
    send_message(chat_id, response)


# Функция: Найти один список
def handle_get_single_list(chat_id, list_id):
    detailed_list = get_detailed_single_list(list_id)
    if detailed_list:
        response = (
            f"Список: {detailed_list['name']}\n"
            f"Описание: {detailed_list['description']}\n"
            f"Тип: {detailed_list['type']}\n"
            f"Жанр: {detailed_list['genre']}\n"
            f"Год: {detailed_list['year']}\n\n"
            "Аниме в списке:\n" + "\n".join(detailed_list["anime_titles"])
        )
    else:
        response = "Не удалось найти список."
    # Отправляем результат в чат пользователю
    send_message(chat_id, response)


# Функция: Сравнить список с просмотренным
def handle_compare_list(chat_id, list_id):
    compared = compare_list_with_watched(list_id, chat_id)
    if compared:
        response = (
            "Сравнение списка с вашей библиотекой:\n\n"
            "Просмотренные:\n" + "\n".join(compared["viewed"]) + "\n\n"
            "Не просмотренные:\n" + "\n".join(compared["not_viewed"])
        )
    else:
        response = "Ошибка при сравнении списка."
    # Отправляем результат в чат пользователю
    send_message(chat_id, response)