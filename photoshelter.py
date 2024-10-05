'''
Photoshelter API integration for National Aquarium
'''
import json
import requests
import pathlib
from pprint import pprint


def get_credentials():
    '''
    reads credential info from config file
    '''
    this_dirpath = pathlib.Path(__file__).parent.absolute()
    with open(this_dirpath / 'credentials.json', 'r') as config_file:
        credentials = json.load(config_file)
    return credentials


def get_media_md(media_id, token):
    '''
    gets metadata for a single media object
    '''
    cred = get_credentials()
    params = {"api_key": cred['api_key']}
    headers = {"content-type": "application/x-www-form-urlencoded",
               "X-PS-Api-Key": cred['api_key']}
    response = requests.get("https://www.photoshelter.com/psapi/v4.0/media/" + media_id + "/metadata", headers=headers)
    pprint(response.request.__dict__)
    pprint(response.__dict__)


def authenticate():
    '''
    do the thing
    '''
    cred = get_credentials()
    params = {"api_key": cred['api_key'],
              "password": cred['password'],
              "email": cred['email'],
              "mode": "token"}
    headers = {"content-type": "application/x-www-form-urlencoded"}
    base_url = "https://www.photoshelter.com/psapi/v4.0/authenticate"
    response = requests.post(base_url, headers=headers, params=params)
    print(response.url)
    print("click on that ^ url and copy the token it gives you")


def main():
    '''
    do the thing
    '''
    #authenticate()
    token = "ie6jWgGDDbz5uRkrRXMt"
    media_id = "I0000xmxpmIut5PM"
    get_media_md(media_id, token)

if __name__ == "__main__":
    main()
