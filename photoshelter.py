'''
Photoshelter API integration for National Aquarium
'''
import re
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
        filepath = pathlib.Path("/tub/NationalAquarium/PhotoShelter-Data_batch9") / filename
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
              "mode": "invited",
              "include": "gallery"}
    headers = {"content-type": "application/x-www-form-urlencoded",
               "X-PS-Api-Key": cred['photoshelter']['api_key']}
    '''
               "Cookie": "SSphotoshelter_com_mem=EReh2JutceibFJ4O1MCf; acs=qYvUUr.DgUMRsRiv9ZGXTqcvRSC5nU40u6iI4gA3tD0kPTg3gblPpWUWZMoI2J04R._WMvnkFxT5ylf.cD80V6UlM8jNU2t9iLavVUG8bMjv5hrNa88oNetXV0E6fxXOIM6piQRuZ_9CsGxg6RLtFIYpoX86DBc9iHv3RpWb4JW4SZiluA7w9FC1DMevxDSBj.cHm7XWo7laY0qgpoQwu8Ynp776G5cFGAVFNe3Zp.NhNTgazErxjUzHEIsUYro36PcJHPjRZfUbkQeo6362GrOzfUsbxEYJ5zW6jvGWgtqAnSpuA2uNejyg"}
    '''
    response = requests.get("https://www.photoshelter.com/psapi/v4.0/media/" + media_id + "/galleries",
                            headers=headers, params=params)
    pprint(response.__dict__)
    input("yo")
    return response


def get_media_filename(media_id, token, cred):
    '''
    gets metadata for a single media object
    '''
    print("getting filename for media...")
    params = {"api_key": cred['photoshelter']['api_key'],
              "password": cred['photoshelter']['password'],
              "token": token}
    headers = {"content-type": "application/x-www-form-urlencoded",
               "X-PS-Api-Key": cred['photoshelter']['api_key']}
    response = requests.get("https://www.photoshelter.com/psapi/v4.0/media/" + media_id, params=params, headers=headers)
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
    i = 0
    while i < 10:
        try:
            response = requests.get("https://www.photoshelter.com/psapi/v4.0/media/" + media_id + "/custom-metadata",
                                    params=params, headers=headers)
            try:
                return response.json()['data']
            except KeyError:
                return None
        except requests.ConnectionError:
            i += 1
            time.sleep(0.1)
            continue


