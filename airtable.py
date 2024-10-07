'''
manages the Airtable stuff
'''
import time
import json
import datetime
import requests
from pyairtable import Api, Table
from pyairtable import metadata as atbl_mtd
from pyairtable.formulas import match


def config():
    '''
    create a config object for Airtable setup
    '''
    this_dirpath = pathlib.Path(__file__).parent.absolute()
    with open(this_dirpath / 'airtable_config.json', 'r') as config_file:
        atbl_config = json.load(config_file)
    return atbl_config


def connect_one_table(base_id, table_name, api_key):
    '''
    connects to Airtable table
    returns an Airtable object
    '''
    try:
        atbl = Table(api_key, base_id, table_name)
        return atbl
    except Exception as exc:
        print(exc, stack_info=True)
        raise RuntimeError("there was a problem connecting to Airtable")


def find(atbl_tbl, query, field, single_result=False):
    '''
    queries at field in table
    if single result=True
    --returns single record (json) if 1 record found
    raises error if >1 record found
    if single_result=False
    --returns list of found records
    '''
    print(f"searching Airtable for value: {query}")
    print(f"in field: {field}")
    try:
        results = atbl_tbl.all(formula=match({field: query}))
        if results:
            if single_result and len(results) > 1:
                raise ValueError
            if single_result and len(results) = 1:
                return results[0]
            return results
        print("no results found")
        return None
    except ValueError:
        raise RuntimeError(f"too many results, expected one and got {len(results)}")
    except Exception as exc:
        print(exc, stack_info=True)
        raise RuntimeError("there was a problem searching Airtable")

