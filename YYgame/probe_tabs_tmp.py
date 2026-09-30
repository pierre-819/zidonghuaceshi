# encoding: utf-8
"""临时探测：逐个点顶部导航 tab，记录 url/title/新标签页/JS报错/失败请求，跑完即删"""
import json
import os

from playwright.sync_api import sync_playwright

TABS = ['首页', '我要买', '我要卖', '中介担保', '账号回收', '账号估值', '个人中心']
OUT = os.path.join('captures', 'explore')
os.makedirs(OUT, exist_ok=True)
result = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1440, 'height': 900}, locale='zh-CN')
    page = context.new_page()

    for tab in TABS:
        errors, failed = [], []
        page.on('pageerror', lambda e: errors.append(str(e)[:120]))
        page.on('requestfailed', lambda r: failed.append(r.url[:100]))
        page.goto('https://malltest.yy.com/', wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(3500)
        before_pages = len(context.pages)
        try:
            page.get_by_role('link', name=tab, exact=True).first.click(timeout=10000)
        except Exception as e:
            result.append({'tab': tab, 'click_error': f'{type(e).__name__}: {str(e)[:120]}'})
            continue
        page.wait_for_timeout(4000)
        cur = context.pages[-1]
        cur.wait_for_load_state('domcontentloaded')
        cur.wait_for_timeout(1500)
        result.append({
            'tab': tab,
            'new_tab_opened': len(context.pages) > before_pages,
            'url': cur.url,
            'title': cur.title(),
            'has_login_dialog': cur.locator('article[class*="dialog-"]').count() > 0,
            'active_tab_text': cur.locator('a[class*="tabActive"]').first.inner_text()
            if cur.locator('a[class*="tabActive"]').count() else '',
            'h1_or_section': cur.locator('[class*="section-"], [class*="main-"]').count(),
            'body_text_head': cur.locator('body').inner_text()[:120].replace('\n', ' | '),
            'pageerror': errors[:3],
            'requestfailed': failed[:3],
        })
        for pg in context.pages[1:]:
            pg.close()

    with open(os.path.join(OUT, 'tabs.json'), 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print('DONE', len(result))
    context.close()
    browser.close()
