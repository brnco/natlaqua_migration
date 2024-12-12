'''
Photoshelter API integration for National Aquarium
'''
import csv
import math
import json
import time
import shutil
import argparse
import requests
import pathlib
import subprocess
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


def get_session(token, cred):
    '''
    starts a session?
    '''
    headers = {"content-type": "application/x-www-form-urlencoded",
               "X-PS-Api-Key": cred['photoshelter']['api_key'],
               "X-PS-Auth-Token": token}
    params = {"token": token, "api_key": cred['photoshelter']['api_key'],
              "org_id": "O0000e.jllXxQUoI"}
    response = requests.post("https://www.photoshelter.com/psapi/v4.0/organization/authenticate",
                            headers=headers, params=params)
    return response


def find_in_csv(media_id):
    '''
    searches CSV of batch 1
    '''
    with open("PhotoShelter Data - batch1-CSV Delivery.csv", mode='r', newline='') as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            if media_id in row:
                return True
            else:
                continue
    return False


def search(token, cred, page=1, per_page=10):
    '''
    searches
    '''
    #"org_id": "O0000e.jllXxQUoI",
    headers = {"content-type": "application/x-www-form-urlencoded",
               "X-PS-Api-Key": cred['photoshelter']['api_key'],
               "X-PS-Auth-Token": token}
    params = {"media_type": "image,video,audio,doc", "org_id": "O0000e.jllXxQUoI",
              "mode": "library", "per_page": per_page, "page": page,
              "sort_by": "creation_time", "sort_direction": "descending",
              "token": token, "api_key": cred['photoshelter']['api_key']}
    response = requests.get("https://www.photoshelter.com/psapi/v4.0/search",
                            headers=headers, params=params)
    return response


def iterate_response(response):
    '''
    moves through response by page, by item
    '''
    #pprint(response.request.__dict__)
    #print(len(response.json()['data']))
    #print(response.json()['meta'])
    #input("press any key to display results")
    for item in response.json()['data']:
        #print(item)
        media_id = item['id']
        filename = item['attributes']['file_name']
        result = find_in_csv(media_id)
        if not result:
            atbl_rec = airtable.StillImageRecord()
            atbl_rec.media_id = media_id
            atbl_rec.file_name = filename
            atbl_rec.send()
        '''
        try:
            atbl_rec.send()
            #print(atbl_rec.__dict__)
            #input("hey")
        except RuntimeError as exc:
            time.sleep(0.5)
            try:
                atbl_rec.send()
            except Exception as exc:
                print(exc)
                raise RuntimeError("Airtable is being bad rn")
        '''
    return


def manage_search(token, cred):
    '''
    manages the search and parsing of results
    '''
    #actual total results is 165137
    #actually 165199
    #page 1019 had an error
    total_results = 165199
    per_page = 100
    total_pages = total_results / per_page
    page = 1
    #response = get_session(token, cred)
    #print(response.__dict__)
    #print(response.json()['meta'])
    #print(response.json()['data'])
    #input("oi")
    while page <= total_pages:
        print(f"working through page {page}")
        response = search(token, cred, page=page, per_page=per_page)
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


def save_file(url, headers, params, filename=None):
    '''
    actually saves the file to disk
    '''
    if not filename:
        filepath = url.split("/")[-2]
    else:
        print(f"actually saving the file: {filename}")
        filepath = pathlib.Path("/run/media/bec/LaCie/PhotoShelter-Data_batch2") / filename
    if filepath.exists():
        print("already exists...")
        return filepath
    with requests.get(url, stream=True, headers=headers, params=params) as res:
        with open(filepath, "wb") as file:
            shutil.copyfileobj(res.raw, file)
    if res.status_code != 200:
        print("did not download, probably")
        print(res.status_code)
        filepath.unlink()
    return filepath


