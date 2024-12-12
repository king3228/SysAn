import boto3
import os
import pandas as pd
from datetime import datetime, timezone
import uuid
from dotenv import load_dotenv

BUCKET_NAME = 'bucket-first'

def get_s3_client():
    """Созданный клиент boto3 для коннекта к Yandex Cloud Object Storage."""
    load_dotenv('/Users/p.miroshin/Documents/Masters/2d_year/keys.env')
    session = boto3.session.Session()
    return session.client(
        service_name='s3',
        endpoint_url='https://storage.yandexcloud.net',
        region_name='ru-central1',
        aws_access_key_id=os.environ.get('ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('ACCESS_SECRET_KEY')
    )

def read_table_from_s3_csv(file_key):
    s3 = get_s3_client()
    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=file_key)
        df = pd.read_csv(response['Body'])
        return df
    except s3.exceptions.NoSuchKey:
        return pd.DataFrame()

def write_table_to_s3_csv(df, file_key):
    s3 = get_s3_client()
    csv_buffer = df.to_csv(index=False)
    s3.put_object(Bucket=BUCKET_NAME, Key=file_key, Body=csv_buffer)

def get_old_timestamp():
    return datetime(1970, 1, 1, tzinfo=timezone.utc)

def get_current_timestamp():
    return datetime.now(timezone.utc)

def check_user_exists(chat_id):
    users_df = read_table_from_s3_csv('users.csv')
    user_record = users_df[users_df['chat_id'] == chat_id]
    return user_record if not user_record.empty else None

def add_user(chat_id):
    users_df = read_table_from_s3_csv('users.csv')
    last_updated = get_old_timestamp().isoformat()
    new_user = pd.DataFrame([{
        'chat_id': chat_id,
        'shikimori_username': None,
        'last_updated': last_updated
    }])

    # Используем pd.concat вместо append
    users_df = pd.concat([users_df, new_user], ignore_index=True)
    write_table_to_s3_csv(users_df, 'users.csv')

def update_last_updated(chat_id):
    users_df = read_table_from_s3_csv('users.csv')
    last_updated = get_current_timestamp().isoformat()
    users_df.loc[users_df['chat_id'] == chat_id, 'last_updated'] = last_updated
    write_table_to_s3_csv(users_df, 'users.csv')

def add_shiki_to_user(chat_id, shiki_username):
    users_df = read_table_from_s3_csv('users.csv')
    users_df.loc[users_df['chat_id'] == chat_id, 'shikimori_username'] = shiki_username
    write_table_to_s3_csv(users_df, 'users.csv')

def load_user_anime_list(chat_id, user_anime_list):
    user_anime_df = read_table_from_s3_csv('user_anime.csv')
    anime_df = read_table_from_s3_csv('anime.csv')

    for anime in user_anime_list:
        target = anime['anime']
        genres = ', '.join([genre['name'] for genre in target['genres']])

        # Обработка данных anime
        if (anime_df['anime_id'] == target['id']).any():
            # Обновляем существующее аниме
            anime_df.loc[anime_df['anime_id'] == target['id'], ['title', 'average_score', 'genres', 'episode_duration', 'episode_count', 'poster_url']] = \
                [target['name'], target['score'], genres, target['episodes'], target['episodes'], target['poster']['originalUrl']]
        else:
            # Добавляем новое аниме, если его нет
            new_anime = pd.DataFrame([{
                'anime_id': target['id'],
                'title': target['name'],
                'average_score': target['score'],
                'genres': genres,
                'type': 'Anime',
                'episode_duration': target['episodes'],
                'episode_count': target['episodes'],
                'poster_url': target['poster']['originalUrl']
            }])
            anime_df = pd.concat([anime_df, new_anime], ignore_index=True)

        # Обработка данных пользователя
        exists_user_anime = ((user_anime_df['chat_id'] == chat_id) & (user_anime_df['anime_id'] == target['id'])).any()
        if exists_user_anime:
            # Обновляем информацию о пользователе для данного аниме
            user_anime_df.loc[(user_anime_df['chat_id'] == chat_id) & (user_anime_df['anime_id'] == target['id']), ['status', 'user_score']] = \
                [anime['status'], anime.get('score', 0)]
        else:
            # Добавляем новую запись пользователя anime, если её нет
            new_user_anime = pd.DataFrame([{
                'user_anime_id': str(uuid.uuid4()),
                'chat_id': chat_id,
                'anime_id': target['id'],
                'status': anime['status'],
                'user_score': anime.get('score', 0)
            }])
            user_anime_df = pd.concat([user_anime_df, new_user_anime], ignore_index=True)

    write_table_to_s3_csv(anime_df, 'anime.csv')
    write_table_to_s3_csv(user_anime_df, 'user_anime.csv')

def get_context_data(chat_id):
    user_anime_df = read_table_from_s3_csv('user_anime.csv')
    anime_df = read_table_from_s3_csv('anime.csv')

    # Фильтрация данных по chat_id и 'finished' статусу
    user_anime_finished = user_anime_df[
        (user_anime_df['chat_id'] == chat_id) &
        (user_anime_df['status'] == 'finished')
    ]

    # Подключение `anime_df` для получения дополнительной информации
    merged_df = pd.merge(user_anime_finished, anime_df, how='inner', on='anime_id')

    # Использование try-except для обработки потенциальных ошибок в векторе `genres`
    try:
        all_genres = merged_df['genres'].dropna().str.split(', ').explode()
        top_genre = all_genres.value_counts().idxmax() if not all_genres.empty else None
    except Exception:
        top_genre = None

    # Использование try-except для обработки потенциальных ошибок в медиане
    try:
        median_episodes = merged_df['episode_count'].dropna().median() if not merged_df.empty else None
    except Exception:
        median_episodes = None

    # Использование try-except для проверки top и bottom titles
    try:
        top_titles = merged_df.nlargest(3, 'user_score').dropna(subset=['title'])['title'].tolist() if not merged_df.empty else []
    except Exception:
        top_titles = []

    try:
        bottom_titles = merged_df.nsmallest(3, 'user_score').dropna(subset=['title'])['title'].tolist() if not merged_df.empty else []
    except Exception:
        bottom_titles = []

    context_data = {
        'top_genre': top_genre,
        'median_episodes': median_episodes,
        'top_titles': top_titles,
        'bottom_titles': bottom_titles
    }

    return context_data

def generate_id():
    return str(uuid.uuid4())