'''
works with Aviary data for National Aquarium
'''
import json
import airtable
import pathlib
import time
import shutil
import argparse
import subprocess
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
    print("preparing download...")
    filepath = pathlib.Path("/run/media/bec/LaCie/Aviary-Data_test") / filename
    if filepath.exists():
        print("already exists...")
        return filepath
    with requests.get(url, stream=True) as res:
        with open(filepath, "wb") as file:
            shutil.copyfileobj(res.raw, file)
    if res.status_code != 200:
        print("file did not download (probably)")
        print(res.status_code)
        filepath.unlink()
        return False
    return filepath


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
    for atbl_rec_remote in atbl_tbl.all(view="test"):
        atbl_rec_local = airtable.MovingImageRecord().from_id(atbl_rec_remote['id'])
        print(f"working on {atbl_rec_local.aviary_id}")
        filename = pathlib.Path(atbl_rec_local.file_name_disk)
        url = atbl_rec_local.url
        print(f"url: {url}")
        print(f"filename: {filename}")
        if download:
            worked_yn = download_media(url, filename)
            if worked_yn:
                atbl_rec_local.downloaded = "true"
            else:
                atbl_rec_local.downloaded = "false"
            atbl_rec_local.save()
        time.sleep(0.1)
        input("yo")


def init():
    '''
    get some command line args and parse em
    '''
    parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mode", dest="mode",
                        choices=['download'],
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
    iterate_airtable(cred, False)


if __name__ == "__main__":
    main()
