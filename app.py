import streamlit as st
import os
import sys
from dotenv import load_dotenv
import pandas as pd

from explorer.bib_explorer import BibExplorer

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="BibXplorer - Book Search",
    page_icon="📚",
    layout="wide"
)

# Initialize session state
if 'explorer' not in st.session_state:
    st.session_state.explorer = None
    st.session_state.initialized = False

# Title
st.title("📚 BibXplorer")
st.markdown("Intelligent book search using SQL and semantic similarity")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    api_key = st.text_input(
        "Gemini API Key",
        type="password",
        value=os.getenv("GEMINI_API_KEY", ""),
        help="Enter your Google Gemini API key"
    )

    csv_path = st.text_input(
        "Books CSV Path",
        value="data/filtered_books_dataset.csv",
        help="Path to the books CSV file"
    )

    embedding_path = st.text_input(
        "Embeddings Path",
        value="data/embeddings_data_parquet",
        help="Path to the embeddings parquet file"
    )

    if st.button("Initialize Explorer", type="primary"):
        if not api_key:
            st.error("Please provide a Gemini API key")
        elif not os.path.exists(csv_path):
            st.error(f"CSV file not found: {csv_path}")
        elif not os.path.exists(embedding_path):
            st.error(f"Embeddings file not found: {embedding_path}")
        else:
            with st.spinner("Initializing explorer..."):
                try:
                    print("Initializing BibExplorer...")
                    st.session_state.explorer = BibExplorer(api_key=api_key)
                    st.session_state.explorer.init_explorer(
                        csv=csv_path,
                        embedding_path=embedding_path
                    )
                    # Get actual column names from database
                    st.session_state.column_names = st.session_state.explorer.database.columns.keys()
                    st.session_state.initialized = True
                    st.success("✅ BibExplorer initialized successfully!")
                except Exception as e:
                    st.error(f"Error initializing explorer: {str(e)}")

    st.divider()

    # Status indicator
    if st.session_state.initialized:
        st.success("🟢 BibExplorer Ready")
    else:
        st.warning("🔴 BibExplorer Not Initialized")

# Main content
if not st.session_state.initialized:
    st.info("👈 Please configure and initialize the explorer using the sidebar")

    # Example queries
    st.subheader("Example Queries")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**SQL-based queries:**")
        st.code("Books with less than 200 pages")
        st.code("Books published after 2010")
        st.code("Books in English")

    with col2:
        st.markdown("**Semantic search queries:**")
        st.code("Books about dragons")
        st.code("Mystery novels set in Victorian London")
        st.code("Science fiction with time travel")

else:
    # Search interface
    st.subheader("🔍 Search Books")

    query = st.text_input(
        "Enter your query",
        placeholder="e.g., 'Books about artificial intelligence' or 'Books with less than 300 pages'",
        key="search_query"
    )

    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        search_button = st.button("Search", type="primary", use_container_width=True)
    with col2:
        clear_button = st.button("Clear", use_container_width=True)

    if clear_button:
        st.session_state.search_results = None
        st.rerun()

    if search_button and query:
        with st.spinner("Searching..."):
            try:
                results = st.session_state.explorer.query_books(query)
                st.session_state.search_results = results
            except Exception as e:
                st.error(f"Error during search: {str(e)}")

    # Display results
    if 'search_results' in st.session_state and st.session_state.search_results:
        st.divider()

        # Limit to top 10 results
        limited_results = st.session_state.search_results[:10]
        total_results = len(st.session_state.search_results)

        st.subheader(f"📖 Results (showing {len(limited_results)} of {total_results} books)")

        # Convert results to DataFrame for better display
        if limited_results:
            # Get actual column count from results
            num_cols = len(limited_results[0])

            # Adjust columns based on actual data
            if num_cols == 10:
                columns = ["ISBN", "Title", "Author", "Pages", "Year", "Language", "Publisher", "Subjects", "Genres", "Abstract"]
            elif num_cols == 9:
                columns = ["ISBN", "Title", "Author", "Pages", "Year", "Language", "Publisher", "Subjects", "Genres"]
            else:
                columns = [f"Column_{i}" for i in range(num_cols)]

            df = pd.DataFrame(limited_results, columns=columns)

            # Display as expandable cards
            for idx, row in df.iterrows():
                with st.expander(f"**{row['Title']}** by {row['Author']}"):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.markdown(f"**ISBN:** {row['ISBN']}")
                        st.markdown(f"**Author:** {row['Author']}")
                        st.markdown(f"**Publisher:** {row['Publisher']}")
                        if row['Subjects']:
                            st.markdown(f"**Subjects:** {row['Subjects']}")
                        if row['Genres']:
                            st.markdown(f"**Genres:** {row['Genres']}")

                    with col2:
                        st.metric("Pages", row['Pages'])
                        st.metric("Year", row['Year'])
                        st.markdown(f"**Language:** {row['Language']}")

            # Also show as table
            st.divider()
            st.subheader("Table View")
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
    elif 'search_results' in st.session_state and st.session_state.search_results is not None:
        st.info("No results found for your query")

# Footer
st.divider()
st.caption("BibXplorer - Powered by Gemini AI and HNSW vector search")
