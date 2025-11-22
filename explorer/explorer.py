from google.genai import Client, types

from database import Database
from similarity_search import VectorIndex


class Explorer:
    def __init__(self, api_key):
        self.vector_index = None
        self.database = None
        self.client = Client(api_key=api_key)

        self.base_context = """
        You are a query expert. Your job is to decide whether a query requires a text2sql query or semantic search.
        If you come to the conclusion that answering the query requires text2sql, provide the SQL. Otherwise, answer with exactly "NO SQL."

        Database schema (the only table):
        TABLE books (
            isbn INTEGER,
            summary TEXT,
            product TEXT,
            quantity INTEGER,
            price FLOAT,
            order_date DATE
        )

        Rules:
        - The user will query for a book.
        - Only apply filters; never invent fields.
        - Never change, update, delete.
        - Respond with SQL or the fact that similarity search is needed, which you will express with "NO SQL.". No explanation.
    """

    def init_explorer(self, vectors, csv):
        self.vector_index = VectorIndex()
        self.vector_index.build_index(vectors)

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
        # TODO
        return ""

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
        return resp

