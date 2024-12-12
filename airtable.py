'''
manages the Airtable stuff
'''
import time
import json
import datetime
import requests
import pathlib
from pprint import pprint
from pyairtable import Api, Table
from pyairtable import metadata as atbl_mtd
from pyairtable.orm import Model, fields
from pyairtable.formulas import match


def config():
    '''
    create a config object for Airtable setup
    '''
    this_dirpath = pathlib.Path(__file__).parent.absolute()
    with open(this_dirpath / 'credentials.json', 'r') as config_file:
        config = json.load(config_file)
    return config['airtable_part2']


def get_api_key():
    '''
    returns personal token from config file
    '''
    atbl_config = config()
    return atbl_config['api_key']


def get_field_map(obj_type):
    '''
    returns dictionary of field mappings attrs
    for specified obj type
    '''
    this_dirpath = pathlib.Path(__file__).parent.absolute()
    with open(this_dirpath / "field_mappings.json", "r") as fm:
        field_map = json.load(fm)
    return field_map[obj_type]


class NatlAquaAirtableRecord:
    '''
    super class for the various AirtableRecord() classes
    that we'll create later
    defines a few methods we'll use for all Airtable records
    '''
    primary_field = None

    @classmethod
    def from_json(cls, json_rec, field_map):
        '''
        creates an Airtable record from JSON response from
        the service (PhotoShelter or Aviary)
        '''
        instance = cls()
        #print(f"json_rec: {json_rec}")
        for attr_name, key_list in field_map.items():
            value = json_rec
            #print(f"key_list: {key_list}")
            for key in key_list:
                #print(f"key: {key}")
                #print(f"value: {value}")
                try:
                    assert value[key]
                except (KeyError, AssertionError):
                    #print("key/ assert error, setting value to none")
                    value = None
                    break
                except TypeError:
                    #print("type error")
                    #print(f"value: {value}")
                    pass
                if isinstance(value, list):
                    #print("in isinstance list")
                    if attr_name == "galleries":
                        all_galleries = []
                        for item in value:
                            try:
                                gallery = item['includes']['gallery']['data']['attributes']['name']
                                all_galleries.append(gallery)
                            except:
                                pass
                        value = '; '.join(all_galleries)
                        break
                    else:
                        for item in reversed(value):
                            try:
                                value = item[key]
                                break
                            except Exception:
                                pass
                else:
                    #print(f"setting value to {value[key]}")
                    value = value[key]
            '''
            if isinstance(value, list):
                value = None
            '''
            if not value:
                continue
            try:
                setattr(instance, attr_name, value)
            except ValueError as exc:
                print(exc)
                continue
            except TypeError as exc:
                #means we're not at the end of key_list, hopefully
                if attr_name == "permissions" or attr_name == "child_count":
                    last_index = len(key_list) - 1
                    if key_list.index(key) == last_index:
                        #we're at the last key
                        setattr(instance, attr_name, str(value))
                else:
                    pass
        return instance

    def _get_primary_key_info(self):
        '''
        for send()
        gets primary key name and value
        '''
        primary_field_name = "gallery_id"
        self_primary_field_value = self._fields[primary_field_name]
        '''
        atbl_tbl = self.get_table()
        #atbl_tbl_schema = atbl_mtd.get_table_schema(atbl_tbl)
        atbl_tbl_schema = atbl_tbl.schema()
        primary_field_id = atbl_tbl_schema['primaryFieldId']
        for field in atbl_tbl_schema['fields']:
            if field['id'] == primary_field_id:
                primary_field_name = field['name']
                break
        try:
            self_primary_field_value = self._fields[primary_fields_name]
        except KeyError:
            self_primary_field_value = self.primary_field
        '''
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


class GalleryRecord(Model, NatlAquaAirtableRecord):
    '''
    object class for collections in PhotoShelter
    '''
    field_map = get_field_map("GalleryRecord")
    serv_atbl_map = {}
    for field, mapping in field_map.items():
        vars()[field] = fields.TextField(mapping['atbl'])
        try:
            serv_atbl_map[field] = mapping['serv']
        except KeyError:
            continue

    class Meta:
        base_id = "appQA1IE68x2OBEGd"
        table_name = "PhotoShelter Galleries"
        typecast = False

        @staticmethod
        def api_key():
            return get_api_key()       

    def from_json(self, record):
        '''
        creates an Airtable record from JSON response
        uses serv -> atbl map
        '''
        return super().from_json(record, self.serv_atbl_map)


class CollectionRecord(Model, NatlAquaAirtableRecord):
    '''
    object class for collections in PhotoShelter
    '''
    field_map = get_field_map("CollectionRecord")
    serv_atbl_map = {}
    for field, mapping in field_map.items():
        vars()[field] = fields.TextField(mapping['atbl'])
        try:
            serv_atbl_map[field] = mapping['serv']
        except KeyError:
            continue

    class Meta:
        base_id = "appQA1IE68x2OBEGd"
        table_name = "PhotoShelter Collections"
        typecast = False

        @staticmethod
        def api_key():
            return get_api_key()       

    def from_json(self, record):
        '''
        creates an Airtable record from JSON response
        uses serv -> atbl map
        '''
        return super().from_json(record, self.serv_atbl_map)

class StillImageRecord(Model, NatlAquaAirtableRecord):
    '''
    object class for Still Images at National Aquarium
    '''
    field_map = get_field_map("StillImageRecord")
    serv_atbl_map = {}
    for field, mapping in field_map.items():
        vars()[field] = fields.TextField(mapping['atbl'])
        try:
            serv_atbl_map[field] = mapping['serv']
        except KeyError:
            continue

    class Meta:
        # part1 base_id = "appWyFi5PxBTJJZaa"
        base_id = "appQA1IE68x2OBEGd"
        table_name = "PhotoShelter Data"
        typecast = False

        @staticmethod
        def api_key():
            return get_api_key()       

    def from_json(self, record):
        '''
        creates an Airtable record from JSON response
        uses serv -> atbl map
        '''
        return super().from_json(record, self.serv_atbl_map)


class MovingImageRecord(Model, NatlAquaAirtableRecord):
    '''
    class for Airtable record for Moving Images housed in Aviary
    '''
    field_map = get_field_map("MovingImageRecord")
    serv_atbl_map = {}
    for field, mapping in field_map.items():
        vars()[field] = fields.TextField(mapping['atbl'])
        try:
            serv_atbl_map[field] = mapping['serv']
        except KeyError:
            continue

    class Meta:
        base_id = "appQA1IE68x2OBEGd"
        table_name = "Aviary Data"
        typecast = False

        @staticmethod
        def api_key():
            return get_api_key()       


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
            if single_result and len(results) == 1:
                return results[0]
            return results
        print("no results found")
        return None
    except ValueError:
        raise RuntimeError(f"too many results, expected one and got {len(results)}")
    except Exception as exc:
        print(exc)
        raise RuntimeError("there was a problem searching Airtable")

