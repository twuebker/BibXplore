from google.genai import Client, types

from database import Database
from similarity_search import VectorIndex
import pyarrow.parquet as pq
import numpy as np

class Explorer:
    def __init__(self, api_key, embedding_dim=768):
        self.vector_index = None
        self.database = None
        self.client = Client(api_key=api_key)
        self.embedding_dim = embedding_dim

        self.base_context = """
        You are a query expert. Your job is to decide whether a query requires a text2sql query or semantic search.
        If you come to the conclusion that answering the query requires text2sql, provide the SQL. Otherwise, answer with exactly "NO SQL."

        Database schema (the only table):
        TABLE books (
            isbn INTEGER,
            title TEXT, 
            author TEXT,
            pages INTEGER,
            year INTEGER,
            language TEXT,
            publisher TEXT,
            subjects TEXT,
            genres TEXT
       )

        Rules:
        - The user will query for a book.
        - Only apply filters; never invent fields.
        - Never change, update, delete.
        - Respond with SQL or the fact that similarity search is needed, which you will express with "NO SQL.". No explanation.
        - All SQL has to be of the form "SELECT * FROM books WHERE [your filter]
        
        Examples:
        When the user says 'I want books of 200 pages or shorter', then you answer with 'SELECT * FROM books WHERE pages <= 200'
        When the user says 'I want books about dragons, then you answer 'NO SQL' because clearly you can not answer this using SQL,
        we need the similarity search instead.
    """

    def init_explorer(self, csv, embedding_path="/data/embeddings_data_parquet"):
        table = pq.read_table(embedding_path)
        isbns = table.column('isbn').to_pylist()

        raw_vectors = table.column('embedding').to_pylist()
        vectors = [np.array(v, dtype=np.float32) for v in raw_vectors]

        self.vector_index = VectorIndex()
        self.vector_index.build_index(isbns, vectors)

        self.database = Database("books.db")
        self.database.populate_from_csv(csv, "books")

    def prompt_model(self, query) -> str:
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                system_instruction=self.base_context
            ),
            contents=query
        )
        return response.text

    def parse_sql_response(self, response):
        return response

    def embed_query(self, query):
        embedded_query = self.client.models.embed_content(
            model="gemini-embedding-001",
            contents=[query],
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=self.embedding_dim
            )
        )

        return embedded_query

    def query_books(self, query):
        resp = self.prompt_model(query)
        if "SELECT" in resp:
            # SQL case
            sql_query = self.parse_sql_response(resp)
            books = self.database.execute_query(sql_query)
        else:
            # Similarity search case
            search_query = self.embed_query(query)
            isbns = self.vector_index.search(search_query)
            books = self.database.get_books(isbns)
        return books

