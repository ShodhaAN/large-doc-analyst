import streamlit as st
import httpx
import json

# ── Page Configuration ──────────────────────────────
st.set_page_config(
    page_title="Large Document Analyst",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── API Base URL ─────────────────────────────────────
API_URL = "http://localhost:8000/api/v1"

# ── Custom CSS for better look ───────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .answer-box {
        background-color: #f0f7ff;
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .source-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin: 0.3rem 0;
        font-size: 0.85rem;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 0.5rem;
        border-radius: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)


# ── Helper Functions ─────────────────────────────────

def check_api_health():
    """Check if the FastAPI server is running"""
    try:
        response = httpx.get(f"{API_URL}/ping", timeout=5.0)
        return response.status_code == 200
    except:
        return False


def check_ollama():
    """Check if Ollama is running"""
    try:
        response = httpx.get(f"{API_URL}/ollama/status", timeout=5.0)
        data = response.json()
        return data.get("ollama_running", False)
    except:
        return False


def upload_pdf(file):
    """Upload a PDF to the FastAPI backend"""
    try:
        files = {"file": (file.name, file.getvalue(), "application/pdf")}
        response = httpx.post(
            f"{API_URL}/upload",
            files=files,
            timeout=120.0
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def ask_question(question: str, top_k: int = 5):
    """Ask a question about uploaded documents"""
    try:
        response = httpx.post(
            f"{API_URL}/ask",
            params={"question": question, "top_k": top_k},
            timeout=120.0
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def summarize_document(filename: str):
    """Get a summary of a document"""
    try:
        response = httpx.post(
            f"{API_URL}/summarize",
            params={"filename": filename},
            timeout=180.0
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def get_stats():
    """Get vector store statistics"""
    try:
        response = httpx.get(f"{API_URL}/stats", timeout=10.0)
        return response.json()
    except:
        return {}


# ── Main App ─────────────────────────────────────────

def main():

    # Header
    st.markdown(
        '<div class="main-header">📄 Large Document Analyst</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="sub-header">Upload PDFs and ask questions using AI</div>',
        unsafe_allow_html=True
    )

    # ── Status Bar ───────────────────────────────────
    col1, col2, col3 = st.columns(3)

    with col1:
        api_ok = check_api_health()
        if api_ok:
            st.success("✅ API Server: Running")
        else:
            st.error("❌ API Server: Not running")

    with col2:
        ollama_ok = check_ollama()
        if ollama_ok:
            st.success("✅ Ollama: Running")
        else:
            st.warning("⚠️ Ollama: Not running")

    with col3:
        stats = get_stats()
        total = stats.get("total_embeddings", 0)
        st.info(f"📊 Chunks indexed: {total}")

    st.divider()

    # ── Two Column Layout ────────────────────────────
    left_col, right_col = st.columns([1, 2])

    # ── LEFT COLUMN — Upload & Documents ────────────
    with left_col:
        st.subheader("📂 Upload Documents")

        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=["pdf"],
            help="Upload any PDF document to analyze"
        )

        if uploaded_file is not None:
            # Show file info
            file_size = len(uploaded_file.getvalue()) / 1024 / 1024
            st.write(f"📄 **{uploaded_file.name}**")
            st.write(f"Size: {file_size:.2f} MB")

            # Upload button
            if st.button("🚀 Process PDF", type="primary"):
                with st.spinner("Processing PDF... This may take a moment!"):
                    result = upload_pdf(uploaded_file)

                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    st.success("✅ PDF processed successfully!")
                    st.write(f"📑 Pages: **{result.get('total_pages', 0)}**")
                    st.write(f"🔢 Chunks: **{result.get('total_chunks', 0)}**")
                    st.write(f"🧠 Embeddings: **{result.get('embeddings_stored', 0)}**")

                    # Save filename to session
                    if "uploaded_files" not in st.session_state:
                        st.session_state.uploaded_files = []
                    if uploaded_file.name not in st.session_state.uploaded_files:
                        st.session_state.uploaded_files.append(uploaded_file.name)

        st.divider()

        # ── Uploaded Files List ──────────────────────
        st.subheader("📚 Uploaded Documents")

        if "uploaded_files" not in st.session_state:
            st.session_state.uploaded_files = []

        if st.session_state.uploaded_files:
            for filename in st.session_state.uploaded_files:
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    st.write(f"📄 {filename}")
                with col_b:
                    if st.button("📝 Summarize", key=f"sum_{filename}"):
                        with st.spinner("Generating summary..."):
                            summary_result = summarize_document(filename)

                        if "error" in summary_result:
                            st.error(f"Error: {summary_result['error']}")
                        else:
                            st.session_state.current_summary = summary_result
        else:
            st.info("No documents uploaded yet.\nUpload a PDF to get started!")

    # ── RIGHT COLUMN — Chat Interface ────────────────
    with right_col:
        st.subheader("💬 Ask Questions")

        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Show summary if available
        if "current_summary" in st.session_state:
            summary = st.session_state.current_summary
            with st.expander("📝 Document Summary", expanded=True):
                st.write(summary.get("summary", ""))
                st.caption(
                    f"Analyzed {summary.get('chunks_analyzed', 0)} chunks "
                    f"from {summary.get('filename', '')}"
                )
            del st.session_state.current_summary

        # Display chat history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.write(message["content"])
                else:
                    with st.chat_message("assistant"):
                        st.write(message["content"])

                        # Show sources
                        if message.get("sources"):
                            st.markdown("**📍 Sources:**")
                            for source in message["sources"]:
                                st.markdown(
                                    f'<div class="source-box">'
                                    f'📄 {source["filename"]} — Page {source["page"]}'
                                    f'</div>',
                                    unsafe_allow_html=True
                                )

        # Question input
        question = st.chat_input(
            "Ask a question about your documents..."
        )

        if question:
            # Check requirements
            if not api_ok:
                st.error("❌ API server is not running!")
                return

            if not ollama_ok:
                st.warning("⚠️ Ollama is not running. Start it with: ollama serve")
                return

            # Add user message
            st.session_state.messages.append({
                "role": "user",
                "content": question
            })

            # Get answer
            with st.spinner("🤔 Thinking..."):
                result = ask_question(question)

            if "error" in result:
                st.error(f"Error: {result['error']}")
            else:
                answer = result.get("answer", "No answer generated")
                sources = result.get("sources", [])
                confidence = result.get("confidence", "medium")

                # Add assistant message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                    "confidence": confidence
                })

            # Refresh to show new messages
            st.rerun()

        # Clear chat button
        if st.session_state.messages:
            if st.button("🗑️ Clear Chat"):
                st.session_state.messages = []
                st.rerun()


if __name__ == "__main__":
    main()