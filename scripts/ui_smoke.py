"""Browser smoke check against a temporary loopback Streamlit server."""
from pathlib import Path
import subprocess
import time
import urllib.request
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
server = subprocess.Popen([str(Path(__import__('sys').executable)), '-m', 'streamlit', 'run',
                           str(ROOT / 'app.py'), '--server.address', '127.0.0.1',
                           '--server.port', '8501', '--server.headless', 'true'],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
try:
    for _ in range(100):
        try:
            urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=1)
            break
        except Exception:
            time.sleep(.2)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = browser.new_page(viewport={'width': 1440, 'height': 1500}, device_scale_factor=1)
        page.goto('http://127.0.0.1:8501')
        page.get_by_text('Start with the source, not a guess.').wait_for()
        page.locator('input[type=file]').set_input_files(str(ROOT / 'docs' / 'sample-training.pdf'))
        page.get_by_role('button', name='Index Documents', exact=True).click()
        page.get_by_text('Active files: sample-training.pdf', exact=True).wait_for()
        assert page.get_by_text('DEMO DATA:', exact=False).count() == 0
        page.get_by_role('button', name='Try a sample PDF', exact=True).click()
        page.get_by_text('DEMO DATA:', exact=False).wait_for()
        prompt = page.get_by_placeholder('Ask about the policies in your PDFs...')
        prompt.fill('What documents are required for prior authorization?')
        prompt.press('Enter')
        page.get_by_text('These passages match your question.', exact=False).wait_for()
        page.get_by_text('[1] sample-training.pdf (PDF p.1)', exact=True).click()
        page.get_by_text('Physical PDF page, counted from 1.', exact=False).first.wait_for()
        page.wait_for_function("document.querySelector('[data-testid=stApp]')?.getAttribute('data-test-script-state') === 'notRunning'")
        page.screenshot(path=str(ROOT / 'docs' / 'demo.png'), full_page=True)
        page.get_by_role('button', name='Clear Chat', exact=True).click()
        page.get_by_text('Active files: sample-training.pdf', exact=True).wait_for()
        page.locator('[data-testid=stChatMessage]').first.wait_for(state='detached')
        assert page.locator('[data-testid=stChatMessage]').count() == 0
        page.get_by_role('button', name='Remove Documents', exact=True).click()
        page.get_by_text('Start with the source, not a guess.').wait_for()
        assert page.get_by_placeholder('Ask about the policies in your PDFs...').is_disabled()
        page.close()
        page = browser.new_page(viewport={'width': 390, 'height': 844})
        page.goto('http://127.0.0.1:8501')
        page.get_by_text('Start with the source, not a guess.').wait_for()
        page.get_by_role('heading', name='Healthcare Claims & Payer Policy Assistant').wait_for()
        page.wait_for_function("document.querySelector('[data-testid=stApp]')?.getAttribute('data-test-script-state') === 'notRunning'")
        page.screenshot(path=str(ROOT / 'docs' / 'mobile.png'), full_page=True)
        browser.close()
        print('UI smoke passed: upload/index/sample/question/source/clear/remove/mobile.')
finally:
    server.terminate()
    try:
        server.wait(timeout=10)
    except subprocess.TimeoutExpired:
        server.kill(); server.wait()
