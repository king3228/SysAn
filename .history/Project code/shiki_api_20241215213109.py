import requests
import time
import json

# URL для GraphQL API Shikimori
GRAPHQL_ENDPOINT = 'https://shikimori.one/api/graphql'

# Заголовки запроса с User-Agent: Api Test
HEADERS = {
    "Accept-Encoding": "gzip, deflate, br",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Connection": "keep-alive",
    "DNT": "1",
    "Origin": "https://shikimori.one",
    "User-Agent": "Api Test"  # User-Agent
}

def graphql_request(query, variables, headers=HEADERS):
    """
    Выполняет GraphQL запрос и возвращает ответ JSON.
    """
    payload = {
        "query": query,
        "variables": variables
    }
    
    try:
        response = requests.post(GRAPHQL_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()  # Исключение в случае HTTP ошибок
        return response.json()
    except requests.RequestException as e:
        print(f"Error performing GraphQL request: {e}")
        return None

def get_user_anime_list(user_shiki_id):
    """
    Получает аниме-лист пользователя по его Shikimori ID.
    """
    query = """
    query($targetType: UserRateTargetTypeEnum!, $userId: ID, $limit: Int, $page: Int){
      userRates(targetType: $targetType, userId: $userId, limit: $limit, page: $page) {
        episodes
        anime {
          id
          status
          name
          score
          airedOn {
            year
          }
          genres {
            name
          }
          episodes
          poster {
            mainUrl
          }
          url
        }
        status
        score
      }
    }
    """

    user_anime_data = []
    page = 1
    limit = 50  # Оптимальный лимит для обхода ограничений API

    while True:
        variables = {
            'targetType': 'Anime',
            'userId': user_shiki_id,
            'limit': limit,
            'page': page
        }
        response = graphql_request(query, variables)

        if not response or 'data' not in response or not response['data']['userRates']:
            break  # Останавливаемся, если данных больше нет

        user_anime_data.extend(response['data']['userRates'])
        page += 1
        time.sleep(1)  # Пауза между запросами для снижения нагрузки на API и избежания банов

    return user_anime_data

def get_anime_by_title(title):
    """
    Получает информацию об аниме по его названию.
    """
    query = """
    query($search: String!, $limit: Int) {
      animes(search: $search, limit: $limit) {
        id
        name
        score
        kind
        episodes
        duration
        season
        url
        genres {
          name
        }
        poster {
          mainUrl
        }
        description
      }
    }
    """
    variables = {
        'search': title,
        'limit': 1
    }

    response = graphql_request(query, variables)

    if response and 'data' in response and response['data']['animes']:
        return response['data']['animes'][0]  # Возвращаем первый найденный результат

    print(f"Anime with title '{title}' not found in Shikimori.")
    return None

