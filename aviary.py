'''
works with Aviary data for National Aquarium
'''
import requests
import json
import airtable
import pathlib
import time
import shutil
import argparse
import subprocess
from bs4 import BeautifulSoup
from pprint import pprint


def get_credentials():
    '''
    reads credential info from config file
    '''
    this_dirpath = pathlib.Path(__file__).parent.absolute()
    with open(this_dirpath / 'credentials.json', 'r') as config_file:
        credentials = json.load(config_file)
    return credentials


def download_media(url, filename):
    '''
    downloads media
    '''
    filepath = pathlib.Path("/run/media/bec/LaCie/Aviary-Data") / filename
    if filepath.exists():
        print("already exists...")
        return filepath
    print("downloading...")
    with requests.get(url, stream=True) as res:
        with open(filepath, "wb") as file:
            shutil.copyfileobj(res.raw, file)
    if res.status_code != 200:
        print("file did not download (probably)")
        print(res.status_code)
        filepath.unlink()
        return False
    '''
    cmd = "curl --output " + str(filepath) + " " + url
    output = subprocess.run(cmd, shell=True, capture_output=True)
    '''
    #print(str(output))
    #print(output.returncode)
    return filepath


def get_media_url(embed_url):
    '''
    uses the html in the embed url to get the media url
    hosted on wasabi
    '''
    try:
        response = requests.get(embed_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        video_tag = soup.find('video')
        video_source = video_tag.source
        video_url = video_source['src']
        return video_url
    except Exception as exc:
        return False


def iterate_airtable(cred, download=False):
    '''
    iterates through airtable list
    '''
    print("iterating through Airtable list...")
    atbl_conf = airtable.config()
    atbl_tbl = airtable.connect_one_table(atbl_conf['base_id'],
                                          'Aviary Data',
                                          atbl_conf['api_key'])
    print("getting all records...")
    for atbl_rec_remote in atbl_tbl.all(view="Ntl Aquarium - downloading"):
        atbl_rec_local = airtable.MovingImageRecord().from_id(atbl_rec_remote['id'])
        print(f"working on {atbl_rec_local.aviary_id}")
        filename = pathlib.Path(atbl_rec_local.file_name_disk)
        embed_url = atbl_rec_local.url
        media_url = get_media_url(embed_url)
        if not media_url:
            atbl_rec_local.downloaded = "false"
            atbl_rec_local.save()
            continue
        #url = "https://s3.us-east-1.wasabisys.com/aviary-p-aqua/collection_resource_files/resource_files/000/103/318/original/open-uri20201218-733-155pxbq.mp4?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=U3QOTTBB2JB9O4ZG5WFS%2F20241106%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20241106T220316Z&X-Amz-Expires=111&X-Amz-SignedHeaders=host&X-Amz-Signature=5eeab1e345faedc9f2151a819c82510fd9dc8e6ec1f88bd2847c8471a4a651fe"
        #media_id = atbl_rec_local.media_id
        #url = "https://aqua.aviaryplatform.com/embed/media/" & media_id
        print(f"url: {media_url}")
        print(f"filename: {filename}")
        if download:
            worked_yn = download_media(media_url, filename)
            if worked_yn:
                atbl_rec_local.downloaded = "true"
            else:
                atbl_rec_local.downloaded = "false"
            atbl_rec_local.save()
        time.sleep(0.1)


'''
'accept': 'application/json',
'api_key': cred['aviary']['api_key']})
'''


def authenticate(cred):
    '''
    authenticates to aviary api
    '''
    print("authenticating...")
    session = requests.Session()
    username = cred['aviary']['username']
    password = cred['aviary']['password']
    print(username)
    print(password)
    print(cred['aviary']['api_key'])
    session.auth = (username, password)
    response = session.post("https://aqua.aviaryplatform.com/api/v1/auth/sign_in",
                            json={"email": username,
                                  "password": password,
                                  "api_key": cred['aviary']['api_key']},
                            headers={'Content-Type': 'application/json'})
    response.raise_for_status()
    auth = {'access-token': response.headers['access-token'],
            'client': response.headers['client'],
            'token-type': response.headers['token-type'],
            'uid': response.headers['uid']}
    session.headers.update(auth)
    return session


def init():
    '''
    get some command line args and parse em
    '''
    parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mode", dest="mode",
                        choices=['authenticate','download'],
                        help="the mode of the script")
    args = parser.parse_args()
    return args


def main():
    '''
    do the thing
    '''
    args = init()
    cred = get_credentials()
    print("running...")
    if args.mode == 'authenticate':
        session = authenticate(cred)
    elif args.mode == 'download':
        iterate_airtable(cred, True)


if __name__ == "__main__":
    main()
