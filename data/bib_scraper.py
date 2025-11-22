import requests
import xml.etree.ElementTree as ET
import time
import json
import concurrent.futures
from datetime import datetime, timedelta
from tqdm import tqdm
import threading

# --- CONFIGURATION ---
BASE_URL = "https://data-bib.muenchen.de/oai-pmh"
OUTPUT_FILENAME_TEMPLATE = "oai_records_{start}_{end}.jsonl"
MAX_WORKERS = 33  # Be careful: too many workers might get your IP banned
NAMESPACES = {
    'oai': 'http://www.openarchives.org/OAI/2.0/',
    'marc': 'http://www.loc.gov/MARC21/slim'
}


# ---------------------

def get_earliest_datestamp(base_url):
    """Queries the Identify verb to find the repository start date."""
    try:
        resp = requests.get(base_url, params={'verb': 'Identify'})
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        earliest = root.find('.//oai:earliestDatestamp', NAMESPACES)
        if earliest is not None:
            return earliest.text
    except Exception as e:
        print(f"Warning: Could not auto-detect start date ({e}). Defaulting to 2000-01-01.")
    return "2000-01-01"


def generate_date_chunks(start_date_str):
    """Splits the time range from start_date to Now into yearly chunks."""
    # OAI-PMH date format is usually YYYY-MM-DD or YYYY-MM-DDThh:mm:ssZ
    # We will stick to YYYY-MM-DD for simplicity as it's widely supported.
    start_dt = datetime.strptime(start_date_str[:10], "%Y-%m-%d")
    end_dt = datetime.now()

    chunks = []
    current = start_dt

    while current < end_dt:
        # Create a 1-year chunk
        next_year = current.replace(year=current.year + 1)

        # Ensure we don't go past today
        if next_year > end_dt:
            next_year = end_dt

        # Format: from=YYYY-MM-DD, until=YYYY-MM-DD
        # We subtract one day from 'until' to avoid overlap if needed,
        # but OAI-PMH usually handles inclusive ranges fine.
        chunks.append((
            current.strftime("%Y-%m-%d"),
            next_year.strftime("%Y-%m-%d")
        ))
        current = next_year

    return chunks


def scrape_worker(date_range, progress_bar):
    """
    Worker function to scrape a specific date range.
    """
    from_date, until_date = date_range
    worker_output = OUTPUT_FILENAME_TEMPLATE.format(start=from_date, end=until_date)

    session = requests.Session()
    session.headers.update({'User-Agent': 'OAI-PMH-Harvester/MultiWorker'})

    # Start parameters with date range
    params = {
        'verb': 'ListRecords',
        'metadataPrefix': 'marc_xml',
        'from': from_date,
        'until': until_date
    }

    records_found = 0

    # Write to a worker-specific file to avoid write contention/locking issues
    with open(worker_output, 'w', encoding='utf-8') as f:
        while True:
            try:
                response = session.get(BASE_URL, params=params)

                # Handle 503 Retry-After (Rate Limiting)
                if response.status_code == 503:
                    retry_after = int(response.headers.get('Retry-After', 10))
                    time.sleep(retry_after)
                    continue

                response.raise_for_status()
                root = ET.fromstring(response.content)

                # Check for OAI errors (like noRecordsMatch)
                error = root.find('.//oai:error', NAMESPACES)
                if error is not None:
                    # noRecordsMatch is common for empty years, just finish this worker
                    if error.get('code') != 'noRecordsMatch':
                        # Log real errors if needed
                        pass
                    break

                list_records = root.find('.//oai:ListRecords', NAMESPACES)
                if list_records is None:
                    break

                records = list_records.findall('oai:record', NAMESPACES)
                if not records:
                    break

                # Write batch to disk
                for record in records:
                    record_str = ET.tostring(record, encoding='unicode')
                    # Compact JSON write
                    f.write(json.dumps({"raw_xml": record_str}) + '\n')

                batch_size = len(records)
                records_found += batch_size

                # Update global progress bar safely
                with threading.Lock():
                    progress_bar.update(batch_size)

                # Handle Resumption
                token_element = list_records.find('oai:resumptionToken', NAMESPACES)
                if token_element is not None and token_element.text:
                    params = {
                        'verb': 'ListRecords',
                        'resumptionToken': token_element.text
                    }
                    time.sleep(0.5)  # Be polite
                else:
                    break

            except Exception as e:
                print(f"Error in worker {from_date}: {e}")
                break

    return records_found


def main():
    print(f"Checking repository info at {BASE_URL}...")
    earliest_date = get_earliest_datestamp(BASE_URL)
    print(f"Earliest date detected: {earliest_date}")

    date_chunks = generate_date_chunks(earliest_date)
    print(f"Split into {len(date_chunks)} tasks (years). Launching {MAX_WORKERS} workers.")

    # Initialize a global progress bar (total unknown until we start getting data)
    # We use a shared bar for all threads
    with tqdm(unit="rec", desc="Total Records Harvested") as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all tasks
            futures = [executor.submit(scrape_worker, chunk, pbar) for chunk in date_chunks]

            # Wait for all to complete
            total = 0
            for future in concurrent.futures.as_completed(futures):
                total += future.result()

    print(f"\nAll workers finished. Total records: {total}")
    print("Note: Data is split across multiple files (oai_records_YYYY-MM-DD_...).")
    print("You can merge them using: cat oai_records_*.jsonl > all_records.jsonl")


if __name__ == "__main__":
    main()
