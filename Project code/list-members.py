import os
import pandas as pd
from datetime import datetime, timezone
import uuid
import requests
import json
from object_storage import *

def list_members(event, context):
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

        # Чтение текущего файла group_members.csv
        members_df = read_table_from_s3_csv('group_members.csv')
        print(f"Members DataFrame: {members_df}")  # Отладочное сообщение

        # Получение списка участников группы
        group_members = members_df[members_df['group_id'] == group_id]
        if group_members.empty:
            return {
                "statusCode": 404,
                "body": json.dumps({"status": "error", "message": f"Группа '{group_name}' не существует или у нее нет участников."})
            }

        return {
            "statusCode": 200,
            "body": json.dumps({"status": "success", "members": group_members['user_id'].tolist()})
        }
    except Exception as e:
        print(f"Ошибка при получении списка участников группы: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"status": "error", "message": f"Произошла ошибка при получении списка участников группы '{group_name}'."})
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