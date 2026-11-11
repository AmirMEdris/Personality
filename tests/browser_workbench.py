"""Real-browser interaction checks; starts its own local server on a free port."""
import threading
import os
from pathlib import Path
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from personality.server import Handler
ROOT=Path(__file__).resolve().parents[1]
server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=os.environ.get("CHROMIUM_PATH"))
        context=browser.new_context(viewport={'width':1440,'height':1000},record_video_dir=str(ROOT/'verification/workbench'))
        page=context.new_page();errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(f'http://127.0.0.1:{server.server_port}/workbench')
        page.locator('#results').wait_for(state='visible')
        assert page.locator('#ranking .rank').count()==5
        page.locator('[data-stage="4"]').click()
        assert 'sigmoid' in page.locator('#stage-detail').inner_text()
        selects=page.locator('#missing-inputs select');selects.nth(0).select_option('1');selects.nth(1).select_option('1')
        assert 'Label established: matches' in page.locator('#missing-result').inner_text()
        selects.nth(1).select_option('?')
        assert 'Label unknown' in page.locator('#missing-result').inner_text()
        page.locator('#threshold').fill('1');page.locator('#threshold').dispatch_event('input')
        assert page.locator('#threshold-value').inner_text()=='0.01'
        page.screenshot(path=str(ROOT/'verification/workbench/desktop.png'),full_page=True)
        page.set_viewport_size({'width':390,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.screenshot(path=str(ROOT/'verification/workbench/mobile.png'),full_page=True)
        assert not errors,errors
        context.close();browser.close()
        print('Workbench browser interactions, charts and mobile overflow passed.')
finally:server.shutdown();server.server_close()