def download_media(media_id, token, cred, filename=None):
    '''
    downloads media
    '''
    print("preparing download...")
    params = {"api_key": cred['photoshelter']['api_key'],
              "password": cred['photoshelter']['password'],
              "token": token,
              "download_filetype": "original"}
    headers = {"content-type": "application/x-www-form-urlencoded",
               "X-PS-Api-Key": cred['photoshelter']['api_key'],
               'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'}
    #response = requests.get("https://www.photoshelter.com/psapi/v4.0/media/" + media_id + "/download", headers=headers, params=params)
    url = "https://www.photoshelter.com/psapi/v4.0/media/" + media_id + "/download"
    filepath = save_file(url, headers, params, filename=filename)
    if filepath.exists():
        return filepath
    else:
        return False


def get_media_galleries(media_id, token, cred):
    '''
    gets the list of galleries for given media_id
    '''
    print("getting galleries for media...")
    params = {"api_key": cred['photoshelter']['api_key'],
              "password": cred['photoshelter']['password'],
              "Auth-Token": token,
              "mode": "library",
              "include": "gallery"}
    headers = {"content-type": "application/x-www-form-urlencoded",
               "X-PS-Api-Key": cred['photoshelter']['api_key']}
    '''
               "Cookie": "SSphotoshelter_com_mem=EReh2JutceibFJ4O1MCf; acs=qYvUUr.DgUMRsRiv9ZGXTqcvRSC5nU40u6iI4gA3tD0kPTg3gblPpWUWZMoI2J04R._WMvnkFxT5ylf.cD80V6UlM8jNU2t9iLavVUG8bMjv5hrNa88oNetXV0E6fxXOIM6piQRuZ_9CsGxg6RLtFIYpoX86DBc9iHv3RpWb4JW4SZiluA7w9FC1DMevxDSBj.cHm7XWo7laY0qgpoQwu8Ynp776G5cFGAVFNe3Zp.NhNTgazErxjUzHEIsUYro36PcJHPjRZfUbkQeo6362GrOzfUsbxEYJ5zW6jvGWgtqAnSpuA2uNejyg"}
    '''
    response = requests.get("https://www.photoshelter.com/psapi/v4.0/media/" + media_id + "/galleries",
                            headers=headers, params=params)
    print(response.__dict__)
    input("yo")
    return response


def get_media_md(media_id, token, cred):
    '''
    gets metadata for a single media object
    '''
    print("getting metadata for media...")
    params = {"api_key": cred['photoshelter']['api_key'],
              "includes": "iptc"}
    headers = {"content-type": "application/x-www-form-urlencoded",
               "X-PS-Api-Key": cred['photoshelter']['api_key']}
    response = requests.get("https://www.photoshelter.com/psapi/v4.0/media/" + media_id, headers=headers)
    return response


def parse_response_for_custom_fields(response):
    '''
    parses the response from get_available_metadata_fields
    prints just the custom fields
    == category: metadata
    '''
    for field in response.json()['data']:
        if field['category'] == 'metadata':
            pprint(field)


def get_media_metadata_custom(media_id, token, cred):
    '''
    gets every available metadata field from PhotoShelter
    '''
    print("getting custom metadata...")
    params = {"api_key": cred['photoshelter']['api_key'],
              "password": cred['photoshelter']['password'],
              "token": token}
    headers = {"content-type": "application/x-www-form-urlencoded",
               "X-PS-Api-Key": cred['photoshelter']['api_key']}
    response = requests.get("https://www.photoshelter.com/psapi/v4.0/media/" + media_id + "/custom-metadata",
                            params=params, headers=headers)
    return response


