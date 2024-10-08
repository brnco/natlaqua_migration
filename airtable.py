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


def get_api_key():
    '''
    returns personal token from config file
    '''
    atbl_config = config()
    return atbl_config['airtable']['api_key']


class NatlAquaAirtableRecord(object):
    '''
    super class for the various AirtableRecord() classes
    that we'll create later
    defines a few methods we'll use for all Airtable records
    '''
    primary_field = None

    def _get_primary_key_info(self):
        '''
        for send()
        gets primary key name and value
        '''
        atbl_tbl = self.get_table()
        atbl_tbl_schema = atbl_mtd.get_table_schema(atbl_tbl)
        primary_field_id = atbl_tbl_schema['primaryFieldId']
        for field in atbl_tbl_schema['fields']:
            if field['id'] == primary_field_id:
                primary_field_name = field['name']
                break
        try:
            self_primary_field_value = self._fields[primary_fields_name]
        except KeyError:
            self_primary_field_value = self.primary_field
        return primary_field_name, self_primary_field_value

    def _search_on_primary_field(self, primary_field_name, self_primary_field_value):
        '''
        searches for self_primary_field_value in primary_field_name
        '''
        atbl_tbl = self.get_table()
        response = atbl_tbl.all(formula=match({
            primary_field_name: self_primary_field_value}))
        if len(response) > 1:
            raise ValueError(f"too many results for {self_primary_field_value}")
        elif len(response) > 0:
            atbl_rec_remote = self.from_id(response[0]['id'])
        else:
            return None
        return atbl_rec_remote

    def _fill_remote_rec_from_local(self, atbl_rec_remote):
        '''
        we can't just assign a record id to an unsaved record
        and have it overwrite the remote record
        so instead we do this
        where we tak ethe remote record
        and fill it with local values
        '''
        for field, value in self._fields.items():
            try:
                atbl_rec_remote._fields[field] = value
            except (KeyError, TypeError) as exc:
                pprint(exc)
                continue
            return atbl_rec_remote

    def _save_rec(self, atbl_rec):
        '''
        actually save the record
        '''
        try:
            atbl_rec.save()
            time.sleep(0.1)
            if atbl_rec.exists():
                return atbl_rec
            else:
                raise RuntimeError("there was a problem saving that record")
            except requests.exceptions.HTTPError as exc:
                pprint(exc)
                raise RuntimeError("there was a network problem while saving that record")


    def send(self):
        '''
        primary means of updating and inserting records

        looks up value of primary field in table
        if found, updates record
        if not found, creates new record
        '''
        primary_field_name, self_primary_field_value = \
                self._get_primary_key_info()
        atbl_rec_remote = self._search_on_primary_field(
                primary_field_name, self_primary_field_value)
        if atbl_rec_remote:
            atbl_rec_remote = self._fill_remote_rec_from_local(
                    atbl_rec_remote)
        else:
            atbl_rec_remote = self
        atbl_rec_remote = self._save_rec(atbl_rec_remote)
        return atbl_rec_remote

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

