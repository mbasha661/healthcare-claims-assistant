"""Page-aware, in-memory PDF retrieval. No network calls at indexing time."""
from dataclasses import dataclass
from io import BytesIO
from hashlib import sha256
import re
import numpy as np
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer

MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_TOTAL_BYTES = 60 * 1024 * 1024
MAX_PAGES = 600
MAX_CHUNKS = 6000

@dataclass(frozen=True)
class Chunk:
    file: str
    page: int
    text: str

@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float

class DocumentError(ValueError):
    pass


def read_pdf(name: str, data: bytes) -> tuple[list[Chunk], int, int]:
    if len(data) > MAX_FILE_BYTES:
        raise DocumentError(f'{name}: exceeds the 20 MB file limit.')
    if not data.lstrip().startswith(b'%PDF-'):
        raise DocumentError(f'{name}: not a PDF file.')
    try:
        reader = PdfReader(BytesIO(data))
        if reader.is_encrypted:
            raise DocumentError(f'{name}: password-protected PDFs are not supported.')
        if len(reader.pages) > MAX_PAGES:
            raise DocumentError(f'{name}: exceeds {MAX_PAGES} pages.')
        chunks, blank = [], 0
        for number, page in enumerate(reader.pages, 1):
            text = re.sub(r'\s+', ' ', page.extract_text() or '').strip()
            if not text:
                blank += 1
                continue
            # Overlap stays on the same physical PDF page, preserving citations.
            words = text.split()
            for start in range(0, len(words), 150):
                part = ' '.join(words[start:start + 200])
                chunks.append(Chunk(name, number, part))
                if len(chunks) > MAX_CHUNKS:
                    raise DocumentError('Too much text. Index fewer or smaller PDFs.')
        if not chunks:
            raise DocumentError(f'{name}: no extractable text. Run OCR on scanned pages first.')
        return chunks, len(reader.pages), blank
    except DocumentError:
        raise
    except Exception as exc:
        raise DocumentError(f'{name}: could not read this PDF. Check it opens correctly.') from exc

class Index:
    """Sparse local word + character embeddings, usable without an API key."""
    def __init__(self, chunks: list[Chunk]):
        if not chunks:
            raise DocumentError('No text was found.')
        self.chunks = chunks
        texts = [c.text for c in chunks]
        self.words = TfidfVectorizer(token_pattern=r'(?u)\b\w+\b', sublinear_tf=True)
        self.chars = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), max_features=60000)
        try:
            self.wmatrix = self.words.fit_transform(texts)
            self.cmatrix = self.chars.fit_transform(texts)
        except ValueError as exc:
            raise DocumentError('These PDFs have no searchable text.') from exc

    def search(self, question: str, k: int = 4) -> list[Hit]:
        if not question.strip():
            return []
        wq = self.words.transform([question])
        cq = self.chars.transform([question])
        scores = (0.8 * (self.wmatrix @ wq.T).toarray().ravel()
                  + 0.2 * (self.cmatrix @ cq.T).toarray().ravel())
        hits, pages = [], set()
        for i in np.argsort(-scores):
            if scores[i] < 0.065:
                break
            c = self.chunks[i]
            key = (c.file, c.page)
            if key not in pages:
                hits.append(Hit(c, float(scores[i])))
                pages.add(key)
            if len(hits) >= k:
                break
        return hits


def build_index(files: list[tuple[str, bytes]]) -> tuple[Index, dict]:
    if not files:
        raise DocumentError('Choose at least one PDF.')
    if sum(len(data) for _, data in files) > MAX_TOTAL_BYTES:
        raise DocumentError('Combined upload limit is 60 MB.')
    chunks, seen, pages, skipped, names = [], set(), 0, 0, []
    for name, data in files:
        digest = sha256(data).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        if name in names:
            raise DocumentError('Two different files have the same name. Rename one before indexing.')
        part, n, blank = read_pdf(name, data)
        chunks.extend(part)
        pages += n
        skipped += blank
        names.append(name)
        if len(chunks) > MAX_CHUNKS or pages > MAX_PAGES:
            raise DocumentError('Combined page/text limit exceeded. Index fewer PDFs.')
    return Index(chunks), dict(files=names, pages=pages, chunks=len(chunks), skipped=skipped)


def evidence_answer(hits: list[Hit]) -> str:
    if not hits:
        return "I couldn't find enough matching evidence in the indexed PDFs. Try the exact scheme name or upload a relevant document."
    lines = ['These passages match your question. They are extracts, not a generated explanation.']
    for i, hit in enumerate(hits, 1):
        lines.append(f'\n[{i}] {hit.chunk.text}')
    return '\n\n'.join(lines)
