'''
Photoshelter API integration for National Aquarium
'''
import json
import argparse
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


def upload_item_to_atbl(item):
    '''
    uploads the item data from search response -> Airtable
    '''



def search(token, cred):
    '''
    searches
    '''
    headers = {"content-type": "application/x-www-form-urlencoded",
               "X-PS-Api-Key": cred['api_key'],
               "X-PS-Auth-Token": token}
    params = {"media_type": "image", "org_id": "O0000e.jllXxQUoI"}
    response = requests.get("https://www.photoshelter.com/psapi/v4.0/search",
                            headers=headers, params=params)
    pprint(response.request.__dict__)
    for item in response.json()['data']:
        print(item)
        input("hey")


def get_library(token, cred):
    '''
    gets library? idk we'll fill this later
    '''
    headers = {"content-type": "application/x-www-form-urlencoded",
               "X-PS-Api-Key": cred['api_key'],
               "X-PS-Auth-Token": token}
    params = {"is_listed": "true"}
    response = requests.get("https://www.photoshelter.com/psapi/v4.0/library", headers=headers, params=params)
    pprint(response.request.__dict__)
    pprint(response.json())


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


def init():
    '''
    get some command line args and parse em
    '''
    parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mode", dest="mode",
                        choices=['download',
                                 'authenticate',
                                 'get_media_metadata',
                                 'get_library',
                                 'search'],
                        help="the mode of the script")
    parser.add_argument("--token", dest="token", default=None,
                        help="the token for this session, "\
                                "generated via authenticate mode")
    parser.add_argument("--media_id", dest="media_id", default=None,
                        help="the media ID (for testing)")
    args = parser.parse_args()
    return args


def main():
    '''
    do the thing
    '''
    args = init()
    cred = get_credentials()
    if args.mode == 'authenticate':
        authenticate()
    else:
        if not args.token:
            raise RuntimeError("you gotta get the token "\
                    "via authenticate mode")
        token = args.token
        if args.mode == "get_media_metadata":
            media_id = args.media_id
            get_media_md(media_id, token)
        elif args.mode == "get_library":
            get_library(token, cred)
        elif args.mode == "search":
            search(token, cred)


if __name__ == "__main__":
    main()
