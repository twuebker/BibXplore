import os
import unittest

from dotenv import load_dotenv

from explorer.bib_explorer import BibExplorer


class TestExplorerEndToEnd(unittest.TestCase):

    def setUp(self):
        """
        Prepare a temporary CSV + temporary DB.
        """
        # Create a temp CSV containing a tiny books table

        load_dotenv()
        api_key = os.environ.get("API_KEY")
        if api_key is None:
            raise ValueError("API_KEY environment variable is not set")

        self.explorer = BibExplorer(api_key=api_key)

        self.explorer.init_explorer("../data/filtered_books_dataset.csv", "../data/embeddings_data_parquet")



    def tearDown(self):
        """Clean temporary files."""
        os.unlink("books.db")

    # -----------------------------
    # TEST 1: SQL PATH
    # -----------------------------
    def test_sql_query(self):
        """
        Test that a prompt requiring SQL is executed using the database.
        """
        # Run query
        results = self.explorer.query_books("I want a short book, preferably less than 200 pages")

        self.assertLess(results[0][3], 200)

    # -----------------------------
    # TEST 2: SIMILARITY SEARCH PATH
    # -----------------------------
    def test_similarity_query(self):
        """
        Test that a prompt requiring semantic search is handled with embedding + vector search.
        """
        # Run query
        results = self.explorer.query_books("I want books about dragons")
        self.assertEqual(10, len(results))

    def test_both(self):
        """
        Test that a prompt requiring semantic search is handled with embedding + vector search.
        """
        # Run query
        results = self.explorer.query_books("I want books about dragons with less than 200 pages")
        self.assertEqual(9, len(results))



if __name__ == "__main__":
    unittest.main()
