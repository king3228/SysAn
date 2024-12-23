import os
import pandas as pd
from datetime import datetime, timezone
import uuid
import requests
import json
from object_storage import *

def list_group_anime(event, context):
    group_name = event['queryStringParameters']['group_name']
    user_id = event['queryStringParameters']['user_id']

    # Приведение user_id к int, если это необходимо
    if isinstance(user_id, str):
        user_id = int(user_id)

    if not is_user_in_group(group_name, user_id):
        return {
            "statusCode": 403,
            "body": json.dumps({"status": "error", "message": f"Пользователь '{user_id}' не является участником группы '{group_name}'."})
        }

    try:
        # Чтение текущего файла groups.csv
        groups_df = read_table_from_s3_csv('groups.csv')
        print(f"Groups DataFrame: {groups_df}")  # Отладочное сообщение

        # Проверка, существует ли группа с таким именем
        group_row = groups_df[groups_df['name'] == group_name]
        if group_row.empty:
            return {
                "statusCode": 404,
                "body": json.dumps({"status": "error", "message": f"Группа '{group_name}' не существует."})
            }

        group_id = group_row['group_id'].values[0]
        print(f"Group ID: {group_id}")  # Отладочное сообщение

        # Чтение текущего файла group_watched_anime.csv
        anime_df = read_table_from_s3_csv('group_watched_anime.csv')
        print(f"Anime DataFrame: {anime_df}")  # Отладочное сообщение

        # Получение списка общих аниме в группе
        group_anime = anime_df[anime_df['group_id'] == group_id]
        if group_anime.empty:
            return {
                "statusCode": 404,
                "body": json.dumps({"status": "error", "message": f"Группа '{group_name}' не существует или у нее нет общих аниме."})
            }

        return {
            "statusCode": 200,
            "body": json.dumps({"status": "success", "anime": group_anime['anime_name'].tolist()})
        }
    except Exception as e:
        print(f"Ошибка при получении списка аниме в группе: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"status": "error", "message": f"Произошла ошибка при получении списка аниме в группе '{group_name}'."})
        }