def iterate_airtable(token, cred, download=False):
    '''
    iterates through airtable list
    '''
    print("iterating through Airtable list")
    atbl_conf = airtable.config()
    atbl_tbl = airtable.connect_one_table(atbl_conf['base_id'],
                                          "PhotoShelter Data", atbl_conf['api_key'])
    print("getting all records...")
    for atbl_rec_remote in atbl_tbl.all(view="Everything"):
        atbl_rec_local = airtable.StillImageRecord().from_id(atbl_rec_remote['id'])
        print(f"working on: {atbl_rec_local.media_id}")
        filename = pathlib.Path(atbl_rec_local.file_name_disk)
        response = get_media_metadata_custom(atbl_rec_local.media_id, token, cred)
        try:
            atbl_rec_with_custom_md = airtable.StillImageRecord().from_json(response.json()['data'])
            atbl_rec_local.permit_number = atbl_rec_with_custom_md.permit_number
        except Exception:
            pass
        response = get_media_galleries(atbl_rec_local.media_id, token, cred)
        print(response.json())
        if response.json()['data']:
            atbl_rec_with_galleries = airtable.StillImageRecord().from_json(response.json()['data'])
            try:
                atbl_rec_local.galleries = atbl_rec_with_galleries.galleries
            except Exception:
                pass
        '''
        response = get_media_md(atbl_rec_local.media_id, token, cred)
        atbl_rec_with_custom_md = airtable.StillImageRecord().from_json(response.json()['data'])
        try:
            atbl_rec_local.license_expiration = atbl_rec_with_custom_md.license_expiration
        except Exception:
            continue
        '''
        if download:
            worked_yn = download_media(atbl_rec_local.media_id, token, cred, filename=filename)
            if worked_yn:
                atbl_rec_local.downloaded = "true"
            else:
                atbl_rec_local.downloaded = "false"
        atbl_rec_local.save()
        time.sleep(0.1)


def prep_batch(cred):
    '''
    prepares a batch
    '''
    print("preparing batch...")
    atbl_conf = airtable.config()
    atbl_tbl = airtable.connect_one_table(atbl_conf['base_id'],
                                          "PhotoShelter Data - batch1", atbl_conf['api_key'])
    print("getting all records...")
    for atbl_rec_remote in atbl_tbl.all(view="batch1 - alternates"):
        atbl_rec = airtable.StillImageRecord().from_id(atbl_rec_remote['id'])
        filename = atbl_rec.file_name_disk
        path_src = pathlib.Path("/run/media/bec/LaCie/PhotoShelter-Data_batch1")
        filepath_src = path_src / filename
        path_dest = pathlib.Path("/run/media/bec/LaCie/PhotoShelter-Data_batch0")
        filepath_dest = path_dest / filename
        atbl_rec.batch = "1"
        print(filename)
        if not filepath_src.exists():
            atbl_rec.pathproblem = "true"
            atbl_rec.send()
        else:
            cmd = ["mv", str(filepath_src), str(filepath_dest)]
            subprocess.run(cmd)
            atbl_rec.moved_to_0 = "true"
            atbl_rec.send()


def get_media_of_gallery(gallery_id, token, cred, page=1):
    '''
    gets the media in a single gallery
    '''
    params = {"api_key": cred['photoshelter']['api_key'],
              "Auth-Token": token,
              "password": cred['photoshelter']['password'],
              "token": token,
              "page": page, "per_page": 1000}
    headers = {"content-type": "application/x-www-form-urlencoded",
               "X-PS-Api-Key": cred['photoshelter']['api_key'],
               "X-PS-Auth-Token": token}
    i = 0
    while i < 10:
        try:
            response = requests.get("https://www.photoshelter.com/psapi/v4.0/galleries/" + gallery_id + "/children",
                                    params=params, headers=headers)
            pprint(response.json())
            response.raise_for_status()
            try:
                return response.json()['data']
            except:
                return None
        except requests.ConnectionError:
            time.sleep(0.5)
            i += 1
            continue
    print("maximum retries hit...")
    raise RuntimeError("I think there's a connection problem bro")


