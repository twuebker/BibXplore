import csv
import json
import os
import xml.etree.ElementTree as ET
import re
import requests
from dotenv import load_dotenv

GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"


def extract_primary_isbn(xml_string):
    """
    Extracts a single ISBN from MARCXML.
    Prefers ISBN-13 (especially 978/979), otherwise falls back to ISBN-10.
    """
    NS = {
        "oai": "http://www.openarchives.org/OAI/2.0/",
        "marc": "http://www.loc.gov/MARC21/slim"
    }

    root = ET.fromstring(xml_string)

    # extract all ISBNs
    isbns = []
    for df in root.findall(".//marc:datafield[@tag='020']", NS):
        for sf in df.findall("marc:subfield[@code='a']", NS):
            if sf.text:
                # normalize (remove hyphens/spaces)
                clean = re.sub(r"[^0-9Xx]", "", sf.text)
                isbns.append(clean)

    if not isbns:
        return None

    # classify them
    isbn13 = [i for i in isbns if len(i) == 13]
    isbn13_978 = [i for i in isbn13 if i.startswith(("978", "979"))]
    isbn10 = [i for i in isbns if len(i) == 10]

    # priority order
    if isbn13_978:
        return isbn13_978[0]
    if isbn13:
        return isbn13[0]
    if isbn10:
        return isbn10[0]

    return isbns[0]

def isbns_from_file(filename):
    records = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    results = []

    for record in records:
        xml = record.get("raw_xml")
        isbn = extract_primary_isbn(xml) if xml else None

        results.append({
            "isbn": isbn
        })

    return results

def query_google_books(isbn, api_key):
    if not api_key:
        raise ValueError("API key is required")
    params = {"q": f"ISBN:{isbn}", "key": api_key}

    response = requests.get(GOOGLE_BOOKS_URL, params=params)

    if response.status_code != 200:
        print(f"Error for ISBN {isbn}: HTTP {response.status_code}")
        return None

    data = response.json()

    if "items" not in data or len(data["items"]) == 0:
        return None

    # first result
    volume = data["items"][0]["volumeInfo"]

    return {
        "isbn": isbn,
        "title": volume.get("title"),
        "subtitle": volume.get("subtitle"),
        "authors": ", ".join(volume.get("authors", [])),
        "publisher": volume.get("publisher"),
        "publishedDate": volume.get("publishedDate"),
        "description": volume.get("description"),
        "pageCount": volume.get("pageCount"),
        "categories": ", ".join(volume.get("categories", [])),
        "language": volume.get("language"),
        "google_books_id": data["items"][0].get("id")
    }


def main(ISBNs, api_key, output_csv, missing_csv):
    books = []
    missing = []

    for isbn in ISBNs:
        print(f"Suche ISBN {isbn} ...")
        info = query_google_books(isbn, api_key)

        if info is None:
            missing.append({"isbn": isbn})
        else:
            books.append(info)


    # CSV: Found Books
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=books[0].keys() if books else ["isbn"])
        writer.writeheader()
        for row in books:
            writer.writerow(row)

    # CSV: Missing ISBNs
    with open(missing_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["isbn"])
        writer.writeheader()
        for row in missing:
            writer.writerow(row)

    print(f"- {len(books)} Books found in {output_csv}")
    print(f"- {len(missing)} Books missing in {missing_csv}")


if __name__ == "__main__":
    load_dotenv("../.env")
    api_key = os.environ.get("API_KEY")
    ISBNs = isbns_from_file("oai_records_2022-11-16_2023-11-16.jsonl")
    main(ISBNs, api_key, output_csv="out.csv", missing_csv="missing.csv")
