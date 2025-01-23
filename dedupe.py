'''
dedupes the csvs of the collection

need to loop through dedupe view in batch5
match media_ids in batch7
-if match, check 'delete' box in batch7
-if not match, ???

then you need to delete those files in batch 7
then re-zip, re-upload

then re-zip batch9 and re-upload

then you're done
'''

import os
import csv
import pathlib
import argparse
import airtable

def process_csv_files(folder_path, output_file):
    '''
    processes teh csv files
    '''
    combined_media_ids = []
    for csv_file in folder_path.glob("*.csv"):
        try:
            with open(csv_file, mode="r", newline="", encoding="utf-8") as in_file:
                reader = csv.reader(in_file)
                for row in reader:
                    if row:
                        combined_media_ids.extend(row)
        except Exception as e:
            print(f"Error reading {file}: {e}")

    seen = set()
    duplicates = set()
    for media_id in combined_media_ids:
        if media_id in seen:
            duplicates.add(media_id)
        else:
            seen.add(media_id)

    try:
        with open(output_file, mode="w", newline="", encoding="utf-8") as out_file:
            writer = csv.writer(out_file)
            for dupe in sorted(duplicates):
                writer.writerow([dupe])
        print("done writing")
    except Exception as e:
        print(f"Error writing to {output_file}: {e}")


def select_files_to_delete():
    '''
    goes through Airtable and selects one version of each file to delete
    '''
    with open("duplicate_media_ids.csv", "r") as csv_file:
        csv_reader = csv.reader(csv_file)
        csv_data = list(csv_reader)
    media_ids_raw = [x[0] for x in csv_data]
    media_ids_found = []
    atbl_conf = airtable.config()
    atbl_tbl_batch9 = airtable.connect_one_table("app9T4BK04B1G5AAU",
                                                 "Batch9", atbl_conf['api_key'])
    atbl_tbl_batch7 = airtable.connect_one_table("appXuHi7ju64VJcVe",
                                                 "Batch7", atbl_conf['api_key'])
    atbl_tbl_batch5 = airtable.connect_one_table("appa0ly6gIEsLMztS",
                                                 "Batch5", atbl_conf['api_key'])
    atbl_tbl_batch4 = airtable.connect_one_table("appfvA08UNoLP71qC",
                                                 "Batch4", atbl_conf['api_key'])
    tables = [atbl_tbl_batch9, atbl_tbl_batch7, atbl_tbl_batch5, atbl_tbl_batch4]
    for tbl in tables:
        print(f"working on table {tbl}")
        for atbl_rec in tbl.all(view="dedupe"):
            media_id = atbl_rec['fields']['media_id']
            if media_id not in media_ids_found:
                tbl.update(atbl_rec['id'], {"delete": True})
                media_ids_found.append(media_id)
    '''
    for atbl_rec in atbl_tbl_batch9.all(view="dedupe"):
        media_ids_found.append(atbl_rec['fields']['media_id'])
    for atbl_rec in atbl_tbl_batch7.all(view="dedupe"):
        media_id = atbl_rec['fields']['media_id']
        if media_id not in media_ids_found:
            media_ids_found.append(media_id)
    for atbl_rec in atbl_tbl_batch
    '''

def delete_duplicate_files():
    '''
    loops through list of duplicate files
    deletes them
    updates Airtable
    
    batches with dupes:
    batch 1?
    batch4
    batch5
    batch7
    batch9

    need to decide which files to delete
    find and mark them in Airtable
    create those views
    then write all this
    '''
    



def init_args():
    '''
    initialize arguments form the CLI
    '''
    parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--mode", dest="mode",
                        choices=['find_duplicates',
                                 'select_files_to_delete',
                                 'delete_duplicate_files'])
    args = parser.parse_args()
    return args


def main():
    '''
    do the thing
    '''
    args = init_args()
    if args.mode == 'find_duplicates':
        folder_path = pathlib.Path("/home/bcoates/code/natlaqua_migration/dedupe/")
        output_file = "duplicate_media_ids.csv"
        process_csv_files(folder_path, output_file)
    elif args.mode == 'select_files_to_delete':
        select_files_to_delete()
    elif args.mode == 'delete_duplicate_files':
        delete_duplicate_files()

if __name__ == "__main__":
    main()