def get_media_in_galleries(token, cred):
    '''
    loops through airtable list of galleries
    gets list of media in each
    '''
    atbl_conf = airtable.config()
    atbl_tbl = airtable.connect_one_table(atbl_conf['base_id'],
                                          "PhotoShelter Galleries", atbl_conf['api_key'])
    for atbl_rec_gall in atbl_tbl.all(view="childs dont add up -- char limit"):
        gallery_id = atbl_rec_gall['fields']['gallery_id']
        child_count = atbl_rec_gall['fields']['Child Count - Total']
        total_pages = math.ceil(child_count / 1000)
        page = 1
        all_media = []
        while page <= total_pages:
            gallery_data = get_media_of_gallery(gallery_id, token, cred, page)
            for media in gallery_data:
                media_id = media['id']
                all_media.append(media_id)
            page += 1
        all_media_str = ", ".join(all_media)
        atbl_tbl.update(atbl_rec_gall['id'], {"Media": all_media_str})


def galleries_search(collection_id, token, cred):
    '''
    goes through the gallery list
    '''
    print("searching galleries...")
    params = {"api_key": cred['photoshelter']['api_key'],
              "Auth-Token": token,
              "password": cred['photoshelter']['password'],
              "token": token,
              "include": "permissions,parent,child-count",
              "sort_by": "name",
              "sort_direction": "descending",
              "parent": collection_id}
    headers = {"content-type": "application/x-www-form-urlencoded",
               "X-PS-Api-Key": cred['photoshelter']['api_key'],
               "X-PS-Auth-Token": token}
    response = requests.get("https://www.photoshelter.com/psapi/v4.0/galleries",
                            params=params, headers=headers)
    response.raise_for_status()
    try:
        foo = response.json()['data']
    except:
        return
    for gallery in response.json()['data']:
        pprint(gallery)
        atbl_rec_gall = airtable.GalleryRecord().from_json(gallery)
        pprint(atbl_rec_gall.__dict__)
        atbl_rec_gall.send()
        time.sleep(0.2)


def manage_galleries_search(token, cred):
    '''
    wraps galleries_search to search for every gallery in every collection in Airtable
    '''
    atbl_conf = airtable.config()
    atbl_tbl = airtable.connect_one_table(atbl_conf['base_id'],
                                          "PhotoShelter Collections", atbl_conf['api_key'])
    for atbl_rec in atbl_tbl.all(view="no galleries"):
        collection_id = atbl_rec['fields']['collection_id']
        galleries_search(collection_id, token, cred)


def collections_search(token, cred):
    '''
    searches collections
    '''
    print("searching collections...")
    params = {"include": "permissions,parent",
              "sort_by": "name",
              "sort_direction": "descending"}
    headers = {"content-type": "application/x-www-form-urlencoded",
               "X-PS-Api-Key": cred['photoshelter']['api_key'],
               "X-PS-Auth-Token": token}
    response = requests.get("https://www.photoshelter.com/psapi/v4.0/collections",
                            params=params, headers=headers)
    response.raise_for_status()
    for coll in response.json()['data']:
        atbl_rec_coll = airtable.CollectionRecord().from_json(coll)
        pprint(atbl_rec_coll.__dict__)
        atbl_rec_coll.send()


