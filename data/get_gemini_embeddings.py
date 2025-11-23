import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()
client = genai.Client()

# --- Data ---
user_query = "a book about detectives"

library = [
    "Pride and Prejudice",
    "The Great Gatsby",
    "The Hobbit",
    "1984",
    "A Game of Thrones",
    "The Catcher in the Rye",
    "Tod im Museum - Ein Fall für Skarabäus Lampe",
    "This Book is about Dragons",
    """Tod im Museum - Ein Fall für Skarabäus Lampe
    »Zwei tote Archäologen in so kurzer Zeit – das riecht fischig!«
Überraschend stirbt der Vater von Skarabäus Lampe, ein bekannter Archäologe. Als es bei der Trauerfeier im Museum einen zweiten Toten gibt, ist das Misstrauen des Detektivs geweckt. Einmal mehr muss er ermitteln. Unterdessen wird die Stadt von einer Welle sozialer Aufwallung und Wut erfasst...
Es gibt Unruhen! Nach einem Ausbruch der gefürchteten Arbeiterkrankheit und ausbleibender Hilfe vom Magistrat, gehen die Armen auf die Straße. Eine Welle der Wut, die Straßenbarrikaden, brennende Dreischnecks und fliegendes Gemüse mit sich führt, rollt durch Überstadt. Als der Vater von Skarabäus Lampe, berühmter Archäologe und Ehrenbürger der Stadt, plötzlich stirbt, ist der Detektiv nach Jahren der Entfremdung völlig ..."""
]

requested_dim = 768

# --- 1. Embed the User Query (RETRIEVAL_QUERY) ---
print("Embedding Query...")
query_result = client.models.embed_content(
    model="gemini-embedding-001",
    contents=[user_query],
    config=types.EmbedContentConfig(
        task_type="RETRIEVAL_QUERY",  # Optimized for search questions
        output_dimensionality=requested_dim
    )
)
query_embedding = np.array([e.values for e in query_result.embeddings])

# --- 2. Embed the Library (RETRIEVAL_DOCUMENT) ---
print("Embedding Library...")
library_result = client.models.embed_content(
    model="gemini-embedding-001",
    contents=library,
    config=types.EmbedContentConfig(
        task_type="RETRIEVAL_DOCUMENT",  # Optimized for content to be found
        output_dimensionality=requested_dim
    )
)
library_embeddings = np.array([e.values for e in library_result.embeddings])

# --- 3. Conditional Normalization ---
# Note: We apply normalization to both the query matrix and library matrix independently
current_dim = query_embedding.shape[1]
print(f"Current dimensionality: {current_dim}")

if current_dim != 3072:
    print("Dimension is not 3072. Applying manual NumPy normalization...")

    # Normalize Query
    q_norms = np.linalg.norm(query_embedding, axis=1, keepdims=True)
    query_embedding = query_embedding / q_norms

    # Normalize Library
    l_norms = np.linalg.norm(library_embeddings, axis=1, keepdims=True)
    library_embeddings = library_embeddings / l_norms
else:
    print("Dimension is 3072. Skipping manual normalization.")

# --- 4. Calculation & Output ---
# Calculate similarity between the single query vector and all library vectors
scores_matrix = cosine_similarity(query_embedding, library_embeddings)
scores = scores_matrix[0]

ranked_results = []
for i, score in enumerate(scores):
    # Truncate long text for cleaner display
    display_text = library[i][:60] + "..." if len(library[i]) > 60 else library[i]
    ranked_results.append((display_text, score))

ranked_results.sort(key=lambda x: x[1], reverse=True)

print(f"\nQuery: '{user_query}'\n")
for text, score in ranked_results:
    print(f"{score:.4f} | {text}")

print(f"\nBest Match: {ranked_results[0][0]}")
