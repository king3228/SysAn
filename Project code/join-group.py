import os
import pandas as pd
from datetime import datetime, timezone
import uuid
import requests
import json
from object_storage import *

def join_group(event, context):
    print(event)
    data = json.loads(event.get('body', "{}"))
    group_name = data.get('group_name')
    user_id = data.get('user_id')

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

    # Проверка, является ли пользователь уже участником группы
    if ((members_df['group_id'] == group_id) & (members_df['user_id'] == user_id)).any():
        return {
            "statusCode": 400,
            "body": json.dumps({"status": "error", "message": f"Пользователь '{user_id}' уже в группе '{group_name}'."})
        }

    # Генерация нового group_member_id с использованием UUID
    new_group_member_id = str(uuid.uuid4())

    # Добавление нового участника
    new_member = pd.DataFrame([{'group_member_id': new_group_member_id, 'group_id': group_id, 'user_id': user_id, 'joined_at': datetime.now()}])
    members_df = pd.concat([members_df, new_member], ignore_index=True)
    write_table_to_s3_csv(members_df, 'group_members.csv')

    return {
        "statusCode": 200,
        "body": json.dumps({"status": "success", "message": f"Пользователь '{user_id}' присоединился к группе '{group_name}'."})
    }