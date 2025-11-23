import re

import numpy as np
import pyarrow.parquet as pq
from google.genai import Client, types

from backend.database import Database
from backend.similarity_search import VectorIndex


class BibExplorer:
    def __init__(self, api_key, embedding_dim=768):
        self.vector_index = None
        self.database = None
        self.client = Client(api_key=api_key)
        self.embedding_dim = embedding_dim

        self.base_context = """
        You are a query expert. Your job is to decide whether a query requires a text2sql query, a semantic search, or both.
        If you think only SQL is needed, your answer should include only the identifiers <SQL>...</SQL> with the query in between. 
        If you think only Similarity Search is needed, your answer should include only <SIM>...</SIM> with the entire user input in between. 
        If you think we need both, then please provide <SQL>...</SQL> with the SQL query in between the identifiers, AND <SIM>...</SIM> 
        with the exact part of the user input that should be executed via similarity search.

        Database schema (the only table) in a SQLite3 DB:
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
        - The user will query for books.
        - Only apply filters; never invent fields.
        - Never change, update, delete.
        - Respond with SQL, the fact that similarity search is needed, which you will express with the identifiers <SIM></SIM>, or both. Omit explanation.
        - All SQL has to be of the form "SELECT * FROM books WHERE [your filter]"
        - Use SQL when you can solve the query using the available fields. Use Similarity search when you can not. Use both if you need both.
        
        Examples:
        When the user says 'I want books of 200 pages or shorter', then you answer with '<SQL>SELECT * FROM books WHERE pages <= 200</SQL>'
        When the user says 'I want books about dragons', then you answer '<SIM></SIM>' because clearly you can not answer this using SQL,
        we need the similarity search instead.
        When the user says 'I want books about dragons by astrid lindgren' then you answer '<SQL>SELECT * FROM books WHERE author IS 'Lindgren, Astrid'</SQL><SIM>I want books about dragons</SIM>' 
        so that both is run.
    """

    def init_explorer(self, csv, embedding_path="../data/embeddings_data_parquet"):
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
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=self.base_context
            ),
            contents=query
        )
        return response.text

    def extract_sim(self, text: str):
        return self._extract(text, open_tag="<SIM>", close_tag="</SIM>")

    def extract_sql(self, text: str):
        return self._extract(text, open_tag="<SQL>", close_tag="</SQL>")

    def _extract(self, text: str, open_tag: str, close_tag: str):
        has_open = open_tag in text
        has_close = close_tag in text

        if has_open != has_close:
            raise ValueError("Mismatched SQL markers: both <SQL> and </SQL> are required.")

        if not has_open:
            return None

        m = re.search(fr"{open_tag}(.*?){close_tag}", text, flags=re.DOTALL)
        if not m:
            raise ValueError("Could not extract SQL content.")

        return m.group(1).strip()

    def parse_response(self, response):
        sql = self.extract_sql(response)
        sim = self.extract_sim(response)

        return sql, sim

    def embed_query(self, query):
        embedded_query = self.client.models.embed_content(
            model="gemini-embedding-001",
            contents=[query],
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=self.embedding_dim
            )
        )
        embedded_query = np.array(embedded_query.embeddings[0].values, np.float32)
        return embedded_query

    def query_books(self, query):
        resp = self.prompt_model(query)
        sql, sim = self.parse_response(resp)
        sql_books = []
        sim_books = []
        query_type = None
        if sql:
            # SQL case
            sql_books = self.database.execute_query(sql)
            query_type = "sql"
        if sim:
            # Similarity search case
            search_query = self.embed_query(sim)
            isbns = self.vector_index.search(search_query)
            sim_books = self.database.get_books(isbns)
            query_type = "sim"
        if sql and sim:
            books = [s for s in sql_books if s in sim_books]
            query_type = "sqlsim"
        else:
            books = sql_books or sim_books
        return books, query_type

