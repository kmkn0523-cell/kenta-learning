import requests
import os
from dotenv import load_dotenv

load_dotenv('/home/kenta_kamijyo/.env')

page_id = '1085583224645058'
token = os.getenv('INSTAGRAM_ACCESS_TOKEN')

r = requests.get(
    f'https://graph.facebook.com/v19.0/{page_id}',
    params={
        'fields': 'instagram_business_account',
        'access_token': token
    }
)
print(r.json())
