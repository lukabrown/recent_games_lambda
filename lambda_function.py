import json
import os
import requests

USER_ID = os.environ['user_id']
API_KEY = os.environ['api_key']

def lambda_handler(event, context):
    url = f"http://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/?key={API_KEY}&steamid={USER_ID}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error: {e}")
        return {
                'statusCode': 500,
                'body': json.dumps("Internal Error.")
            }
