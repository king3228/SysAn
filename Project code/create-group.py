import os
import pandas as pd
from datetime import datetime, timezone
import uuid
import requests
import json
from object_storage import *

def create_group(event, context):
    data = json.loads(event.get('body', "{}"))
    group_name = data.get('event')

    # Чтение текущего файла groups.csv
    groups_df = read_table_from_s3_csv('groups.csv')

    # Проверка, существует ли уже группа с таким именем
    if group_name in groups_df['name'].values:
        return {
            "statusCode": 400,
            "body": json.dumps({"status": "error", "message": f"Группа '{group_name}' уже существует."})
        }

    # Генерация нового group_id с использованием UUID
    new_group_id = str(uuid.uuid4())

    # Создание новой группы
    new_group = pd.DataFrame([{'group_id': new_group_id, 'name': group_name, 'created_at': datetime.now()}])
    groups_df = pd.concat([groups_df, new_group], ignore_index=True)
    write_table_to_s3_csv(groups_df, 'groups.csv')

    return {
        "statusCode": 201,
        "body": json.dumps({"status": "success", "message": f"Группа '{group_name}' с ID {new_group_id} создана."})
    }