"""ClaimsDesk: a PDF-first healthcare payer policy and claims assistant."""
from pathlib import Path
import json
import streamlit as st
from dotenv import load_dotenv
from claims.retrieval import build_index, DocumentError
from claims.generation import generate

load_dotenv()
st.set_page_config(page_title='ClaimsDesk | Payer Policy Assistant', page_icon='🏥', layout='wide')
st.markdown('''<style>
.stApp {background:#f4f8fc; color:#14304d}
[data-testid="stSidebar"] {background:#163a5f}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,[data-testid="stSidebar"] label {color:#eaf3fb!important}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {color:#c9dcee!important}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] p,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small {color:#14304d!important}
[data-testid="stSidebar"] button {border-radius:8px}
[data-testid="stSidebar"] button p {color:#14304d!important}
[data-testid="stSidebar"] button[kind="primary"] p {color:#fff!important}
.block-container {padding-top:2.5rem; max-width:1250px}
@media (max-width:640px) {.block-container {padding-top:5rem} .hero {padding:22px} .hero h1 {font-size:28px}}
.hero {background:#e3eef9; border-left:5px solid #4a7fb5; border-radius:12px; padding:28px 32px; margin-bottom:24px}
.hero small {font-size:12px; letter-spacing:2px; color:#33587e}
.hero h1 {font-size:34px; padding:8px 0; color:#163a5f}
.hero p {margin:0; color:#3d5b7a; font-size:16px}
[data-testid="stChatMessage"] {border:1px solid #dbe7f2; border-radius:12px; background:#fff}
[data-testid="stMetric"] {background:#e9f1f9; padding:12px; border-radius:10px}
</style>''', unsafe_allow_html=True)

for key, value in {'messages': [], 'index': None, 'stats': None, 'is_demo': False}.items():
    if key not in st.session_state:
        st.session_state[key] = value


def install(files, demo=False):
    # Replace only after a successful build; never corrupt an existing index on error.
    index, stats = build_index(files)
    st.session_state.update(index=index, stats=stats, is_demo=demo, messages=[])

with st.sidebar:
    st.title('ClaimsDesk')
    st.caption('REVENUE CYCLE • KNOWLEDGE DESK')
    st.divider()
    st.subheader('Your documents')
    uploads = st.file_uploader('Upload policy or claims PDFs', type=['pdf'], accept_multiple_files=True,
                               help='Text PDFs, up to 20 MB each and 60 MB total. OCR is not included.')
    st.caption('Select files, then index. Uploading alone does not change the active index.')
    st.caption('Never upload documents containing patient health information (PHI).')
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
<h1>Healthcare Claims &amp; Payer Policy Assistant</h1>
<p>Find the evidence behind a claim decision. Ask your PDFs, then check the source page.</p></div>''', unsafe_allow_html=True)

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
        st.warning('DEMO DATA: invented training policies, not real payer policy. Upload official PDFs for real research.')
else:
    st.subheader('Start with the source, not a guess.')
    st.write('Upload one or more payer policy or claims manual PDFs in the sidebar and select Index Documents. Or try the clearly labelled sample PDF, no account or API key needed.')
    st.info('Ask about prior authorization, timely filing limits, denial codes, coordination of benefits, or required documents. Exact policy terms work best with local search.')


def show_message(message):
    with st.chat_message(message['role']):
        st.markdown(message['content'])
        if message.get('note'):
            st.caption(message['note'])
        for i, source in enumerate(message.get('sources', []), 1):
            with st.expander(f"[{i}] {source['file']} (PDF p.{source['page']})"):
                st.caption('Physical PDF page, counted from 1.')
                st.write(source['text'])

for message in st.session_state.messages:
    show_message(message)

question = st.chat_input('Ask about the policies in your PDFs...', disabled=st.session_state.index is None, max_chars=1200)
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
                       file_name='claimsdesk-chat.json', mime='application/json')
st.caption('Research aid, not billing, medical, or legal advice. A PDF can be outdated. Confirm details with the payer\'s current policy. Each question is searched independently; repeat policy names in follow-ups.')
