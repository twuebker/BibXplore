from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os

from flask_cors import CORS

from explorer.bib_explorer import BibExplorer  # Replace 'your_module_name' with actual filename

app = Flask(__name__)
CORS(app)


explorer = None

def init_explorer():
    """Initialize the BibExplorer once at startup"""
    global explorer

    print("Initializing BibExplorer...")

    load_dotenv()
    api_key = os.environ.get("API_KEY")

    if api_key is None:
        raise ValueError("API_KEY environment variable is not set")

    explorer = BibExplorer(api_key=api_key)
    explorer.init_explorer(
        "./data/filtered_books_dataset.csv",
        "./data/embeddings_data_parquet"
    )

    print("BibExplorer initialized successfully!")

@app.route('/get_books', methods=['POST'])
def get_books():
    try:
        data = request.get_json()
        query = data.get('query', '')

        if not query:
            return jsonify({'error': 'No query provided', 'books': []}), 400

        # Call your existing function
        books, query_type = explorer.query_books(query)

        # Return the results
        return jsonify({
            'books': books,
            'query_type': query_type,
            'count': len(books)
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e), 'books': []}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'explorer_initialized': explorer is not None})

if __name__ == '__main__':
    # Initialize the explorer before starting the server
    init_explorer()

    # Start the Flask app
    print("Starting Flask server on http://localhost:5000")
    app.run(debug=True, port=5000, use_reloader=False)  # use_reloader=False prevents double initialization
