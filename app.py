"""Uzhavan: a PDF-first agriculture schemes assistant."""
from pathlib import Path
import json
import streamlit as st
from dotenv import load_dotenv
from agri.retrieval import build_index, DocumentError
from agri.generation import generate

load_dotenv()
st.set_page_config(page_title='Uzhavan | Scheme Assistant', page_icon='🌾', layout='wide')
st.markdown('''<style>
.stApp {background:#f7f9f5; color:#193b2b}
[data-testid="stSidebar"] {background:#163d2c}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,[data-testid="stSidebar"] label {color:#eef6ed!important}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {color:#d1e1d4!important}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] p,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small {color:#193b2b!important}
[data-testid="stSidebar"] button {border-radius:8px}
[data-testid="stSidebar"] button p {color:#193b2b!important}
[data-testid="stSidebar"] button[kind="primary"] p {color:#fff!important}
.block-container {padding-top:2.5rem; max-width:1250px}
@media (max-width:640px) {.block-container {padding-top:5rem} .hero {padding:22px} .hero h1 {font-size:28px}}
.hero {background:#e4efdf; border-left:5px solid #729e4b; border-radius:12px; padding:28px 32px; margin-bottom:24px}
.hero small {font-size:12px; letter-spacing:2px; color:#43653b}
.hero h1 {font-size:34px; padding:8px 0; color:#163d2c}
.hero p {margin:0; color:#496444; font-size:16px}
[data-testid="stChatMessage"] {border:1px solid #e0e8dc; border-radius:12px; background:#fff}
[data-testid="stMetric"] {background:#edf2e9; padding:12px; border-radius:10px}
</style>''', unsafe_allow_html=True)

for key, value in {'messages': [], 'index': None, 'stats': None, 'is_demo': False}.items():
    if key not in st.session_state:
        st.session_state[key] = value


def install(files, demo=False):
    # Replace only after a successful build; never corrupt an existing index on error.
    index, stats = build_index(files)
    st.session_state.update(index=index, stats=stats, is_demo=demo, messages=[])

with st.sidebar:
    st.title('Uzhavan')
    st.caption('AGRICULTURE • KNOWLEDGE DESK')
    st.divider()
    st.subheader('Your documents')
    uploads = st.file_uploader('Upload scheme PDFs', type=['pdf'], accept_multiple_files=True,
                               help='Text PDFs, up to 20 MB each and 60 MB total. OCR is not included.')
    st.caption('Select files, then index. Uploading alone does not change the active index.')
    if st.button('Index Documents', type='primary', use_container_width=True):
        try:
            with st.spinner('Reading pages and building the local index...'):
                install([(f.name, f.getvalue()) for f in uploads])
            st.success('Documents indexed.')
        except DocumentError as exc:
            st.error(str(exc))
    if st.button('Try a sample PDF', use_container_width=True):
        demo = Path(__file__).parent / 'docs' / 'sample-training.pdf'
        try:
            install([(demo.name, demo.read_bytes())], demo=True)
        except DocumentError as exc:
            st.error(str(exc))
    st.divider()
    provider = st.selectbox('Answer mode', ['Evidence only (no key)', 'Ollama (local)', 'Groq (optional cloud)'])
    api_key = ''
    cloud_allowed = False
    if provider.startswith('Groq'):
        st.caption('Only use a free Groq account. Retrieved excerpts and questions leave this device. Never upload private documents without permission.')
        api_key = st.text_input('Groq API key (or set GROQ_API_KEY)', type='password')
        cloud_allowed = st.checkbox('Allow sending retrieved text to Groq')
    elif provider.startswith('Ollama'):
        st.caption('Requires Ollama on this computer with qwen2.5:3b downloaded.')
    st.divider()
    if st.button('Clear Chat', use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    if st.button('Remove Documents', use_container_width=True):
        st.session_state.update(index=None, stats=None, messages=[], is_demo=False)
        st.rerun()
    st.caption('Session only. Nothing is saved to disk by the app. Removing documents also clears chat.')

st.markdown('''<div class="hero"><small>PDF-FIRST • PAGE-CITED • FREE TO RUN LOCALLY</small>
<h1>Tamil Nadu Agriculture Schemes Assistant</h1>
<p>Find the evidence behind a scheme. Ask your PDFs, then check the source page.</p></div>''', unsafe_allow_html=True)

if st.session_state.stats:
    stats = st.session_state.stats
    a, b, c = st.columns(3)
    a.metric('Indexed documents', len(stats['files']))
    b.metric('PDF pages', stats['pages'])
    c.metric('Searchable passages', stats['chunks'])
    st.caption('Active files: ' + ', '.join(stats['files']))
    if stats['skipped']:
        st.warning(f"{stats['skipped']} pages had no extractable text and were skipped. They may need OCR.")
    if st.session_state.is_demo:
        st.warning('DEMO DATA: invented training schemes, not government policy. Upload official PDFs for real research.')
else:
    st.subheader('Start with the source, not a guess.')
    st.write('Upload one or more scheme booklets in the sidebar and select Index Documents. Or try the clearly labelled sample PDF, no account or API key needed.')
    st.info('Ask about eligibility, benefits, required documents, or where to apply. Exact scheme names work best with local search.')


def show_message(message):
    with st.chat_message(message['role']):
        st.markdown(message['content'])
        if message.get('note'):
            st.caption(message['note'])
        for source in message.get('sources', []):
            with st.expander(f"[{source['id']}] {source['file']} (PDF p.{source['page']})"):
                st.write(source['text'])
                st.caption('Physical PDF page, counted from 1. Search relevance is not a confidence score.')

for message in st.session_state.messages:
    show_message(message)

question = st.chat_input('Ask about the schemes in your PDFs...', disabled=st.session_state.index is None, max_chars=1200)
if question:
    question = question.strip()
    if question:
        user = dict(role='user', content=question)
        st.session_state.messages.append(user)
        show_message(user)
        with st.spinner('Finding evidence...'):
            hits = st.session_state.index.search(question)
            effective = provider if not provider.startswith('Groq') or cloud_allowed else 'Evidence only (no key)'
            answer, note = generate(question, hits, effective, api_key)
            if provider.startswith('Groq') and not cloud_allowed:
                note = 'Cloud sharing not enabled. Showing local evidence.'
            message = dict(role='assistant', content=answer, note=note,
                           sources=[dict(id=i, file=h.chunk.file, page=h.chunk.page, text=h.chunk.text)
                                    for i, h in enumerate(hits, 1)])
        st.session_state.messages.append(message)
        show_message(message)

if st.session_state.messages:
    # Explicit fields only: no API key, local paths or index internals in export.
    st.download_button('Download conversation (JSON)', json.dumps(st.session_state.messages, ensure_ascii=False, indent=2),
                       file_name='uzhavan-chat.json', mime='application/json')
st.caption('Research aid, not an official service. A PDF can be outdated. Confirm details with the issuing department. Each question is searched independently; repeat scheme names in follow-ups.')
