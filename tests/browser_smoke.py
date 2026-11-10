"""Optional browser regression test and actual-app recording. Requires Playwright."""
import json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path=os.environ.get("CHROMIUM_PATH"))
    context=browser.new_context(viewport={'width':1440,'height':1000},record_video_dir=str(ROOT/'verification'),record_video_size={'width':1440,'height':1000})
    page=context.new_page();errors=[];posts=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.on('request',lambda req:posts.append(req.url) if req.method=='POST' else None)
    page.goto('http://127.0.0.1:8765');page.get_by_text('Personality is a pattern.',exact=False).wait_for()
    page.screenshot(path=str(ROOT/'verification/overview.png'),full_page=True)
    page.locator('[data-view="profile"]').click();page.locator('#next').click()
    assert 'Please answer' in page.locator('#survey-error').inner_text()
    survey=json.loads((ROOT/'web/survey.json').read_text())
    for s in survey:
        for i,q in enumerate(s['items']):
            page.locator(f'#q{i}').select_option('5' if q['direction']==1 else '1')
        page.locator('#next').click()
    assert page.get_by_text('50 / 50',exact=False).count()==5
    assert posts==[], 'Questionnaire answers must not be sent'
    page.screenshot(path=str(ROOT/'verification/profile.png'),full_page=True)
    page.locator('[data-view="target"]').click()
    page.locator('#r-cocaine').select_option('6');assert 'No match' in page.locator('#target-result').inner_text()
    page.locator('#r-ketamine').select_option('4');assert '2 qualifying · Match'==page.locator('#target-result').inner_text()
    page.screenshot(path=str(ROOT/'verification/target.png'),full_page=True)
    page.locator('[data-view="model"]').click();page.locator('#predict').click();page.get_by_text('Classified as',exact=False).wait_for()
    page.screenshot(path=str(ROOT/'verification/model.png'),full_page=True)
    page.locator('[data-view="profile"]').click();page.locator('#reset').click();assert page.locator('#q0').input_value()==''
    page.set_viewport_size({'width':390,'height':844});page.locator('[data-view="overview"]').click()
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    page.screenshot(path=str(ROOT/'verification/mobile.png'),full_page=True)
    assert not errors,errors
    video=page.video;context.close();video.save_as(str(ROOT/'verification/walkthrough.webm'));browser.close()
    print('Browser checks passed: all 50 answers, correct trait extremes, no questionnaire POSTs, target boundary, inference, reset, mobile overflow, no JS errors.')
