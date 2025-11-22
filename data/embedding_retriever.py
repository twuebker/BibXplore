import pandas as pd
from google import genai
from google.genai import types
from tqdm import tqdm
import time
import os
import glob
from dotenv import load_dotenv

load_dotenv()
client = genai.Client()

# Configuration
INPUT_CSV = "filtered_books_dataset.csv"
OUTPUT_DIR = "embeddings_data_parquet"
BATCH_SIZE = 50
EMBEDDING_DIM = 768

def create_embedding_text(row):
    return f"""Title: {row.get('title', '') or ''}
Author: {row.get('author', '') or ''}
Genre: {row.get('genres', '') or ''}
Subjects: {row.get('subjects', '') or ''}
Summary: {row.get('summary', '') or ''}"""


def get_processed_isbns(output_dir):
    """
    Scans the output directory for any existing parquet files
    and collects all ISBNs that are already done.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        return set()

    # Find all .parquet files in the folder
    files = glob.glob(os.path.join(output_dir, "*.parquet"))
    if not files:
        return set()

    print(f"   Scanning {len(files)} existing parquet chunks to find processed ISBNs...")

    all_isbns = set()
    # Read only the 'isbn' column from all files for speed
    # pd.read_parquet can read a whole folder or list of files
    try:
        # We iterate to handle potential corrupted individual files gracefully
        for f in files:
            try:
                df_chunk = pd.read_parquet(f, columns=['isbn'])
                all_isbns.update(df_chunk['isbn'].astype(str).values)
            except Exception as e:
                print(f"     Warning: Could not read chunk {f}: {e}")
    except Exception as e:
        print(f"   Warning reading existing files: {e}")

    return all_isbns


def process_and_save(df, output_dir, batch_size=50):
    df['text_to_embed'] = df.apply(create_embedding_text, axis=1)
    records = df.to_dict('records')
    total_records = len(records)

    # Iterate through the data
    for i in tqdm(range(0, total_records, batch_size), desc="Processing Batches"):
        batch_records = records[i: i + batch_size]
        batch_texts = [r['text_to_embed'] for r in batch_records]

        # --- API Call with Retry (Same as before) ---
        vectors = None
        while True:
            try:
                response = client.models.embed_content(
                    model="gemini-embedding-001",
                    contents=batch_texts,
                    config=types.EmbedContentConfig(
                        task_type="RETRIEVAL_DOCUMENT",
                        output_dimensionality=EMBEDDING_DIM
                    )
                )
                vectors = [e.values for e in response.embeddings]
                time.sleep(0.2)
                break
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    print(f"\n[!] Rate limit. Waiting 60s...")
                    time.sleep(60)
                else:
                    print(f"\n[!] Critical error in batch {i}: {e}")
                    break

        if not vectors:
            continue  # Skip saving if batch failed completely

        # --- Save Batch as Parquet Chunk ---
        chunk_df = pd.DataFrame({
            'isbn': [str(r['isbn']) for r in batch_records],
            'embedding': vectors
        })

        # Unique filename per batch: "part_{index}.parquet"
        # We use the starting index 'i' to ensure unique names
        filename = os.path.join(output_dir, f"part_{i}.parquet")

        chunk_df.to_parquet(filename, index=False)


def main():
    if not os.path.exists(INPUT_CSV):
        print(f"File {INPUT_CSV} not found.")
        return

    print("1. Loading Input Data...")
    df = pd.read_csv(INPUT_CSV)
    df['isbn'] = df['isbn'].astype(str)

    print("2. Checking Resume State...")
    processed_isbns = get_processed_isbns(OUTPUT_DIR)
    print(f"   Found {len(processed_isbns)} records already processed.")

    # Filter out finished ISBNs
    df_to_process = df[~df['isbn'].isin(processed_isbns)].copy()

    if len(df_to_process) == 0:
        print("   All records processed! Exiting.")
        return

    print(f"   Resuming... {len(df_to_process)} records left.")
    print("3. Starting Processing...")

    process_and_save(df_to_process, OUTPUT_DIR, batch_size=BATCH_SIZE)

    print("\nDone.")
    print(f"You can read the full dataset later using: df = pd.read_parquet('{OUTPUT_DIR}')")


if __name__ == "__main__":
    main()
