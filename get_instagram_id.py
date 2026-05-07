import requests
import os
from dotenv import load_dotenv

load_dotenv('/home/kenta_kamijyo/.env')

page_id = '1085583224645058'
page_token = 'EAAQrKpZAdzNMBRT9OHVuUhlMjZBcByXHx5iV0OyLLSXEzF06bdl6eaWzpc6krRibpOvAaXqyMU7Oqneu3ZBeOqkXvfTzXZBIuNP3O7eo3g7NaOTRHncWZA4jwPKCoRqFOPxiIPndrmcYqEjS0KPVdMDjKZCX5jrjl0WOrkqKYlLEaVJDV2eKIZB504y4NaGI19fRG8veHHNegXQkR1ZCxrkwTawloYt4C2RlBWZBCY7ZBPaM6YM12vRlSMGNFZBZBu2JzwZDZD'

r = requests.get(
    f'https://graph.facebook.com/v19.0/{page_id}',
    params={
        'fields': 'instagram_business_account',
        'access_token': page_token
    }
)
print(r.json())
