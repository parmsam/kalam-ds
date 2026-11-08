import asyncio, json, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
from playwright.async_api import async_playwright

def simplify(s, d=3.0):
    o = [s[0]]
    for p in s[1:]:
        if math.hypot(p[0]-o[-1][0], p[1]-o[-1][1]) >= d: o.append(p)
    if len(s) > 1 and o[-1] is not s[-1]: o.append(s[-1])
    return [[round(x, 1), round(y, 1)] for x, y in o]

async def main():
    data = json.load(open('ordered.json'))
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--allow-file-access-from-files'])
        pg = await b.new_page()
        css = os.environ.get('FONTS_CSS')  # optional: serve fonts locally when Google Fonts is unreachable
        if css: await pg.route('https://fonts.googleapis.com/**', lambda r: r.fulfill(path=css, content_type='text/css'))
        await pg.goto('file://' + os.path.join(HERE, 'fit.html')); await pg.wait_for_timeout(500)
        res = await pg.evaluate('d => fitAll(d)', data)
        await b.close()
    strokes = {g: [simplify(s) for s in v] for g, v in res['out'].items()}
    json.dump(strokes, open('fitted.json', 'w'), ensure_ascii=False)
    for g, s in res['stats'].items(): print(g, s)

asyncio.run(main())