def add_galleries_to_media():
    '''
    iterates list of galleries
    iterates through media in gallery
    adds gallery to found media
    '''
    atbl_conf = airtable.config()
    atbl_tbl_gall = airtable.connect_one_table("appQA1IE68x2OBEGd",
                                               "PhotoShelter Galleries", atbl_conf['api_key'])
    atbl_tbl_part1 = airtable.connect_one_table("appWyFi5PxBTJJZaa",
                                                "PhotoShelter Data", atbl_conf['api_key'])
    atbl_tbl_part2 = airtable.connect_one_table("appQA1IE68x2OBEGd",
                                                "PhotoShelter Data", atbl_conf['api_key'])
    for atbl_rec_gall in atbl_tbl_gall.all(view='has media - not yet linked'):
        media_raw = atbl_rec_gall['fields']['Media']
        media_lst = [item.strip() for item in media_raw.split(",")]
        unfound_media = []
        for media_id in media_lst:
            atbl_rec_media = airtable.find(atbl_tbl_part1, media_id, 'media_id', True)
            if not atbl_rec_media:
                atbl_rec_media = airtable.find(atbl_tbl_part2, media_id, 'media_id', True)
                if not atbl_rec_media:
                    unfound_media.append(media_id)
                    continue
                # here means we match part2
                try:
                    galleries_raw = atbl_rec_media['fields']['Galleries']
                    galleries_lst = [item.strip() for item in galleries_raw.split(";")]
                    galleries_lst.append(atbl_rec_gall['fields']['gallery_id'])
                    galleries_updated = ",".join(set(galleries_lst))
                    atbl_tbl_part2.update(atbl_rec_media['id'], {"Galleries": galleries_updated})
                    continue
                except KeyError:
                    atbl_tbl_part2.update(atbl_rec_media['id'], {"Galleries": atbl_rec_gall['fields']['gallery_id']})
                    continue
            # here means we match part1
            try:
                galleries_raw = atbl_rec_media['fields']['Galleries']
                galleries_lst = [item.strip() for item in galleries_raw.split(";")]
                galleries_lst.append(atbl_rec_gall['fields']['gallery_id'])
                galleries_updated = ",".join(set(galleries_lst))
                atbl_tbl_part1.update(atbl_rec_media['id'], {"Galleries": galleries_updated})
                continue
            except KeyError:
                atbl_tbl_part1.update(atbl_rec_media['id'], {"Galleries": atbl_rec_gall['fields']['gallery_id']})
                continue
        if unfound_media:
            try:
                print("didn't find that one")
                unfound_media_rec = atbl_rec_gall['fields']['Media - Not In Airtable']
                unfound_media_lst = unfound_media_rec.split(',')
                unfound_media_lst.extend(unfound_media)
                unfound_media_updated = ",".join(set(unfound_media_lst))
                atbl_tbl_gall.update(atbl_rec_gall['id'], {"Media - Not In Airtable": unfound_media_updated})
            except KeyError:
                unfound_media = ",".join(set(unfound_media))
                atbl_tbl_gall.update(atbl_rec_gall['id'], {"Media - Not In Airtable": unfound_media})


def link_media_to_galleries():
    '''
    links media record to gallery records
    '''
    atbl_conf = airtable.config()
    # part2 - atbl_tbl_gall = airtable.connect_one_table("appQA1IE68x2OBEGd",
    atbl_tbl_gall = airtable.connect_one_table("appgYr7zoiRmDT0ye",
                                               "PhotoShelter Galleries", atbl_conf['api_key'])
    atbl_tbl_part1 = airtable.connect_one_table("appgYr7zoiRmDT0ye",
                                                "PhotoShelter Data", atbl_conf['api_key'])
    atbl_tbl_part2 = airtable.connect_one_table("appQA1IE68x2OBEGd",
                                                "PhotoShelter Data", atbl_conf['api_key'])
    for atbl_rec_media in atbl_tbl_part1.all(view="has galleries"):
        galleries = atbl_rec_media['fields']['Galleries'].split(",")
        galleries_ids = []
        for gallery in galleries:
            atbl_rec_gall = airtable.find(atbl_tbl_gall, gallery, "gallery_id", True)
            if not atbl_rec_gall:
                raise RuntimeError("How can there not be result?")
            gallery_rec_id = atbl_rec_gall['id']
            galleries_ids.append(gallery_rec_id)
        atbl_tbl_part1.update(atbl_rec_media['id'], {"PhotoShelter Galleries": galleries_ids})
        time.sleep(0.1)


