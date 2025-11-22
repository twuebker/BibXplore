import os
import json
import glob
import re
import random
import csv
import pandas as pd
from tqdm import tqdm
import xml.etree.ElementTree as ET

# Namespaces for parsing
NAMESPACES = {
    'ns0': 'http://www.openarchives.org/OAI/2.0/',
    'ns1': 'http://www.loc.gov/MARC21/slim'
}


def extract_text(root, tag, subfield_code=None):
    field = root.find(f".//ns1:datafield[@tag='{tag}']", NAMESPACES)
    if field is None: return None
    if subfield_code:
        subfield = field.find(f"ns1:subfield[@code='{subfield_code}']", NAMESPACES)
        return subfield.text if subfield is not None else None
    return field.text


def get_control_field(root, tag):
    field = root.find(f".//ns1:controlfield[@tag='{tag}']", NAMESPACES)
    return field.text if field is not None else None


def is_valid_record(json_line):
    try:
        data = json.loads(json_line)
        raw_xml = data.get("raw_xml", "")
        if not raw_xml: return None
        root = ET.fromstring(raw_xml)

        # --- 1. Mandatory Core Fields ---

        isbn = extract_text(root, '020', 'a')
        if not isbn: return None
        # [REMOVED] isbn = str(isbn).replace("-", "")  <-- Keeping hyphens now

        summary_text = extract_text(root, '520', 'a')
        if not summary_text or not summary_text.strip(): return None

        # Clean newlines to keep CSV rows intact
        summary_text = summary_text.replace("\n", " ").replace("\r", " ").strip()

        pages_str = extract_text(root, '300', 'a')
        if not pages_str: return None
        page_match = re.search(r'(\d+)', pages_str)
        if not page_match: return None
        page_count = int(page_match.group(1))

        pub_year = None
        f008 = get_control_field(root, '008')
        if f008 and len(f008) >= 11:
            year_candidate = f008[7:11]
            if year_candidate.isdigit(): pub_year = int(year_candidate)
        if not pub_year:
            date_str = extract_text(root, '264', 'c')
            if date_str:
                year_match = re.search(r'(\d{4})', date_str)
                if year_match: pub_year = int(year_match.group(1))
        if not pub_year: return None

        lang = None
        if f008 and len(f008) >= 38: lang = f008[35:38]
        if not lang or lang == "|||": lang = extract_text(root, '041', 'a')
        if not lang: return None

        # --- 2. Mandatory Metadata ---

        title = extract_text(root, '245', 'a')
        if not title: return None
        title = title.replace("\n", " ").strip()

        author = extract_text(root, '100', 'a')
        if not author: return None

        publisher = extract_text(root, '264', 'b')
        if not publisher: return None

        genres_list = [g.find("ns1:subfield[@code='a']", NAMESPACES).text
                       for g in root.findall(".//ns1:datafield[@tag='655']", NAMESPACES)
                       if g.find("ns1:subfield[@code='a']", NAMESPACES) is not None]
        if not genres_list: return None

        # --- 3. Optional Metadata ---

        subjects_list = [s.find("ns1:subfield[@code='a']", NAMESPACES).text
                         for s in root.findall(".//ns1:datafield[@tag='650']", NAMESPACES)
                         if s.find("ns1:subfield[@code='a']", NAMESPACES) is not None]

        return {
            "isbn": isbn,
            "title": title,
            "author": author,
            "summary": summary_text,
            "pages": page_count,
            "year": pub_year,
            "language": lang,
            "publisher": publisher,
            "subjects": "; ".join(subjects_list) if subjects_list else "",
            "genres": "; ".join(genres_list)
        }
    except:
        return None


def process_directory(input_dir, output_csv):
    files = glob.glob(os.path.join(input_dir, "*.jsonl"))
    if not files:
        print("No files found.")
        return

    all_records = []

    print("Step 1: Scanning files and extracting valid records...")
    for file_path in tqdm(files, desc="Reading Files", unit="file"):
        with open(file_path, 'r', encoding='utf-8') as in_f:
            for line in in_f:
                if line.strip():
                    record = is_valid_record(line)
                    if record:
                        all_records.append(record)

    print(f"\nFound {len(all_records)} total valid records (before deduplication).")

    if not all_records:
        return

    # Write raw CSV
    print(f"Step 2: Writing raw records to {output_csv}...")
    fieldnames = all_records[0].keys()
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(all_records)

    print("Done writing raw file.")

    print("\nStep 3: Starting deduplication (preferring most recent year)...")
    deduplicate_books(output_csv, output_csv)


def deduplicate_books(input_path, output_path):
    try:
        df = pd.read_csv(input_path, dtype={'isbn': str})
        original_count = len(df)
        df['year'] = pd.to_numeric(df['year'], errors='coerce')

        df_sorted = df.sort_values(by=['isbn', 'year'], ascending=[True, False])
        df_deduped = df_sorted.drop_duplicates(subset=['isbn'], keep='first')

        final_count = len(df_deduped)
        print(f"  Original records: {original_count:,}")
        print(f"  Unique records:   {final_count:,}")
        print(f"  Removed records:  {original_count - final_count:,}")

        print(f"  Overwriting {output_path}...")
        df_deduped.to_csv(output_path, index=False, quoting=csv.QUOTE_ALL)
        print("  Deduplication complete.")

    except Exception as e:
        print(f"An error occurred during deduplication: {e}")


if __name__ == "__main__":
    INPUT_DIRECTORY = "./"
    OUTPUT_FILENAME = "filtered_books_dataset.csv"

    if os.path.exists(INPUT_DIRECTORY):
        process_directory(INPUT_DIRECTORY, OUTPUT_FILENAME)
    else:
        print(f"Error: Directory '{INPUT_DIRECTORY}' does not exist.")
