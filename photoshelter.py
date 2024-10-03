'''
Photoshelter API integration for National Aquarium
'''
import json
import requests
import pathlib


def get_credentials():
    '''
    reads credential info from config file
    '''
    this_dirpath = pathlib.Path(__file__).parent.absolute()
    with open(this_dirpath / 'credentials.json', 'r') as config_file:
        credentials = json.load(config_file)
    return credentials


def main():
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
    print(response.__dict__)


if __name__ == "__main__":
    main()