def get_session_info(token):
    '''
    man I am just trying to figure this out
    '''
    cred = get_credentials()
    params = {"include": "organizations",
              "api_key": cred['photoshelter']['api_key']}
    headers = {"content-type": "application/x-www-form-urlencoded",
               "X-PS-Auth-Token": token}
    base_url = "https://www.photoshelter.com/psapi/v4.0/user/session"
    response = requests.get(base_url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def authenticate():
    '''
    do the thing
    '''
    cred = get_credentials()
    params = {"api_key": cred['photoshelter']['api_key'],
              "password": cred['photoshelter']['password'],
              "email": cred['photoshelter']['email'],
              "mode": "token",
              "include": "options"}
    headers = {"content-type": "application/x-www-form-urlencoded"}
    base_url = "https://www.photoshelter.com/psapi/v4.0/authenticate"
    response = requests.post(base_url, headers=headers, params=params)
    print(response.url)
    print("click on that ^ url and copy the token it gives you")


def authenticate_org(token):
    '''
    authenticates to the org?
    idk man this api sucks
    '''
    cred = get_credentials()
    params = {"api_key": cred['photoshelter']['api_key'],
              "password": cred['photoshelter']['password'],
              "email": cred['photoshelter']['email'],
              "org_id": "O0000e.jllXxQUoI"}
    headers = {"content-type": "application/x-www-form-urlencoded",
               "X-PS-Auth-Token": token}
    data = {"org_id": "O0000e.jllXxQUoI",
            "password": cred['photoshelter']['password'],
            "email": cred['photoshelter']['email']}
    base_url = "https://www.photoshelter.com/psapi/v4.0/organization/authenticate"
    response = requests.post(base_url, json=data, headers=headers, params=params)
    response.raise_for_status()
    print(response.status_code)
    print(response.json())


def log_in():
    '''
    wrapper for all this other crap
    '''
    print("logging in...")
    authenticate()
    print("please enter the token from that url, below")
    token = input("Token: ")
    print("authenticating to the org...")
    authenticate_org(token)
    session_info = get_session_info(token)
    print("check for org_id below:")
    pprint(session_info)


def init():
    '''
    get some command line args and parse em
    '''
    parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mode", dest="mode",
                        choices=['log_in',
                                 'download',
                                 'authenticate',
                                 'authenticate_org',
                                 'get_session_info',
                                 'get_media_metadata',
                                 'get_media_metadata_custom',
                                 'get_library',
                                 'search',
                                 'iterate_airtable',
                                 'prep_batch',
                                 'galleries_search',
                                 'collections_search',
                                 'get_media_in_galleries',
                                 'add_galleries_to_media',
                                 'link_media_to_galleries'],
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
    print("running")
    if args.mode == 'log_in':
        log_in()
    elif args.mode == 'authenticate':
        authenticate()
    elif args.mode == "prep_batch":
        prep_batch(cred)
    else:
        if not args.token:
            raise RuntimeError("you gotta get the token "\
                    "via authenticate mode")
        token = args.token
        if args.mode == "get_media_metadata":
            media_id = args.media_id
            get_media_md(media_id, token, cred)
        elif args.mode == 'authenticate_org':
              authenticate_org(token)
        elif args.mode == 'get_session_info':
            get_session_info(token)
        elif args.mode == "get_media_metadata_custom":
            media_id = args.media_id
            response = get_media_metadata_custom(media_id, token, cred)
            pprint(response.json())
            #parse_response_for_custom_fields(response)
        elif args.mode == "get_library":
            get_library(token, cred)
        elif args.mode == "search":
            manage_search(token, cred)
        elif args.mode == "iterate_airtable":
            iterate_airtable(token, cred, download=False)
        elif args.mode == "download":
            download_media("I0000IcZL.qvRYv8", token, cred)
        elif args.mode == "galleries_search":
            manage_galleries_search(token, cred)
        elif args.mode == "collections_search":
            collections_search(token, cred)
        elif args.mode == "get_media_in_galleries":
            get_media_in_galleries(token, cred)
        elif args.mode == "add_galleries_to_media":
            add_galleries_to_media()
        elif args.mode == "link_media_to_galleries":
            link_media_to_galleries()


if __name__ == "__main__":
    main()
