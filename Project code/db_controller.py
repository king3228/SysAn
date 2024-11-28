import ydb
import pandas as pd
import json
import uuid
from datetime import datetime, timezone

def connect_db():
    IAM = ''
    driver_config = ydb.DriverConfig(
        endpoint='grpcs://ydb.serverless.yandexcloud.net:2135',
        database='/ru-central1/b1gsde16rgc0mhkhj1t4/etnjgop9305nqltdo5ob',
        credentials=ydb.credentials.AccessTokenCredentials(f'Bearer {IAM}')
    )
    driver = ydb.Driver(driver_config)
    driver.wait(timeout=5)
    return driver

def get_old_timestamp():
    return datetime(1970, 1, 1, tzinfo=timezone.utc)

def get_current_timestamp():
    return datetime.now(timezone.utc)

def check_user_exists(driver, chat_id):
    session = driver.table_client.session().create()
    query = f"""
    SELECT shikimori_username, last_updated
    FROM users
    WHERE chat_id = {chat_id}
    """
    result_set = session.transaction(ydb.SerializableReadWrite()).execute(query, commit_tx=True)
    return result_set[0].rows if result_set else None

def add_user(driver, chat_id):
    session = driver.table_client.session().create()
    last_updated = get_old_timestamp().strftime('%Y-%m-%dT%H:%M:%SZ')
    query = f"""
    INSERT INTO users (chat_id, shikimori_username, last_updated)
    VALUES ({chat_id}, NULL, CAST('{last_updated}' AS TIMESTAMP))
    """
    session.transaction(ydb.SerializableReadWrite()).execute(query, commit_tx=True)

def update_last_updated(driver, chat_id):
    session = driver.table_client.session().create()
    last_updated = get_current_timestamp().strftime('%Y-%m-%dT%H:%M:%SZ')
    query = f"""
    UPDATE users
    SET last_updated = CAST('{last_updated}' AS TIMESTAMP)
    WHERE chat_id = {chat_id}
    """
    session.transaction(ydb.SerializableReadWrite()).execute(query, commit_tx=True)

def add_shiki_to_user(driver, chat_id, shiki_username):
    session = driver.table_client.session().create()
    query = f"""
    UPDATE users
    SET shikimori_username = '{shiki_username}'
    WHERE chat_id = {chat_id}
    """
    session.transaction(ydb.SerializableReadWrite()).execute(
        query,
        commit_tx=True
    )

def get_context_data(driver, chat_id):
    session = driver.table_client.session().create()
    

    query_top_genre = f"""
    SELECT genre
    FROM (
    SELECT
        json_value(uad.detail, '$') AS genre, -- Извлекаем значение из JSON
        COUNT(*) AS count
    FROM
        user_anime ua
    LEFT JOIN
        anime a ON ua.anime_id = a.anime_id
    LEFT JOIN
        UNNEST(json_query_array(a.geners, '$')) AS uad(detail) ON true -- Преобразуем JSON в таблицу без алиасов
    WHERE
        ua.chat_id = {chat_id} AND ua.status = 'finished'
    GROUP BY
        genre
    ORDER BY
        count DESC
    LIMIT 1
    ) t
    """

    query_median_episodes = f"""
    SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY a.episode_count) AS median_episodes
    FROM user_anime ua
    JOIN anime a ON ua.anime_id = a.anime_id
    WHERE ua.chat_id = {chat_id} AND ua.status = 'finished'
    """

    query_top_bottom_titles = f"""
    (SELECT array_agg(a.title ORDER BY ua.user_score DESC LIMIT 3) AS top_titles
    FROM user_anime ua
    JOIN anime a ON ua.anime_id = a.anime_id
    WHERE ua.chat_id = {chat_id} AND ua.status = 'finished'),
    (SELECT array_agg(a.title ORDER BY ua.user_score ASC LIMIT 3) AS bottom_titles
    FROM user_anime ua
    JOIN anime a ON ua.anime_id = a.anime_id
    WHERE ua.chat_id = {chat_id} AND ua.status = 'finished')
    """

    # Выполнение запросов
    top_genre_result = session.transaction(ydb.SerializableReadWrite()).execute(query_top_genre)
    median_episodes_result = session.transaction(ydb.SerializableReadWrite()).execute(query_median_episodes)
    top_bottom_titles_result = session.transaction(ydb.SerializableReadWrite()).execute(query_top_bottom_titles)

    context_data = {
        'top_genre': top_genre_result[0].rows[0].genre,
        'median_episodes': median_episodes_result[0].rows[0].median_episodes,
        'top_titles': top_bottom_titles_result[0].rows[0].top_titles,
        'bottom_titles': top_bottom_titles_result[0].rows[0].bottom_titles
    }

    return context_data

import pandas as pd
import ydb
import json
from datetime import datetime


def escape_sql(value):
    """Экранировать строковое значение для предотвращения SQL-инъекций."""
    if isinstance(value, str):
        return value.replace("'", "''")
    return value

def load_user_anime_list(driver, chat_id, user_anime_list):
    with ydb.SessionPool(driver) as pool:
        session = pool.acquire()
        try:
            # Начинаем транзакцию
            transaction = session.transaction(ydb.SerializableReadWrite()).begin()

            for anime in user_anime_list:
                target = anime['anime']
                genres = [genre['name'] for genre in target['genres']]
                genres_json = json.dumps(genres)
                user_anime_id = str(uuid.uuid4())

                # Выполняем проверку без блокировок
                check_anime_query = f"SELECT anime_id FROM anime WHERE anime_id = {target['id']}"
                anime_exists = transaction.execute(check_anime_query)[0].rows

                check_user_anime_query = f"SELECT user_anime_id FROM user_anime WHERE user_anime_id = '{user_anime_id}'"
                user_anime_exists = transaction.execute(check_user_anime_query)[0].rows

                if not anime_exists:
                    anime_query = f"""
                    INSERT INTO anime (anime_id, title, average_score, geners, type, episode_duration, episode_count, poster_url)
                    VALUES (
                        {target['id']},
                        '{escape_sql(target['name'])}',
                        {target['score']},
                        '{escape_sql(genres_json)}',
                        'Anime',
                        {target['episodes']},
                        {target['episodes']},
                        '{escape_sql(target['poster']['originalUrl'])}'
                    )
                    """
                    transaction.execute(anime_query)

                if not user_anime_exists:
                    user_anime_query = f"""
                    INSERT INTO user_anime (user_anime_id, chat_id, anime_id, status, user_score)
                    VALUES (
                        '{user_anime_id}',
                        {chat_id},
                        {target['id']},
                        '{escape_sql(anime['status'])}',
                        {anime.get('score', 0)}
                    )
                    """
                    transaction.execute(user_anime_query)

            # Коммитим транзакцию в конце всех операций
            transaction.commit()

        except Exception as e:
            print(f"Error processing animes: {e}")
            transaction.rollback()

        finally:
            pool.release(session)

def generate_id():
    return str(uuid.uuid4())