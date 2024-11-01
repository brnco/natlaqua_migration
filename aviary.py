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


if __name__ == "__main__":
    main()
