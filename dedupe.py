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
    elif args.mode == 'delete_duplicate_files':
        delete_duplicate_files()

if __name__ == "__main__":
    main()
