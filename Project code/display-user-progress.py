import os
import pandas as pd
from datetime import datetime, timezone
import uuid
import requests
import json
from object_storage import *

def display_user_progress(event, context):
    group_name = event['queryStringParameters']['group_name']

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

    # Чтение текущего файла group_members.csv
    members_df = read_table_from_s3_csv('group_members.csv')

    # Чтение текущего файла group_watched_anime.csv
    anime_df = read_table_from_s3_csv('group_watched_anime.csv')

    # Чтение текущего файла user_group_progress.csv
    progress_df = read_table_from_s3_csv('user_group_progress.csv')

    # Получение списка участников группы
    group_members = members_df[members_df['group_id'] == group_id]

    # Получение списка общих аниме в группе
    group_anime = anime_df[anime_df['group_id'] == group_id]

    if group_members.empty or group_anime.empty:
        return {
            "statusCode": 404,
            "body": json.dumps({"status": "error", "message": f"Группа '{group_name}' не существует или у нее нет участников/аниме."})
        }

    # Вывод прогресса участников по общим аниме
    progress_data = {}
    for _, member in group_members.iterrows():
        user_id = member['user_id']
        user_progress = progress_df[(progress_df['user_id'] == user_id) & (progress_df['group_id'] == group_id)]

        if not user_progress.empty:
            progress_data[user_id] = {}
            for _, progress in user_progress.iterrows():
                anime_id = progress['anime_id']
                anime_row = anime_df[anime_df['anime_id'] == anime_id]
                if not anime_row.empty:
                    anime_name = anime_row['anime_name'].values[0]
                    episodes_watched = progress['progress']
                    progress_data[user_id][anime_name] = episodes_watched
                else:
                    progress_data[user_id][f"Аниме с ID '{anime_id}' не найдено в группе."] = 0
        else:
            progress_data[user_id] = "Пользователь не имеет прогресса по аниме в группе."

    return {
        "statusCode": 200,
        "body": json.dumps({"status": "success", "progress": progress_data})
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