import json
import os
import requests
import boto3
from datetime import date

USER_ID = os.environ['user_id']
API_KEY = os.environ['api_key']
BUCKET = os.environ['bucket']
STEAM_URL = f"http://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/?key={API_KEY}&steamid={USER_ID}"

S3 = boto3.client("s3")

def lambda_handler(event, context):
    try:
        date_str = date.today().strftime("%Y-%m-%d")
        key = f"{date_str}.txt"

        try:
            response = S3.get_object(
                Bucket=BUCKET,
                Key=key
            )
            return json.loads(response["Body"].read().decode())
        except S3.exceptions.NoSuchKey:
            print('No object found')
            response = send_steam_call()

            if response.get('statusCode') is not None:
                return response

            data = {"games": []}
            for i in range(response['response']['total_count']):
                name = response['response']['games'][i]['name']
                url = f"https://steamcdn-a.akamaihd.net/steam/apps/{response['response']['games'][i]['appid']}/library_600x900_2x.jpg"
                data["games"].append({'name': name, 'url': url})

            S3.put_object(
                Bucket=BUCKET,
                Key=key,
                Body=json.dumps(data).encode()
            )

            return data
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps("Internal Server Error.")
        }

def send_steam_call():
    try:
        response = requests.get(STEAM_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps("Internal Server Error.")
        }
