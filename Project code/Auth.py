import requests
#%%
def get_shikimori_user_id(username):
    url = "https://shikimori.one/api/users"
    params = {
        'search': username
    }
    headers = {
        'User-Agent': 'Api Test'
    }
    response = requests.get(url, params=params, headers=headers)

    response.raise_for_status()

    users = response.json()

    if users:
        return users[0]['id']
    return None