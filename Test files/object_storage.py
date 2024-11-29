import json
import time
import requests
import os
import boto3

session = boto3.session.Session()
s3 = session.client(
    service_name='s3',
    endpoint_url='https://storage.yandexcloud.net',
    region_name='ru-central1',
    aws_access_key_id=os.environ.get('ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('ACCESS_SECRET_KEY')
)

BUCKET_NAME = 'bucket-first'
FILE_KEY = 'ping_requests.json'
BOT_TOKEN = os.environ.get('TMP_TELEGRAM_TOKEN')

def check_and_send_messages(event, context):
    current_time = time.time()
    ping_requests = read_ping_requests()
    updated_requests = []

    for request in ping_requests:
        if current_time >= request['trigger_time']:
            send_message(request)
        else:
            updated_requests.append(request)

    write_ping_requests(updated_requests)

def send_message(request):
    chat_id = request['chat_id']
    time_interval = request['time_interval']

    if request.get('photo_url'):
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        data = {
            'chat_id': chat_id,
            'caption': f"Прошло {time_interval} минут!",
            'reply_to_message_id': request['message_id'],
            'photo': request['photo_url']
        }
    else:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': f"Прошло {time_interval} минут!",
            'reply_to_message_id': request['message_id']
        }

    requests.post(url, data=data)

def read_ping_requests():
    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=FILE_KEY)
        return json.loads(response['Body'].read().decode('utf-8'))
    except s3.exceptions.NoSuchKey:
        return []

def write_ping_requests(ping_requests):
    data = json.dumps(ping_requests, ensure_ascii=False)
    s3.put_object(Bucket=BUCKET_NAME, Key=FILE_KEY, Body=data)