def iterate_airtable(token, cred, download=False):
    '''
    iterates through airtable list
    '''
    print("iterating through Airtable lists")
    batches = {"Batch1": "appjqbWe1U5qks6yg",
               "Batch2": "appsaN570Gj510rXj",
               "Batch3": "appDdM0GeiZGQ2Xa3",
               "Batch4": "appfvA08UNoLP71qC",
               "Batch5": "appa0ly6gIEsLMztS",
               "Batch6": "appGRmNo0i67eTLPL",
               "Batch7": "appXuHi7ju64VJcVe",
               "Batch8": "app7ViBOzU2gAj2yu",
               "Batch9": "app9T4BK04B1G5AAU"}
    batches = {"Batch9": "app9T4BK04B1G5AAU"}
    atbl_conf = airtable.config()
    for batch, base_id in batches.items():
        atbl_tbl = airtable.connect_one_table(base_id,
                                                batch, atbl_conf['api_key'])
        print("getting all records...")
        for atbl_rec_remote in atbl_tbl.all(view="need dl"):
            atbl_rec_updates = {"Checked for Permit": True}
            media_id = atbl_rec_remote['fields']['media_id']
            # atbl_rec_local = airtable.StillImageRecord().from_id(atbl_rec_remote['id'])
            print(f"working on: {media_id}")
            # filename = pathlib.Path(atbl_rec_local.file_name_disk)
            response = get_media_filename(media_id, token, cred)
            response_data = response.json()['data']
            pprint(response_data)
            filename_ps = pathlib.Path(response_data['attributes']['file_name'])
            filename = filename_ps.stem + "_" + media_id + filename_ps.suffix
            atbl_rec_updates['Filename'] = filename
            response_data = get_media_metadata_custom(media_id, token, cred)
            try:
                atbl_rec_with_custom_md = airtable.StillImageRecord().from_json(response_data)
                atbl_rec_updates['Permit'] = atbl_rec_with_custom_md.permit_number
            except Exception:
                pass
            if download:
                worked_yn = download_media(media_id, token, cred, filename=filename)
                if worked_yn:
                    atbl_rec_updates['downloaded'] = "true"
                else:
                    atbl_rec_updates['downloaded'] = "false"
            atbl_tbl.update(atbl_rec_remote['id'], atbl_rec_updates)
            #input("yo")
            # time.sleep(0.1)


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

    last straggler gallery: G0000_sI_gnW12n4
    '''
    atbl_conf = airtable.config()
    atbl_tbl = airtable.connect_one_table("app7yOX6pEDBdwT7O",
                                          "Galleries", atbl_conf['api_key'])
    for atbl_rec_gall in atbl_tbl.all(view="no media"):
        gallery_id = atbl_rec_gall['fields']['gallery_id']
        child_count = atbl_rec_gall['fields']['Child Count - Total']
        total_pages = math.ceil(child_count / 1000)
        page = 1
        all_media = []
        while page <= total_pages:
            gallery_data = get_media_of_gallery(gallery_id, token, cred, page)
            for media in gallery_data:
                media_id = media['id']
                #media_id = media_id.replace("I0000", "")
                all_media.append(media_id)
            page += 1
        all_media_str = ", ".join(all_media)
        atbl_tbl.update(atbl_rec_gall['id'], {"Media": all_media_str})


def galleries_search(collection_id, gallery_id, token, cred):
    '''
    goes through the gallery list
    '''
    print("searching galleries for")
    print(f"collection_id: {collection_id}")
    print(f"gallery_id: {gallery_id}")
    params = {"api_key": cred['photoshelter']['api_key'],
              "Auth-Token": token,
              "password": cred['photoshelter']['password'],
              "token": token,
              "include": "child-count",
              "sort_by": "name",
              "sort_direction": "descending",
              "parent": collection_id}
    headers = {"content-type": "application/x-www-form-urlencoded",
               "X-PS-Api-Key": cred['photoshelter']['api_key'],
               "X-PS-Auth-Token": token}
    try:
        response = requests.get("https://www.photoshelter.com/psapi/v4.0/galleries",
                            params=params, headers=headers)
    except Exception as exc:
        print("first exception, response-related")
        print(exc)
        return
    try:
        foo = response.json()['data']
    except:
        print("second exception, no .json()[data]")
        print(response.__dict__)
        return
    for gallery in response.json()['data']:
        pprint(gallery)
        atbl_rec_gall = airtable.GalleryRecord().from_json(gallery)
        print(f"gallery_id from atbl: {gallery_id}")
        print(f"gallery_id from serv: {atbl_rec_gall.gallery_id}")
        if atbl_rec_gall.gallery_id == gallery_id:
            pprint(atbl_rec_gall.__dict__)
            atbl_rec_gall.send()
            time.sleep(0.2)


def get_children_of_collection(collection_id, collection_name, token, cred):
    '''
    gets the children of the collection
    '''
    print(f"getting children for {collection_id}...")
    params = {"api_key": cred['photoshelter']['api_key'],
              "Auth-Token": token,
              "password": cred['photoshelter']['password'],
              "token": token,
              "sort_by": "name",
              "sort_direction": "descending"}
    headers = {"content-type": "application/x-www-form-urlencoded",
               "X-PS-Api-Key": cred['photoshelter']['api_key'],
               "X-PS-Auth-Token": token}
    try:
        response = requests.get("https://www.photoshelter.com/psapi/v4.0/collections/" + collection_id + "/children",
                            params=params, headers=headers)
    except Exception as exc:
        print(exc)
        return
    try:
        foo = response.json()['data']
    except:
        print(response.__dict__)
        return
    for gallery in response.json()['data']:
        #pprint(gallery)
        atbl_rec_gall = airtable.GalleryRecord().from_json(gallery)
        atbl_rec_gall.parent_collection_id = collection_id
        atbl_rec_gall.parent_collection_name = collection_name
        pprint(atbl_rec_gall.__dict__)
        atbl_rec_gall.send()
        time.sleep(0.2)


def manage_galleries_search(token, cred):
    '''
    wraps galleries_search to search for every gallery in every collection in Airtable
    '''
    atbl_conf = airtable.config()
    atbl_tbl = airtable.connect_one_table("app7yOX6pEDBdwT7O",
                                          "Galleries", atbl_conf['api_key'])
    for atbl_rec in atbl_tbl.all(view="no media"):
        collection_id = atbl_rec['fields']['parent_collection_id']
        gallery_id = atbl_rec['fields']['gallery_id']
        #collection_name = atbl_rec['fields']['Name']
        #get_children_of_collection(collection_id, collection_name, token, cred)
        galleries_search(collection_id, gallery_id, token, cred)



def galleries_path_search(gallery_id, token, cred):
    '''
    does the searching for breadcrumb path of gallery
    '''
    params = {"api_key": cred['photoshelter']['api_key'],
              "Auth-Token": token,
              "password": cred['photoshelter']['password'],
              "token": token,
              "gallery_id": gallery_id}
    headers = {"content-type": "application/x-www-form-urlencoded",
               "X-PS-Api-Key": cred['photoshelter']['api_key'],
               "X-PS-Auth-Token": token}
    i = 0
    while i < 10:
        try:
            response = requests.get("https://www.photoshelter.com/psapi/v4.0/galleries/" + gallery_id + "/path",
                                    params=params, headers=headers)
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


def manage_galleries_path_search(token, cred):
    '''
    adds the breadcrumb path to the gallery record
    '''
    print("getting breadcrumb path for galleries...")
    atbl_conf = airtable.config()
    atbl_tbl = airtable.connect_one_table("app7yOX6pEDBdwT7O",
                                          "Galleries", atbl_conf['api_key'])
    for atbl_rec in atbl_tbl.all(view="no media - check"):
        gallery_id = atbl_rec['fields']['gallery_id']
        print(gallery_id)
        response_data = galleries_path_search(gallery_id, token, cred)
        try:
            path_names = [gall['attributes']['name'] for gall in reversed(response_data)]
            breadcrumb_names = " > ".join(path_names)
            path_ids = [coll['id'] for coll in reversed(response_data)]
            breadcrumb_ids = ",".join(path_ids)
            atbl_tbl.update(atbl_rec['id'], {"Parents - Names": breadcrumb_names,
                                            "Parents - IDs": breadcrumb_ids})
        except:
            continue


def collections_path_search(collection_id, token, cred):
    '''
    does the searching for breadcrumb path of collection
    '''
    params = {"api_key": cred['photoshelter']['api_key'],
              "Auth-Token": token,
              "password": cred['photoshelter']['password'],
              "token": token,
              "collection_id": collection_id}
    headers = {"content-type": "application/x-www-form-urlencoded",
               "X-PS-Api-Key": cred['photoshelter']['api_key'],
               "X-PS-Auth-Token": token}
    response = requests.get("https://www.photoshelter.com/psapi/v4.0/collections/" + collection_id + "/path",
                            params=params, headers=headers)
    try:
        return response.json()['data']
    except:
        return None


def manage_collections_path_search(token, cred):
    '''
    adds the breadcrumb path to the collection record
    '''
    print("getting breadcrumb path for collections...")
    atbl_conf = airtable.config()
    atbl_tbl = airtable.connect_one_table("app7yOX6pEDBdwT7O",
                                          "Collections", atbl_conf['api_key'])
    for atbl_rec in atbl_tbl.all(view="no path"):
        collection_id = atbl_rec['fields']['collection_id']
        print(collection_id)
        response_data = collections_path_search(collection_id, token, cred)
        path_names = [coll['attributes']['name'] for coll in reversed(response_data)]
        breadcrumb_names = " > ".join(path_names)
        path_ids = [coll['id'] for coll in reversed(response_data)]
        breadcrumb_ids = ",".join(path_ids)
        atbl_tbl.update(atbl_rec['id'], {"Parents - Names": breadcrumb_names,
                                         "Parents - IDs": breadcrumb_ids})


def collections_search(token, cred):
    '''
    searches collections
    '''
    print("searching collections...")
    params = {"include": "permissions,parent",
              "sort_by": "name",
              "sort_direction": "descending",
              "page": 2, "per_page": 500}
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


def print_found_media_to_csv(batch, atbl_rec_gallery_id, found_media):
    '''
    prints found media for gallery in batch to text file
    '''
    this_dirpath = pathlib.Path(__file__).parent.absolute()
    csv_name = batch + "_" + atbl_rec_gallery_id + ".csv"
    csv_path = this_dirpath / "straggler_galleries" / csv_name
    with open(csv_path, "w") as csv_file:
        wr = csv.writer(csv_file)
        wr.writerow(found_media)

'''
def link_straggler_galleries():
    batch = "Batch99"
    atbl_rec_gall = {"id": "rec12345"}
    found_media = ["I01234", "I05678", "I09123"]
    print_found_media_to_csv(batch, atbl_rec_gall['id'], found_media)
