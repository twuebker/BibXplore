import os
import sqlite3
import csv
from typing import List, Tuple, Any

class Database:
    def __init__(self, db_path: str):
        """Initialize with the path to the SQLite database file."""
        os.unlink(db_path)
        self.db_path = db_path
        self.columns = {
            "isbn": "TEXT PRIMARY KEY",
            "title": "TEXT",
            "author": "TEXT",
            "pages": "INTEGER",
            "year": "INTEGER",
            "language": "TEXT",
            "publisher": "TEXT",
            "subjects": "TEXT",
            "genres": "TEXT",
        }

    def _get_connection(self):
        """Internal helper to get a database connection."""
        return sqlite3.connect(self.db_path)

    def populate_from_csv(self, csv_path: str, table_name: str):
        """
        Populate a database table from a CSV file.
        Automatically creates the table using CSV headers.
        """

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            csv_headers = reader.fieldnames

            # Ensure CSV headers match filtered columns (after exclusion)
            filtered_headers = [h for h in csv_headers if h != "summary"]
            if set(filtered_headers) != set(self.columns.keys()):
                raise ValueError("CSV headers do not match provided columns after exclusion")

            # Prepare SQL components
            columns_sql = ", ".join([f'"{name}" {col_type}' for name, col_type in self.columns.items()])
            placeholders = ", ".join(["?"] * len(self.columns))

            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns_sql});')

                # Insert rows
                for row in reader:
                    row_values = [row[h] for h in filtered_headers]  # exclude the column
                    cur.execute(
                        f'INSERT INTO "{table_name}" ({", ".join(filtered_headers)}) VALUES ({placeholders});',
                        row_values
                    )
                conn.commit()

    def execute_query(self, query: str) -> List[Tuple[Any]]:
        """
        Execute any SQL query and return results (if any).
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query)
            results = cur.fetchall()
            return results


    def get_books(self, isbns):
        with self._get_connection() as conn:
            cur = conn.cursor()
            placeholders = ",".join("?" * len(isbns))
            cur.execute(f"SELECT * FROM books WHERE isbn IN ({placeholders})", isbns)
            return cur.fetchall()
