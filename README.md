# Uzhavan: Tamil Nadu Agriculture Schemes Assistant

An original PDF question-answering app by Mahaboob Basha. Upload agriculture scheme PDFs, index their text locally, ask questions, and inspect the matching excerpts with **filename and physical PDF page** citations.

![Demo using fictional training data](docs/demo.png)

> The screenshot and bundled sample use invented training schemes, not real government policy. Add official, current scheme PDFs for actual research. This is not an official government service.

## Quick start (no key, no account)

Requires Python 3.10+ (tested on Python 3.10).

```bash
git clone https://github.com/mbasha661/uzhavan-scheme-assistant.git
cd uzhavan-scheme-assistant
python -m venv .venv
```

Activate the environment:

```bash
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Then:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 127.0.0.1
```

Open the local URL shown in your terminal, usually http://localhost:8501.

1. Select **Try a sample PDF** for a two-page fictional demo, or upload your own text PDFs.
2. For uploaded files, select **Index Documents**. A successful index replaces the previous documents and chat. A failed index leaves them unchanged.
3. Ask: `What documents are required for the Seed Learning Grant?`
4. Expand a source to inspect the evidence. The answer should point to PDF page 1. Ask about the drip irrigation workshop to exercise page 2.
5. Use **Clear Chat** to keep documents but remove messages. **Remove Documents** clears both. Download a JSON conversation if needed.

## Answer modes and costs

| Mode | Setup | Data handling | Output |
|---|---|---|---|
| Evidence only (default) | None | Local, no API requests | Matching extracts, not an LLM-generated answer |
| Ollama (local) | Install Ollama and download a model | Question and excerpts sent only to `127.0.0.1:11434` | Generated explanation with citation checks |
| Groq (optional cloud) | Your own free-tier Groq key | Explicit checkbox required before sending question + retrieved excerpts to Groq | Generated explanation, subject to provider limits |

The default is deliberately usable offline after installing dependencies. It uses **local sparse TF-IDF embeddings**, combining word and character features, not a pretrained neural embedding model. It works best with the same language and exact scheme terms used in the PDF. It is not cross-language semantic search.

No paid API is required. This app cannot check your Groq account's billing plan. Use only a free account, do not enable paid billing, and expect quotas/model availability to change. Failed requests fall back to local evidence. Model calls are never made in the default mode.

### Local generated answers with Ollama

Install Ollama separately from its official site. On the same computer as Streamlit:

```bash
ollama pull qwen2.5:3b
ollama serve  # only if the Ollama service is not already running
```

Select **Ollama (local)**. Downloading the model needs internet and several GB of disk space. Runtime speed and memory depend on your computer. Set `OLLAMA_MODEL` to use a different installed model. Ollama generation was implemented and failure-tested, but not run against a downloaded model in the build environment.

### Optional Groq free-tier generation

Copy `.env.example` to `.env` and set `GROQ_API_KEY`, or enter the key in the sidebar. Never commit this file or put a key in a PDF. Default model: `llama-3.1-8b-instant`; override with `GROQ_MODEL` if your account needs another model.

Select **Groq (optional cloud)** and explicitly allow sending retrieved text. Without the checkbox, the app stays local even if a key is present. No key is bundled. Groq live generation is not part of the verified offline demo.

## How it works

```text
PDF uploads -> pypdf text extraction per page -> overlapping text chunks
             -> local word + character TF-IDF vectors -> cosine-style ranking
Question     -> same vectorizers -> top 4 distinct source pages
             -> extracts OR optional LLM -> answer + inspectable page evidence
```

- Chunks never cross a PDF page, so a citation cannot drift into another page.
- Pages count from **1 in the PDF viewer**, not the printed page number on the paper.
- Content hashes avoid indexing identical uploads twice.
- All files are rebuilt atomically into a session-only index; there is no unsafe pickle loading or shared global vector database.
- An empty/weak retrieval produces a not-found response rather than an invented scheme.
- Model instructions tell the generator to treat excerpts as evidence, not commands. Citation syntax is checked; missing or out-of-range citations trigger an extractive fallback. This is **not** a factuality or prompt-injection guarantee.

## Privacy, safety and limits

- PDFs, vectors and chat live in the current Streamlit session's memory. The app does not write uploads to disk. The browser/session can remain active until it disconnects and the server clears it. Use Remove Documents to clear active app state.
- Run bound to loopback as shown above. There is no authentication or production hosting hardening. Do not expose it on a network without adding access control and reviewing upload protections.
- 20 MB per file, 60 MB total, 600 total pages and 6,000 chunks. These checks reduce accidental overload, but this is not a hardened hostile-file sandbox.
- Scanned images require OCR outside this app. Empty pages are counted and reported; partially scanned PDFs may give incomplete results.
- Text-based Tamil is indexed if the PDF has a correct Unicode text layer. Broken font encodings need OCR. Cross-language retrieval is not provided; use the PDF's language. Optional models' Tamil quality varies.
- Search relevance is not confidence. TF-IDF can miss paraphrases and retrieve irrelevant passages. Read the original PDF before making eligibility or financial decisions.
- Each question is independent. For follow-ups, repeat the scheme name; previous chat is not supplied as retrieval context.
- A source citation proves where a passage came from, not that it is current or that a generated claim is true. Verify dates, eligibility, amounts, and application routes with the issuing department.
- The bundled sample is synthetic and contains no real scheme advice. Official booklets are not bundled or scraped automatically.

## Project map

- `app.py`: green Streamlit UI, upload/index/chat/export controls
- `agri/retrieval.py`: PDF validation, page chunks, local indexing, ranking
- `agri/generation.py`: opt-in Ollama/Groq, citation checks and fallback
- `docs/sample-training.pdf`: original fictional two-page test fixture
- `scripts/make_sample.py`: regenerates the sample
- `tests/`: deterministic retrieval and failure-path tests
- `docs/demo.png`: actual running-app screenshot using sample data

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests cover page accuracy, duplicate uploads, corrupt/empty PDFs, irrelevant questions, missing keys, model failure and invalid citation fallback. The UI was also exercised in Chromium: upload a real PDF fixture, index, ask a question, expand a source, clear chat, and remove documents. No real government-PDF accuracy evaluation or live external model evaluation has been performed.

## Reference and originality

Behavioural reference supplied for the assignment: https://github.com/wownalini/Farmer_Scheme_Rag_App

This is a new implementation, not a fork or copy of that repository's code. The shared requirements are multi-PDF upload, indexing, chat, green styling and source-page citations. The reference uses a separate API and paid-model integrations; this app runs in one process and defaults to local retrieval without a key. The existing `tn-schemes-kg-rag` project was reviewed but not reused: it is a different graph-based workflow.

The reference repository had no README or buildathon rules at inspection. Confirm the event's rules, allowed assistance, data requirements and deadline before submitting. Nothing has been submitted or deployed by this project.
