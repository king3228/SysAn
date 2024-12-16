import time
from datetime import datetime, timezone
from object_storage import *
from shiki_api import get_user_anime_list, get_anime_by_title
from yandex_gpt_alpha import format_recommendations, get_anime_recommendations
from tg_controller import send_message

user_state = {}

def handle_start_command(chat_id):
    user_info = check_user_exists(chat_id)

    if user_info is None:
        add_user(chat_id)
        send_message(
            chat_id,
            text=("Добро пожаловать! Я бот, который поможет вам с рекомендованными аниме.\n"
                  "Используйте команды, например /get_recd для получения рекомендаций, "
                  "или /add_shiki для привязки аккаунта Shikimori."),
            command_buttons=["/get_recd", "/add_shiki"]
        )
    else:
        shikimori_username = user_info[0].get('shikimori_username')
        send_message(
            chat_id,
            text=("Рад снова вас видеть! Я ваш помощник по рекомендациям аниме. "
                  "Используйте команды, например /get_recd для получения рекомендаций"),
            command_buttons=["/get_recd", "/add_shiki"]
        )

        if not shikimori_username:
            send_message(
                chat_id,
                text=("Похоже, вы ещё не привязали аккаунт Shikimori. "
                      "Используйте команду /add_shiki, чтобы это сделать."),
                command_buttons=["/add_shiki"]
            )

def handle_add_shiki_command(chat_id):
    user_state[chat_id] = 'awaiting_id'
    send_message(chat_id, text="Пожалуйста, отправьте свой идентификатор профиля Shikimori.")

def handle_get_recommendations_request(chat_id):
    user_state[chat_id] = 'awaiting_recommendation_prompt'
    send_message(chat_id, text="Пожалуйста, напишите пожелания по аниме, которое хотите посмотреть.")

def handle_user_input_for_recommendations(chat_id, user_query):
    if chat_id in user_state and user_state[chat_id] == 'awaiting_recommendation_prompt':
        del user_state[chat_id]

        user_info = check_user_exists(chat_id)
        if user_info is not None:
            last_updated = user_info.loc[0, 'last_updated']
            shikimori_username = user_info.loc[0, 'shikimori_username']
            current_time = datetime.now(timezone.utc)
            seconds_since_epoch = int(current_time.timestamp())
            if (seconds_since_epoch - last_updated) > 86400:
                if shikimori_username:
                    user_anime_list = get_user_anime_list(shikimori_username)
                    load_user_anime_list(chat_id, user_anime_list)
                    update_last_updated(chat_id)
                else:
                    send_message(chat_id, "Необходимо привязать аккаунт Shikimori, чтобы обновить список.")
            
            context_data = get_context_data(chat_id)
            recommendations = format_recommendations(get_anime_recommendations(context_data, user_query))

            if not recommendations:
                send_message(chat_id, "Не удалось получить рекомендации. Попробуйте позже.")
                return

            for recommendation in recommendations:
                title = recommendation.get('название')
                anime_info = get_anime_by_title(title)
                time.sleep(1)  # Предотвращение перегрузки API

                if anime_info:
                    text = (f"{anime_info['name']} ({anime_info.get('season', 'N/A')})\n"
                            f"{anime_info['description']}\nОценка: {anime_info['score']}\n"
                            f"Жанры: {', '.join([genre['name'] for genre in anime_info['genres']])}")

                    photo_url = anime_info['poster']['main2xUrl']
                    result = send_message(
                        chat_id, 
                        text=text, 
                        photo_url=photo_url, 
                        inline_button_text="Подробнее на Shikimori", 
                        inline_button_url=anime_info['url']
                    )

                    if not result['success'] and result.get('status_code') == 400:
                        # Повторите попытку без фото, если возникла ошибка 400
                        send_message(
                            chat_id,
                            text=text,
                            inline_button_text="Подробнее на Shikimori",
                            inline_button_url=anime_info['url']
                        )
                else:
                    send_message(chat_id, f"{title}\nИзвините, технические неполадки.")

def handle_message(chat_id, text):
    if chat_id in user_state:
        if user_state[chat_id] == 'awaiting_id':
            add_shiki_to_user(chat_id, text)
            send_message(chat_id, "Ваш аккаунт Shikimori успешно привязан!")
            del user_state[chat_id]
        elif user_state[chat_id] == 'awaiting_recommendation_prompt':
            handle_user_input_for_recommendations(chat_id, text)
            del user_state[chat_id]
        return

    if text.startswith('/start'):
        handle_start_command(chat_id)
    elif text.startswith('/add_shiki'):
        handle_add_shiki_command(chat_id)
    elif text.startswith('/get_recd'):
        handle_get_recommendations_request(chat_id)
    else:
        send_message(chat_id, "Неизвестная команда. Попробуйте /start, /add_shiki или /get_recd.")