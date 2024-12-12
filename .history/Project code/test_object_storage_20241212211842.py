import pytest
import os
import boto3
from dotenv import load_dotenv
import pandas as pd
from io import StringIO
from datetime import datetime, timezone
from object_storage import (  # Ваши функции находятся в модуле object_storage
    read_table_from_s3_csv,
    write_table_to_s3_csv,
    get_old_timestamp,
    get_current_timestamp,
    check_user_exists,
    add_user,
    update_last_updated,
    add_shiki_to_user,
    load_user_anime_list,
    get_context_data,
    generate_id
)


load_dotenv('/Users/p.miroshin/Documents/Masters/2d_year/keys.env')

BUCKET_NAME = 'bucket-first'

# Настраиваем клиент для Yandex Cloud Object Storage
session = boto3.session.Session()
s3 = session.client(
    service_name='s3',
    endpoint_url='https://storage.yandexcloud.net',
    region_name='ru-central1',
    aws_access_key_id=os.environ.get('ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('ACCESS_SECRET_KEY')
)

@pytest.fixture(scope='function')
def setup_s3_bucket():
    # Загружаем начальные данные перед каждым тестом
    print(aws_access_key_id)
    users_data = """chat_id,shikimori_username,last_updated\n1,shiki_user,1970-01-01T00:00:00+00:00"""
    users_df = pd.read_csv(StringIO(users_data))
    users_csv_buffer = StringIO()
    users_df.to_csv(users_csv_buffer, index=False)
    s3.put_object(Bucket=BUCKET_NAME, Key='users.csv', Body=users_csv_buffer.getvalue())

    anime_data = """anime_id,title\n1,Naruto"""
    anime_df = pd.read_csv(StringIO(anime_data))
    anime_csv_buffer = StringIO()
    anime_df.to_csv(anime_csv_buffer, index=False)
    s3.put_object(Bucket=BUCKET_NAME, Key='anime.csv', Body=anime_csv_buffer.getvalue())

    user_anime_data = """user_anime_id,chat_id,anime_id,status,user_score\n1,1,1,finished,10"""
    user_anime_df = pd.read_csv(StringIO(user_anime_data))
    user_anime_csv_buffer = StringIO()
    user_anime_df.to_csv(user_anime_csv_buffer, index=False)
    s3.put_object(Bucket=BUCKET_NAME, Key='user_anime.csv', Body=user_anime_csv_buffer.getvalue())

def test_read_table_from_s3_csv(setup_s3_bucket):
    df = read_table_from_s3_csv('users.csv')
    assert not df.empty
    assert 'chat_id' in df.columns

def test_write_table_to_s3_csv(setup_s3_bucket):
    df = pd.DataFrame({'chat_id': [2], 'shikimori_username': ['test_user'], 'last_updated': [get_old_timestamp().isoformat()]})
    write_table_to_s3_csv(df, 'users.csv')
    
    result_df = read_table_from_s3_csv('users.csv')
    assert len(result_df) == 2
    assert df.iloc[1]['chat_id'] == 2

def test_get_old_timestamp():
    assert get_old_timestamp() == datetime(1970, 1, 1, tzinfo=timezone.utc)

def test_get_current_timestamp():
    timestamp = get_current_timestamp()
    assert isinstance(timestamp, datetime)

def test_check_user_exists(setup_s3_bucket):
    user_record = check_user_exists(1)
    assert user_record is not None

def test_add_user(setup_s3_bucket):
    add_user(2)
    users_df = read_table_from_s3_csv('users.csv')
    assert len(users_df) == 2
    assert not users_df[users_df['chat_id'] == 2].empty

def test_update_last_updated(setup_s3_bucket):
    update_last_updated(1)
    users_df = read_table_from_s3_csv('users.csv')
    assert datetime.fromisoformat(users_df[users_df['chat_id'] == 1]['last_updated'].values[0]) > get_old_timestamp()

def test_add_shiki_to_user(setup_s3_bucket):
    add_shiki_to_user(1, 'new_shiki_user')
    users_df = read_table_from_s3_csv('users.csv')
    assert users_df[users_df['chat_id'] == 1]['shikimori_username'].values[0] == 'new_shiki_user'

def test_load_user_anime_list(setup_s3_bucket):
    load_user_anime_list(1, [{'anime': {'id': 2, 'name': 'One Piece', 'score': 9, 'genres': [{'name': 'Adventure'}], 'episodes': 24, 'poster': {'originalUrl': 'http://example.com'}}, 'status': 'watching', 'score': 9}])
    anime_df = read_table_from_s3_csv('anime.csv')
    user_anime_df = read_table_from_s3_csv('user_anime.csv')
    
    assert len(anime_df) == 2
    assert len(user_anime_df) == 2

def test_get_context_data(setup_s3_bucket):
    context_data = get_context_data(1)
    # Подставьте корректные значения топа жанров и медианы эпизодов
    assert len(context_data['top_titles']) > 0