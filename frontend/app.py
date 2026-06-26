import streamlit as st
import httpx
import time

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DocMind",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = "http://localhost:8000/api/v1"

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

/* Reset & base */
*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background: #0d0d0d !important;
    color: #e8e8e8 !important;
    font-family: 'Inter', sans-serif !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #111111 !important;
    border-right: 1px solid #1e1e1e !important;
    padding-top: 0 !important;
}
[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }

/* Main content area */
[data-testid="stMain"] { background: #0d0d0d !important; }
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* Sidebar wordmark */
.sidebar-brand {
    padding: 24px 20px 20px;
    border-bottom: 1px solid #1e1e1e;
    margin-bottom: 12px;
}
.sidebar-brand-name {
    font-size: 15px;
    font-weight: 600;
    color: #ffffff;
    letter-spacing: -0.3px;
}
.sidebar-brand-tag {
    font-size: 11px;
    color: #555;
    margin-top: 2px;
}

/* Upload zone */
.upload-label {
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #555;
    padding: 0 20px;
    margin-bottom: 8px;
}

/* Streamlit file uploader override */
[data-testid="stFileUploader"] {
    margin: 0 16px;
}
[data-testid="stFileUploaderDropzone"] {
    background: #161616 !important;
    border: 1.5px dashed #2a2a2a !important;
    border-radius: 10px !important;
    padding: 20px 12px !important;
    transition: border-color 0.2s;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #444 !important;
}
[data-testid="stFileUploaderDropzone"] > div {
    color: #555 !important;
    font-size: 12px !important;
}
[data-testid="stFileUploaderDropzone"] svg { display: none !important; }
[data-testid="stFileUploaderDropzoneInstructions"] span {
    color: #555 !important;
    font-size: 12px !important;
}

/* Document list */
.doc-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 20px;
    margin: 2px 0;
    border-radius: 0;
    cursor: pointer;
    transition: background 0.15s;
    font-size: 13px;
    color: #aaa;
    border: none;
    background: transparent;
}
.doc-item:hover { background: #1a1a1a; color: #fff; }
.doc-item.active { background: #1a1a1a; color: #fff; }
.doc-icon { font-size: 13px; opacity: 0.6; }

/* Summarize button */
.stButton > button {
    background: transparent !important;
    border: 1px solid #2a2a2a !important;
    color: #888 !important;
    font-size: 11px !important;
    padding: 4px 10px !important;
    border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.15s !important;
    width: 100% !important;
}
.stButton > button:hover {
    border-color: #444 !important;
    color: #ccc !important;
    background: #1a1a1a !important;
}

/* Chat layout */
.chat-wrapper {
    display: flex;
    flex-direction: column;
    height: 100vh;
    max-width: 760px;
    margin: 0 auto;
    padding: 0 20px;
}

.chat-header {
    padding: 28px 0 0;
    text-align: center;
    flex-shrink: 0;
}
.chat-title {
    font-size: 22px;
    font-weight: 600;
    color: #ffffff;
    letter-spacing: -0.5px;
}
.chat-subtitle {
    font-size: 13px;
    color: #555;
    margin-top: 4px;
}

/* Messages */
.messages-area {
    flex: 1;
    overflow-y: auto;
    padding: 32px 0 20px;
    display: flex;
    flex-direction: column;
    gap: 24px;
}

.msg-row {
    display: flex;
    gap: 12px;
    align-items: flex-start;
}
.msg-row.user { flex-direction: row-reverse; }

.avatar {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    flex-shrink: 0;
    margin-top: 2px;
}
.avatar.ai {
    background: #1e1e1e;
    border: 1px solid #2a2a2a;
    color: #888;
}
.avatar.user {
    background: #2563eb;
    color: #fff;
    font-weight: 600;
}

.bubble {
    max-width: 85%;
    font-size: 14px;
    line-height: 1.65;
    color: #e0e0e0;
}
.bubble.ai { color: #d4d4d4; }
.bubble.user {
    background: #1a1a2e;
    border: 1px solid #252540;
    padding: 10px 14px;
    border-radius: 14px 14px 4px 14px;
    color: #e0e0e0;
}

/* Sources */
.sources-row {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 10px;
}
.source-pill {
    font-size: 11px;
    color: #666;
    background: #161616;
    border: 1px solid #222;
    border-radius: 20px;
    padding: 3px 10px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

/* Typing indicator */
.typing-indicator {
    display: flex;
    gap: 5px;
    align-items: center;
    padding: 8px 0;
}
.typing-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #444;
    animation: typing-bounce 1.2s infinite;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing-bounce {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
    30% { transform: translateY(-6px); opacity: 1; }
}

/* Summary card */
.summary-card {
    background: #111;
    border: 1px solid #1e1e1e;
    border-radius: 12px;
    padding: 16px;
    margin-top: 8px;
    font-size: 13px;
    color: #bbb;
    line-height: 1.7;
}
.summary-title {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #555;
    margin-bottom: 10px;
}

/* Chat input */
[data-testid="stChatInput"] {
    background: #111 !important;
    border-top: 1px solid #1a1a1a !important;
    padding: 16px 0 20px !important;
}
[data-testid="stChatInput"] textarea {
    background: #161616 !important;
    border: 1.5px solid #222 !important;
    border-radius: 12px !important;
    color: #e0e0e0 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    padding: 12px 16px !important;
    resize: none !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #333 !important;
    box-shadow: none !important;
    outline: none !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: #444 !important; }
[data-testid="stChatInputSubmitButton"] {
    background: #2563eb !important;
    border-radius: 8px !important;
}

/* Empty state */
.empty-state {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
    color: #333;
    padding: 60px 0;
}
.empty-icon { font-size: 32px; opacity: 0.3; }
.empty-text { font-size: 14px; color: #444; }

/* Processing spinner */
.processing-msg {
    font-size: 12px;
    color: #555;
    padding: 8px 20px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Divider in sidebar */
.sidebar-divider {
    height: 1px;
    background: #1e1e1e;
    margin: 16px 0;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #222; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #333; }

/* Spinner override */
[data-testid="stSpinner"] { display: none !important; }
</style>
""", unsafe_allow_html=True)


# ── API helpers ───────────────────────────────────────────────────────────────

def api_ok():
    try:
        r = httpx.get(f"{API_URL}/ping", timeout=3)
        return r.status_code == 200
    except:
        return False


def ollama_ok():
    try:
        r = httpx.get(f"{API_URL}/ollama/status", timeout=3)
        return r.json().get("ollama_running", False)
    except:
        return False


def upload_pdf(file):
    try:
        files = {"file": (file.name, file.getvalue(), "application/pdf")}
        r = httpx.post(f"{API_URL}/upload", files=files, timeout=180)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def ask_question(question, top_k=5):
    try:
        r = httpx.post(
            f"{API_URL}/ask",
            params={"question": question, "top_k": top_k},
            timeout=180,
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def summarize_doc(filename):
    try:
        r = httpx.post(
            f"{API_URL}/summarize",
            params={"filename": filename},
            timeout=240,
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}


# ── Session state defaults ────────────────────────────────────────────────────

for key, default in {
    "messages": [],
    "uploaded_files": [],
    "active_doc": None,
    "summary_cache": {},
    "show_summary": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    # Brand
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-brand-name">◈ DocMind</div>
        <div class="sidebar-brand-tag">AI Document Analyst</div>
    </div>
    """, unsafe_allow_html=True)

    # Upload
    st.markdown('<div class="upload-label">Documents</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Drop a PDF",
        type=["pdf"],
        label_visibility="collapsed",
    )

    # Auto-process on upload
    if uploaded and uploaded.name not in st.session_state.uploaded_files:
        placeholder = st.empty()
        placeholder.markdown(
            '<div class="processing-msg">⟳ &nbsp;Processing…</div>',
            unsafe_allow_html=True,
        )
        result = upload_pdf(uploaded)
        placeholder.empty()

        if "error" not in result:
            st.session_state.uploaded_files.append(uploaded.name)
            st.session_state.active_doc = uploaded.name
            st.session_state.messages.append({
                "role": "system",
                "content": f"**{uploaded.name}** ready — {result.get('total_pages', 0)} pages, {result.get('total_chunks', 0)} chunks indexed.",
            })
            st.rerun()

    # Document list
    if st.session_state.uploaded_files:
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        for fname in st.session_state.uploaded_files:
            is_active = fname == st.session_state.active_doc
            cls = "doc-item active" if is_active else "doc-item"
            st.markdown(
                f'<div class="{cls}"><span class="doc-icon">◻</span>{fname[:28]}{"…" if len(fname) > 28 else ""}</div>',
                unsafe_allow_html=True,
            )
            if st.button("Summarize", key=f"sum_{fname}"):
                if fname not in st.session_state.summary_cache:
                    with st.spinner(""):
                        res = summarize_doc(fname)
                    if "error" not in res:
                        st.session_state.summary_cache[fname] = res.get("summary", "")
                st.session_state.show_summary = fname
                st.rerun()

    # Bottom status (hidden, background check)
    _ = api_ok()
    _ = ollama_ok()


# ── Main chat area ────────────────────────────────────────────────────────────

st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)

# Header
st.markdown("""
<div class="chat-header">
    <div class="chat-title">What do you want to know?</div>
    <div class="chat-subtitle">Upload a document in the sidebar, then ask anything.</div>
</div>
""", unsafe_allow_html=True)

# Summary panel
if st.session_state.show_summary:
    fname = st.session_state.show_summary
    summary_text = st.session_state.summary_cache.get(fname, "")
    if summary_text:
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-title">Summary · {fname}</div>
            {summary_text.replace(chr(10), '<br>')}
        </div>
        """, unsafe_allow_html=True)
        if st.button("✕ Close summary"):
            st.session_state.show_summary = None
            st.rerun()

# Messages
if not st.session_state.messages:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">◈</div>
        <div class="empty-text">Upload a PDF to get started</div>
    </div>
    """, unsafe_allow_html=True)
else:
    for msg in st.session_state.messages:
        role = msg["role"]

        if role == "system":
            st.markdown(f"""
            <div style="text-align:center;font-size:12px;color:#444;padding:6px 0;">
                {msg["content"]}
            </div>
            """, unsafe_allow_html=True)

        elif role == "user":
            st.markdown(f"""
            <div class="msg-row user">
                <div class="avatar user">S</div>
                <div class="bubble user">{msg["content"]}</div>
            </div>
            """, unsafe_allow_html=True)

        elif role == "assistant":
            sources_html = ""
            if msg.get("sources"):
                pills = "".join([
                    f'<span class="source-pill">◻ {s["filename"]} · p.{s["page"]}</span>'
                    for s in msg["sources"]
                ])
                sources_html = f'<div class="sources-row">{pills}</div>'

            content = msg["content"].replace("\n", "<br>")
            st.markdown(f"""
            <div class="msg-row">
                <div class="avatar ai">◈</div>
                <div class="bubble ai">
                    {content}
                    {sources_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

# Chat input
question = st.chat_input("Ask anything about your documents…")

if question:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": question})

    # Typing animation placeholder
    typing_placeholder = st.empty()
    typing_placeholder.markdown("""
    <div class="msg-row">
        <div class="avatar ai">◈</div>
        <div class="bubble ai">
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Get answer
    result = ask_question(question)
    typing_placeholder.empty()

    if "error" in result:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"Something went wrong: {result['error']}",
            "sources": [],
        })
    else:
        st.session_state.messages.append({
            "role": "assistant",
            "content": result.get("answer", "I couldn't generate an answer."),
            "sources": result.get("sources", []),
        })

    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)