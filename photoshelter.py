'''
Photoshelter API integration for National Aquarium
'''
import json
import argparse
import requests
import pathlib
from pprint import pprint
import airtable


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



def search(token, cred, page=1, per_page=10):
    '''
    searches
    '''
    headers = {"content-type": "application/x-www-form-urlencoded",
               "X-PS-Api-Key": cred['photoshelter']['api_key'],
               "X-PS-Auth-Token": token}
    params = {"media_type": "image", "org_id": "O0000e.jllXxQUoI",
              "per_page": per_page, "page": page}
    response = requests.get("https://www.photoshelter.com/psapi/v4.0/search",
                            headers=headers, params=params)
    return response


def iterate_response(response):
    '''
    moves through response by page, by item
    '''
    pprint(response.request.__dict__)
    '''
    print(len(response.json()['data']))
    print(response.json()['meta'])
    input("press any key to display results")
    '''
    for item in response.json()['data']:
        print(item)
        #atbl_rec = airtable.StillImageRecord().from_json(item)
        #atbl_rec.send()
        #print(atbl_rec.__dict__)
        input("hey")
    return


def manage_search(token, cred):
    '''
    manages the search and parsing of results
    '''
    total_results = 20
    per_page = 5
    total_pages = total_results / per_page
    page = 1
    while page <= total_pages:
        response = search(token, cred, page, per_page)
        iterate_response(response)
        page += 1


def get_library(token, cred):
    '''
    gets library? idk we'll fill this later
    '''
    headers = {"content-type": "application/x-www-form-urlencoded",
               "X-PS-Api-Key": cred['photoshelter']['api_key'],
               "X-PS-Auth-Token": token}
    params = {"is_listed": "true"}
    response = requests.get("https://www.photoshelter.com/psapi/v4.0/library", headers=headers, params=params)
    pprint(response.request.__dict__)
    pprint(response.json())


def download_media(media_id, token, cred):
    '''
    downloads media
    '''
    params = {"api_key": cred['photoshelter']['api_key'],
              "password": cred['photoshelter']['password'],
              "token": token,
              "download_filetype": "original"}
    headers = {"content-type": "application/x-www-form-urlencoded",
               "X-PS-Api-Key": cred['photoshelter']['api_key']}
    response = requests.get("https://www.photoshelter.com/psapi/v4.0/media/" + media_id + "/download", headers=headers, params=params)
    return response


def get_media_md(media_id, token, cred):
    '''
    gets metadata for a single media object
    '''
    params = {"api_key": cred['photoshelter']['api_key'],
              "include": "iptc"}
    headers = {"content-type": "application/x-www-form-urlencoded",
               "X-PS-Api-Key": cred['photoshelter']['api_key']}
    response = requests.get("https://www.photoshelter.com/psapi/v4.0/media/" + media_id, headers=headers)
    return response


def iterate_airtable(token, cred):
    '''
    iterates through airtable list
    '''
    atbl_conf = airtable.config()
    atbl_tbl = airtable.connect_one_table(atbl_conf['base_id'], "PhotoShelter Data", atbl_conf['api_key'])
    for atbl_rec_remote in atbl_tbl.all():
        atbl_rec_local = airtable.StillImageRecord().from_id(atbl_rec_remote['id'])
        #response = get_media_md(atbl_rec_local.media_id, token, cred)
        response = download_media(atbl_rec_local.media_id, token, cred)
        pprint(response.request.__dict__)
        pprint(response.json())
        #print(atbl_rec_local.__dict__)
        input("yo")


def authenticate():
    '''
    do the thing
    '''
    cred = get_credentials()
    params = {"api_key": cred['photoshelter']['api_key'],
              "password": cred['photoshelter']['password'],
              "email": cred['photoshelter']['email'],
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
                                 'search',
                                 'iterate_airtable'],
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
            manage_search(token, cred)
        elif args.mode == "iterate_airtable":
            iterate_airtable(token, cred)


if __name__ == "__main__":
    main()
