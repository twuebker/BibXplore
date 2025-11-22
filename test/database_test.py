import unittest
import os
import tempfile
import sqlite3
from explorer.database import Database

class TestDatabase(unittest.TestCase):

    def setUp(self):
        """Create a temporary database file before each test."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.db_path = self.temp_db.name
        self.db = Database(self.db_path)

        self.csv_path = "../data/filtered_books_dataset.csv"
        self.table_name = "books"

    def tearDown(self):
        """Delete temporary files after test."""
        try:
            os.unlink(self.db_path)
        except FileNotFoundError:
            pass

    def test_populate_and_query(self):
        """Test populating from CSV and querying data."""
        self.db.populate_from_csv(self.csv_path, self.table_name)

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='books'")
        table = cur.fetchone()
        self.assertIsNotNone(table, "Table 'books' should exist after population")

        cur.execute(f"SELECT COUNT(*) FROM {self.table_name}")
        (count,) = cur.fetchone()
        self.assertGreater(count, 0, "CSV load should insert rows")

        conn.close()

    def test_execute_query(self):
        """Test execute_query returns expected results."""
        self.db.populate_from_csv(self.csv_path, self.table_name)

        results = self.db.execute_query(f"SELECT * FROM {self.table_name} LIMIT 5")
        self.assertTrue(len(results) > 0, "execute_query should return rows")

    def test_get_books(self):
        """Test get_books using a few ISBNs known from the dataset."""
        self.db.populate_from_csv(self.csv_path, self.table_name)

        all_rows = self.db.execute_query(f"SELECT isbn FROM {self.table_name} LIMIT 1")
        isbn = all_rows[0][0]

        results = self.db.get_books((isbn,))
        self.assertEqual(len(results), 1, "get_books should return the matching book")

if __name__ == "__main__":
    unittest.main()
