'''
dedupes the csvs of the collection
'''

import os
import csv
import pathlib

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

folder_path = pathlib.Path("/home/bcoates/code/natlaqua_migration/dedupe/")

output_file = "duplicate_media_ids.csv"

process_csv_files(folder_path, output_file)
