import sqlite3
import csv
from typing import List, Tuple, Any

class Database:
    def __init__(self, db_path: str):
        """Initialize with the path to the SQLite database file."""
        self.db_path = db_path

    def _get_connection(self):
        """Internal helper to get a database connection."""
        return sqlite3.connect(self.db_path)

    def populate_from_csv(self, csv_path: str, table_name: str):
        """
        Populate a database table from a CSV file.
        Automatically creates the table using CSV headers.
        """
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)

            # Prepare SQL components
            columns_sql = ", ".join([f'"{h}" TEXT' for h in headers])
            placeholders = ", ".join(["?"] * len(headers))

            with self._get_connection() as conn:
                cur = conn.cursor()

                # Create table if not exists
                cur.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns_sql});')

                # Insert rows
                for row in reader:
                    cur.execute(
                        f'INSERT INTO "{table_name}" VALUES ({placeholders});',
                        row
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
