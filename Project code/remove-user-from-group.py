import os
import pandas as pd
from datetime import datetime, timezone
import uuid
import requests
import json
from object_storage import *

def add_anime_to_group(event, context):
    data = json.loads(event['body'])
    group_name = data.get('group_name')
    user_id = data.get('user_id')
    anime_title = data.get('anime_title')

    if not is_user_in_group(group_name, user_id):
        return {
            "statusCode": 403,
            "body": json.dumps({"status": "error", "message": f"Пользователь '{user_id}' не является участником группы '{group_name}'."})
        }

    # Чтение текущего файла groups.csv
    groups_df = read_table_from_s3_csv('groups.csv')

    # Проверка, существует ли группа с таким именем
    group_row = groups_df[groups_df['name'] == group_name]
    if group_row.empty:
        return {
            "statusCode": 404,
            "body": json.dumps({"status": "error", "message": f"Группа '{group_name}' не существует."})
        }

    group_id = group_row['group_id'].values[0]

    # Чтение текущего файла group_watched_anime.csv
    anime_df = read_table_from_s3_csv('group_watched_anime.csv')

    # Получение данных об аниме по его названию
    anime_data = get_anime_by_title(anime_title)
    if anime_data:
        anime_id = int(anime_data['id'])
        anime_name = anime_data['name']

        # Проверка, добавлено ли уже это аниме в группу
        existing_anime = anime_df[(anime_df['group_id'] == group_id) & (anime_df['anime_id'] == anime_id)]
        if not existing_anime.empty:
            return {
                "statusCode": 400,
                "body": json.dumps({"status": "error", "message": f"Аниме '{anime_name}' уже добавлено в группу '{group_name}'."})
            }

        # Добавление нового аниме
        new_anime = pd.DataFrame([{'group_id': group_id, 'anime_id': anime_id, 'anime_name': anime_name, 'watched_at': datetime.now()}])
        anime_df = pd.concat([anime_df, new_anime], ignore_index=True)
        write_table_to_s3_csv(anime_df, 'group_watched_anime.csv')
        return {
            "statusCode": 200,
            "body": json.dumps({"status": "success", "message": f"Аниме '{anime_name}' добавлено в группу '{group_name}'."})
        }
    else:
        return {
            "statusCode": 404,
            "body": json.dumps({"status": "error", "message": f"Аниме с названием '{anime_title}' не найдено."})
        }
def is_user_in_group(group_name, user_id):
    # Чтение текущего файла groups.csv
    groups_df = pd.read_csv('groups.csv')
    print(f"Groups DataFrame: {groups_df}")  # Отладочное сообщение

    # Проверка, существует ли группа с таким именем
    group_row = groups_df[groups_df['name'] == group_name]
    if group_row.empty:
        print(f"Группа '{group_name}' не существует.")
        return False

    group_id = group_row['group_id'].values[0]
    print(f"Group ID: {group_id}")  # Отладочное сообщение

    # Чтение текущего файла group_members.csv
    members_df = pd.read_csv('group_members.csv')
    print(f"Members DataFrame: {members_df}")  # Отладочное сообщение

    # Проверка, является ли пользователь участником группы
    user_in_group = ((members_df['group_id'] == group_id) & (members_df['user_id'] == user_id)).any()
    print(f"User in group: {user_in_group}")  # Отладочное сообщение

    if user_in_group:
        return True
    else:
        print(f"Пользователь '{user_id}' не является участником группы '{group_name}'.")
        return False