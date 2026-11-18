from pathlib import Path
from io import BytesIO
import pytest
from reportlab.pdfgen import canvas
from agri.retrieval import build_index, DocumentError, evidence_answer
from agri.generation import generate

SAMPLE = Path(__file__).resolve().parents[1] / 'docs' / 'sample-training.pdf'

def test_pages_and_evidence():
    idx, stats = build_index([(SAMPLE.name, SAMPLE.read_bytes())])
    assert stats['pages'] == 2
    hits = idx.search('What documents are required for the Seed Learning Grant?')
    assert hits[0].chunk.page == 1
    assert 'membership card' in evidence_answer(hits)
    hits = idx.search('drip irrigation workshop')
    assert hits[0].chunk.page == 2

def test_deduplication():
    _, stats = build_index([('a.pdf', SAMPLE.read_bytes()), ('copy.pdf', SAMPLE.read_bytes())])
    assert len(stats['files']) == 1

def test_invalid_and_missing():
    with pytest.raises(DocumentError):
        build_index([])
    with pytest.raises(DocumentError):
        build_index([('bad.pdf', b'not a PDF')])

def test_blank_scan():
    buffer = BytesIO(); c = canvas.Canvas(buffer); c.showPage(); c.save()
    with pytest.raises(DocumentError, match='OCR'):
        build_index([('scan.pdf', buffer.getvalue())])

def test_unknown_and_empty():
    idx, _ = build_index([(SAMPLE.name, SAMPLE.read_bytes())])
    assert idx.search('') == []
    assert idx.search('xylophone astrophysics quasar') == []
    assert "couldn't find" in evidence_answer([])

def test_no_key_fallback(monkeypatch):
    monkeypatch.delenv('GROQ_API_KEY', raising=False)
    idx, _ = build_index([(SAMPLE.name, SAMPLE.read_bytes())])
    answer, note = generate('seed kit', idx.search('seed kit'), 'Groq (optional cloud)')
    assert 'missing' in note and '[1]' in answer

def test_model_error_fallback(monkeypatch):
    import requests
    def fail(*args, **kwargs):
        raise requests.Timeout()
    monkeypatch.setattr(requests, 'post', fail)
    idx, _ = build_index([(SAMPLE.name, SAMPLE.read_bytes())])
    answer, note = generate('seed kit', idx.search('seed kit'), 'Ollama (local)')
    assert 'unavailable' in note and 'extracts' in answer

def test_bad_citations_fallback(monkeypatch):
    class Response:
        def raise_for_status(self): pass
        def json(self): return {'message': {'content': 'Invented [99]'}}
    monkeypatch.setattr('requests.post', lambda *a, **kw: Response())
    idx, _ = build_index([(SAMPLE.name, SAMPLE.read_bytes())])
    _, note = generate('seed kit', idx.search('seed kit'), 'Ollama (local)')
    assert 'failed citation' in note
