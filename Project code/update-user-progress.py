import os
import pandas as pd
from datetime import datetime, timezone
import uuid
import requests
import json
from object_storage import *

def update_user_progress(event, context):
    data = json.loads(event['body'])
    group_name = data.get('group_name')
    user_id = data.get('user_id')

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

    # Получение списка общих аниме в группе
    group_anime = anime_df[anime_df['group_id'] == group_id]
    if group_anime.empty:
        return {
            "statusCode": 404,
            "body": json.dumps({"status": "error", "message": f"Группа '{group_name}' не имеет общих аниме."})
        }

    # Получение информации о просмотренных сериях аниме пользователем
    user_anime_list = get_user_anime_list(user_id)
    if not user_anime_list:
        return {
            "statusCode": 404,
            "body": json.dumps({"status": "error", "message": f"Пользователь '{user_id}' не имеет прогресса по аниме."})
        }

    # Создание словаря для хранения прогресса каждого аниме
    anime_progress = {int(anime['anime']['id']): anime['episodes'] for anime in user_anime_list}

    # Чтение текущего файла user_group_progress.csv
    progress_df = read_table_from_s3_csv('user_group_progress.csv')

    # Обновление прогресса для каждого аниме в группе
    for _, anime in group_anime.iterrows():
        anime_id = anime['anime_id']
        episodes_watched = anime_progress.get(int(anime_id), 0)

        # Проверка, существует ли запись для данного пользователя и аниме
        progress_row = progress_df[(progress_df['user_id'] == user_id) & (progress_df['anime_id'] == anime_id)]
        if progress_row.empty:
            # Добавление новой записи
            new_progress = pd.DataFrame([{'user_group_progress_id': str(uuid.uuid4()), 'user_id': user_id, 'group_id': group_id, 'anime_id': anime_id, 'progress': episodes_watched}])
            progress_df = pd.concat([progress_df, new_progress], ignore_index=True)
        else:
            # Обновление существующей записи
            progress_df.loc[progress_row.index, 'progress'] = episodes_watched

    # Сохранение обновленного DataFrame в CSV файл
    write_table_to_s3_csv(progress_df, 'user_group_progress.csv')

    return {
        "statusCode": 200,
        "body": json.dumps({"status": "success", "message": f"Прогресс пользователя '{user_id}' по всем аниме в группе '{group_name}' обновлен."})
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