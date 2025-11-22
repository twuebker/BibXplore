import streamlit as st
import os
import sys
import logging
from dotenv import load_dotenv
import pandas as pd

from explorer.bib_explorer import BibExplorer

# Load environment variables
load_dotenv()

# Configure logging to output to the console/terminal
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="BibXplorer - Book Search",
    page_icon="📚",
    layout="wide"
)

# Custom CSS for vertical alignment and centering of pagination controls
st.markdown("""
    <style>
    .stButton button {
        height: 100%;
        padding-top: 0;
        padding-bottom: 0;
    }
    div[data-testid="column"] {
        display: flex;
        align-items: center;
        justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'explorer' not in st.session_state:
    st.session_state.explorer = None
    st.session_state.initialized = False
if 'page_number' not in st.session_state:
    st.session_state.page_number = 0
if 'query_type' not in st.session_state:
    st.session_state.query_type = None
# Initialize the input key if not present
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""


def initialize_app():
    """Initialize the BibExplorer automatically in the backend."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    # Default paths - ensure these exist in your deployment environment
    csv_path = "data/filtered_books_dataset.csv"
    embedding_path = "data/embeddings_data_parquet"

    if not api_key:
        st.error("Service Configuration Error: API Key missing.")
        logger.error("Gemini API Key not found in environment variables.")
        return

    if not os.path.exists(csv_path):
        st.error("Service Configuration Error: Data source missing.")
        logger.error(f"CSV file not found at: {csv_path}")
        return

    if not os.path.exists(embedding_path):
        st.error("Service Configuration Error: Embeddings data missing.")
        logger.error(f"Embeddings file not found at: {embedding_path}")
        return

    try:
        logger.info("Starting BibExplorer backend initialization...")
        explorer = BibExplorer(api_key=api_key)
        explorer.init_explorer(
            csv=csv_path,
            embedding_path=embedding_path
        )
        st.session_state.explorer = explorer
        st.session_state.column_names = explorer.database.columns.keys()
        st.session_state.initialized = True
        logger.info("BibExplorer backend initialized successfully.")

    except Exception as e:
        st.error("System Error: Unable to initialize search engine.")
        logger.error(f"Initialization failed: {str(e)}", exc_info=True)

# Run initialization automatically on app load
if not st.session_state.initialized:
    with st.spinner("Connecting to library database..."):
        initialize_app()

# Callback to clear search
def clear_search():
    st.session_state.search_results = None
    st.session_state.query_type = None
    st.session_state.page_number = 0
    st.session_state.search_query = ""

# Title
st.title("📚 BibXplorer")
st.markdown("Intelligent book search using SQL and semantic similarity")

# Main content
if not st.session_state.initialized:
    st.warning("⚠️ Search service is currently unavailable.")
else:
    # Search interface
    st.subheader("🔍 Search Books")

    # Text input bound to session state
    query = st.text_input(
        "Enter your query",
        placeholder="e.g., 'Books about artificial intelligence' or 'Books with less than 300 pages'",
        key="search_query",
        label_visibility="collapsed"
    )

    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        search_button = st.button("Search", type="primary", use_container_width=True)
    with col2:
        # Use on_click callback to clear state BEFORE the rerun happens
        clear_button = st.button("Clear", use_container_width=True, on_click=clear_search)

    if search_button and query:
        with st.spinner("Searching..."):
            try:
                logger.info(f"Processing user query: {query}")
                st.session_state.page_number = 0

                results, q_type = st.session_state.explorer.query_books(query)

                st.session_state.search_results = results
                st.session_state.query_type = q_type

                logger.info(f"Query ({q_type}) found {len(results) if results else 0} matches.")
            except Exception as e:
                st.error("An error occurred while processing your search.")
                logger.error(f"Search execution error: {str(e)}", exc_info=True)

    # Display results
    if 'search_results' in st.session_state and st.session_state.search_results:
        st.divider()

        display_results = st.session_state.search_results
        current_query_type = st.session_state.get('query_type', 'unknown')

        if display_results:
            # Get actual column count from results
            num_cols = len(display_results[0])

            if num_cols == 10:
                columns = ["ISBN", "Title", "Author", "Pages", "Year", "Language", "Publisher", "Subjects", "Genres", "Abstract"]
            elif num_cols == 9:
                columns = ["ISBN", "Title", "Author", "Pages", "Year", "Language", "Publisher", "Subjects", "Genres"]
            else:
                columns = [f"Column_{i}" for i in range(num_cols)]

            full_df = pd.DataFrame(display_results, columns=columns)

            if 'Year' in full_df.columns:
                full_df['Year'] = pd.to_numeric(full_df['Year'], errors='coerce')
            if 'Pages' in full_df.columns:
                full_df['Pages'] = pd.to_numeric(full_df['Pages'], errors='coerce')

            total_results = len(full_df)

            # --- Sorting UI ---
            col_header, col_sort_field, col_sort_order = st.columns([4, 2, 2])

            with col_header:
                # Using markdown to create a new line after the colon
                if current_query_type == "sim": # Assuming "sim" is the code for semantic search
                   st.markdown(f"### Similarity Search\nTop {total_results} results (most relevant from top to bottom)")
                elif current_query_type == "semantic": # Handling previous code "semantic" just in case
                   st.markdown(f"### Similarity Search\nTop {total_results} results (most relevant from top to bottom)")
                elif current_query_type == "sql":
                    st.markdown(f"### SQL Search:\nAll {total_results} results found")
                elif current_query_type == "sqlsim":
                    st.markdown(f"### Similarity and SQL Search\nTop {total_results} results (most relevant from top to bottom)")
                else:
                    st.markdown(f"### Results:\n({total_results} books shown)")

            with col_sort_field:
                sort_col = st.selectbox("Sort by", options=columns,
                                        index=columns.index("Year") if "Year" in columns else 0)

            with col_sort_order:
                sort_asc = st.selectbox("Order", options=["Ascending", "Descending"], index=1) == "Ascending"

            full_df = full_df.sort_values(by=sort_col, ascending=sort_asc)

            # --- Pagination ---
            items_per_page = 10
            total_pages = (total_results + items_per_page - 1) // items_per_page

            start_idx = st.session_state.page_number * items_per_page
            end_idx = start_idx + items_per_page

            page_df = full_df.iloc[start_idx:end_idx]

            st.dataframe(
                page_df,
                use_container_width=True,
                hide_index=True
            )

            # Pagination Controls
            if total_pages > 1:
                st.markdown("<br>", unsafe_allow_html=True)

                spacer_left, prev_col, info_col, next_col, spacer_right = st.columns([4, 1, 2, 1, 4])

                with prev_col:
                    if st.button("◀", disabled=st.session_state.page_number == 0, use_container_width=True,
                                 key="prev_btn_bottom"):
                        st.session_state.page_number -= 1
                        st.rerun()

                with info_col:
                    st.markdown(
                        f"<div style='text-align: center; font-weight: bold;'>{st.session_state.page_number + 1} / {total_pages}</div>",
                        unsafe_allow_html=True
                    )

                with next_col:
                    if st.button("▶", disabled=st.session_state.page_number == total_pages - 1,
                                 use_container_width=True, key="next_btn_bottom"):
                        st.session_state.page_number += 1
                        st.rerun()

    elif 'search_results' in st.session_state and st.session_state.search_results is not None:
        st.info("No results found for your query")

# Footer
st.divider()
st.caption("BibXplorer - Powered by Gemini AI and HNSW vector search")