''' 


def link_straggler_galleries():
    '''
    links three straggler galleries to media
    batches = {"Batch1": "appjqbWe1U5qks6yg",
               "Batch2": "appsaN570Gj510rXj",
    '''
    batches = {"Batch3": "appDdM0GeiZGQ2Xa3",
               "Batch4": "appfvA08UNoLP71qC",
               "Batch5": "appa0ly6gIEsLMztS",
               "Batch6": "appGRmNo0i67eTLPL",
               "Batch7": "appXuHi7ju64VJcVe",
               "Batch8": "app7ViBOzU2gAj2yu",
               "Batch9": "app9T4BK04B1G5AAU"}
    atbl_conf = airtable.config()
    for batch, base_id in batches.items():
        atbl_tbl_gall = airtable.connect_one_table(base_id,
                                                   "Galleries", atbl_conf['api_key'])
        atbl_tbl_media = airtable.connect_one_table(base_id,
                                                    batch, atbl_conf['api_key'])
        straggler_galleries = ["G0000_sI_gnW12n4", "G0000NS7rS6NnAcQ", "G0000AcKmu4eXInQ"]
        for gall_id in straggler_galleries:
            atbl_rec_gall = airtable.find(atbl_tbl_gall, gall_id, "gallery_id", True)
            media = atbl_rec_gall['fields']['Media']
            media_ids = ["I0000" + media_id for media_id in media.split(", ")]
            found_media = []
            for media_id in media_ids:
                print(f"searching {batch}")
                atbl_rec_media = airtable.find(atbl_tbl_media, media_id, "media_id", True)
                if not atbl_rec_media:
                    time.sleep(0.2)
                    continue
                found_media.append(atbl_rec_media['id'])
            print(f"found: {len(found_media)}")
            try:
                atbl_tbl_gall.update(atbl_rec_gall['id'], found_media)
            except:
                print_found_media_to_csv(batch, atbl_rec_gall['id'], found_media)


def link_wayward_galleries():
    '''
    there's a bunch of galleries that we didn't get at first
    and now we have to do this
    
    batches = {"Batch1": "appjqbWe1U5qks6yg",
               "Batch2": "appsaN570Gj510rXj",
    batches = {"Batch3": "appDdM0GeiZGQ2Xa3",
    batches = {"Batch4": "appfvA08UNoLP71qC",
               "Batch5": "appa0ly6gIEsLMztS",
               "Batch6": "appGRmNo0i67eTLPL",
    '''
    batches = {"Batch7": "appXuHi7ju64VJcVe",
               "Batch8": "app7ViBOzU2gAj2yu",
               "Batch9": "app9T4BK04B1G5AAU"}
    atbl_conf = airtable.config()
    for batch, base_id in batches.items():
        atbl_tbl_gall = airtable.connect_one_table(base_id,
                                                   "Galleries", atbl_conf['api_key'])
        atbl_tbl_media = airtable.connect_one_table(base_id,
                                                    batch, atbl_conf['api_key'])
        for atbl_rec_gall in atbl_tbl_gall.all(view="stragglers - normal"):
            media_raw = atbl_rec_gall['fields']['Media']
            media = [media_id for media_id in media_raw.split(", ")]
            found_media = []
            for media_id in media:
                time.sleep(0.1)
                result = airtable.find(atbl_tbl_media, media_id, "media_id", True)
                if not result:
                    continue
                found_media.append(result['id'])
            if found_media:
                print(f"batch: {batch}")
                print(f"found_media: {found_media}")
                atbl_tbl_gall.update(atbl_rec_gall['id'], {batch: found_media})
        #input("yo")


def link_media_to_galleries():
    '''
    links media record to gallery records
    '''
    batches = {"Batch1": "appjqbWe1U5qks6yg",
               "Batch2": "appsaN570Gj510rXj",
               "Batch3": "appDdM0GeiZGQ2Xa3",
               "Batch4": "appfvA08UNoLP71qC",
               "Batch5": "appa0ly6gIEsLMztS",
               "Batch6": "appGRmNo0i67eTLPL",
               "Batch7": "appXuHi7ju64VJcVe",
               "Batch8": "app7ViBOzU2gAj2yu",
               "Batch9": "app9T4BK04B1G5AAU"}
    atbl_conf = airtable.config()
    for batch, base_id in batches.items():
        atbl_tbl_gall = airtable.connect_one_table(base_id,
                                                   "Galleries", atbl_conf['api_key'])
        atbl_tbl_media = airtable.connect_one_table(base_id,
                                                    batch, atbl_conf['api_key'])
        for atbl_rec_media in atbl_tbl_media.all():
            media_id = atbl_rec_media['fields']['media_id']
            media_id_search = media_id.replace("I0000", "")
            results = airtable.find(atbl_tbl_gall, media_id, 'Media')
            if not results:
                continue
            galleries = []
            for atbl_rec_gall in results:
                galleries.append(atbl_rec_gall['id'])
            galleries = list(set(galleries))
            atbl_tbl_media.update(atbl_rec_media['id'], {'Galleries': galleries})
            time.sleep(0.1)


def add_to_batch9(media_id, gallery_id, token, cred):
    '''
    adds media_id ot batch 9
    '''
    atbl_conf = airtable.config()
    atbl_tbl_batch9_galleries = airtable.connect_one_table("app9T4BK04B1G5AAU",
                                                 "Galleries", atbl_conf['api_key'])
    atbl_tbl_batch9_media = airtable.connect_one_table("app9T4BK04B1G5AAU",
                                                 "Batch9", atbl_conf['api_key'])

    atbl_rec_batch9_gallery = airtable.find(atbl_tbl_batch9_galleries, gallery_id, 'gallery_id', True)
    if not atbl_rec_batch9_gallery:
        print(f"gallery_id {gallery_id} does not exist in Batch9 Galleries table")
        raise RuntimeError
    batch9_gallery_rec_id = atbl_rec_batch9_gallery['id']
    atbl_rec_batch9_media = airtable.find(atbl_tbl_batch9_media, media_id, "media_id", True)
    if not atbl_rec_batch9_media:
        atbl_tbl_batch9_media.create({"media_id": media_id, "Galleries": [batch9_gallery_rec_id]})
        return
    print("this media_id already exists in batch9 but wasn't caught earlier")
    raise RuntimeError


def qc(token, cred):
    '''
    for qc tasks
    '''
    batches = {"Batch1": "appjqbWe1U5qks6yg",
               "Batch2": "appsaN570Gj510rXj",
               "Batch3": "appDdM0GeiZGQ2Xa3",
               "Batch4": "appfvA08UNoLP71qC",
               "Batch5": "appa0ly6gIEsLMztS",
               "Batch6": "appGRmNo0i67eTLPL",
               "Batch7": "appXuHi7ju64VJcVe",
               "Batch8": "app7ViBOzU2gAj2yu",
               "Batch9": "app9T4BK04B1G5AAU"}
    atbl_conf = airtable.config()
    atbl_tbl_gall = airtable.connect_one_table("app7yOX6pEDBdwT7O",
                                               "Galleries", atbl_conf['api_key'])
    for atbl_rec_gall in atbl_tbl_gall.all(view="has coll - has children - has media - child count diff"):
        gallery_id = atbl_rec_gall['fields']['gallery_id']
        media_raw = atbl_rec_gall['fields']['Media']
        media_lst = media_raw.split(", ")
        for media_id in media_lst:
            found = False
            atbl_rec_gall = atbl_tbl_gall.get(atbl_rec_gall['id'])
            child_count_diff = atbl_rec_gall['fields']['child_count_diff']
            if child_count_diff == 0:
                break
            for batch, base_id in batches.items():
                atbl_tbl_batch_galleries = airtable.connect_one_table(base_id, "Galleries", atbl_conf['api_key'])
                atbl_tbl_batch_media = airtable.connect_one_table(base_id, batch, atbl_conf['api_key'])
                result_batch_media = airtable.find(atbl_tbl_batch_media, media_id, "media_id", True)
                if not result_batch_media:
                    continue
                try:
                    result_batch_media_linked_galleries = result_batch_media['fields']['Galleries']
                    gallery_ids = []
                    for atbl_rec_id_gallery in result_batch_media_linked_galleries:
                        linked_gallery_rec = atbl_tbl_batch_galleries.get(atbl_rec_id_gallery)
                        gallery_ids.append(linked_gallery_rec['fields']['gallery_id'])
                    pprint(gallery_ids)
                    print(gallery_id)
                    if gallery_id in gallery_ids:
                        found = True
                        break
                except KeyError:
                    pass
                if gallery_id in result_batch_media_linked_galleries:
                    continue
                result_batch_gallery = airtable.find(atbl_tbl_batch_galleries, gallery_id, "gallery_id", True)
                if not result_batch_gallery:
                    print(f"there was a problem linking these:")
                    print(f"gallery_id: {gallery_id}")
                    print(f"media_id: {media_id}")
                    print(f"batch: {batch}")
                    raise RuntimeError
                try:
                    batch_media_linked = result_batch_gallery['fields'][batch]
                    batch_media_linked.append(result_batch_media['id'])
                except KeyError:
                    batch_media_linked = [result_batch_media['id']]
                atbl_tbl_batch_galleries.update(result_batch_gallery['id'], {batch: list(set(batch_media_linked))})
                child_count_batch_field = 'child_count_' + batch.lower()
                child_count = atbl_rec_gall['fields'][child_count_batch_field]
                child_count += 1
                atbl_tbl_gall.update(atbl_rec_gall['id'], {child_count_batch_field: child_count})
                found = True
                break
            if not found:
                print(f"could not find: {media_id}")
                add_to_batch9(media_id, gallery_id, token, cred)
                child_count = atbl_rec_gall['fields']['child_count_batch9']
                child_count += 1
                atbl_tbl_gall.update(atbl_rec_gall['id'], {'child_count_batch9': child_count})


def rebuild_airtable_from_disk():
    '''
    ay yi yi
    '''
    path = pathlib.Path("/tub/NationalAquarium/PhotoShelter-Data_batch9")
    atbl_conf = airtable.config()
    atbl_tbl = airtable.connect_one_table("app9T4BK04B1G5AAU",
                                                 "Batch9", atbl_conf['api_key'])
    records = []
    for file in path.glob("*"):
        match = re.search(r'([A-Z]0000|VD000).{11}', file.name)
        if match:
            media_id = match.group()
            print(media_id)
        else:
            media_id = "None"
        records.append({"media_id": media_id,
                         "Filename": file.name})
    atbl_tbl.batch_create(records)


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
                                 'link_media_to_galleries',
                                 'link_wayward_galleries',
                                 "link_straggler_galleries",
                                 'rebuild_airtable_from_disk',
                                 'add_path_to_collections',
                                 'qc',
                                 'add_path_to_galleries'],
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
            iterate_airtable(token, cred, download=True)
        elif args.mode == "download":
            download_media("I0000IcZL.qvRYv8", token, cred)
        elif args.mode == "galleries_search":
            manage_galleries_search(token, cred)
        elif args.mode == "add_path_to_galleries":
            manage_galleries_path_search(token, cred)
        elif args.mode == "collections_search":
            collections_search(token, cred)
        elif args.mode == "add_path_to_collections":
            manage_collections_path_search(token, cred)
        elif args.mode == "get_media_in_galleries":
            get_media_in_galleries(token, cred)
        elif args.mode == "add_galleries_to_media":
            add_galleries_to_media()
        elif args.mode == "link_media_to_galleries":
            link_media_to_galleries()
        elif args.mode == "link_wayward_galleries":
            link_wayward_galleries()
        elif args.mode == "link_straggler_galleries":
            link_straggler_galleries()
        elif args.mode == "qc":
            qc(token, cred)
        elif args.mode == "rebuild_airtable_from_disk":
            rebuild_airtable_from_disk()


if __name__ == "__main__":
    main()
