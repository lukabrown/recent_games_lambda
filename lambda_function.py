import json
import os
import requests
import boto3
from datetime import date

USER_ID = os.environ['user_id']
API_KEY = os.environ['api_key']
BUCKET = os.environ['bucket']
STEAM_GAMES_URL = f"http://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/?key={API_KEY}&steamid={USER_ID}&include_appinfo=true"
STEAM_STORE_URL = "https://api.steampowered.com/IStoreBrowseService/GetItems/v1/"

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
            response = send_steam_call(STEAM_GAMES_URL)

            if response.get('statusCode') is not None:
                return response

            data = {"games": []}
            for i in range(response['response']['total_count']):
                name = response['response']['games'][i]['name']
                app_id = response['response']['games'][i]['appid']
                payload = {
                    "ids": [{"appid": app_id}],
                    "context": {
                        "language": "english",
                        "country_code": "US"
                    },
                    "data_request": {
                        "include_assets": True
                    }
                }

                r = send_steam_call(STEAM_STORE_URL, params={"input_json": json.dumps(payload)})
                try:
                    remainder = r['response']['store_items'][0]['assets']['header_2x']
                except (KeyError):
                    remainder = r['response']['store_items'][0]['assets']['header']

                url = f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{app_id}/{remainder}"
                store_url = f"https://store.steampowered.com/app/{app_id}"
                data["games"].append({'name': name, 'url': url, 'storeUrl': store_url})

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

def send_steam_call(url, params=None):
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps("Internal Server Error. Steam call failed.")
        }
