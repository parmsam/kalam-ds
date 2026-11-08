"""Hand-checked fixes on top of extract.py output.
ORDER: detection index (A=0,B=1,...) of each stroke, in the worksheet's numbered order.
ROUTES: page-pixel waypoints for strokes whose curls the automatic tracer can't follow."""
import sys, json, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
PAGES = sys.argv[1]  # folder of x3-NN.png renders
import extract as E
ORDER = {
 'અ':'ACDB','આ':'ADEBC','ઇ':'AB','ઈ':'AB','ઉ':'AB','ઊ':'AB','એ':'CEDBA','ઐ':'DEFCBA','ઓ':'CEFDBA','ઔ':'EFGDCBA',
 'અં':'BDECA','અઃ':'ADEBCF','ક':'AB','ખ':'ACB','ગ':'BA','ઘ':'BCA','ચ':'ACB','છ':'AB','જ':'A','ઝ':'ACB',
 'ટ':'A','ઠ':'A','ડ':'A','ઢ':'A','ણ':'ACB','ત':'BA','થ':'BA','દ':'AB','ધ':'ACB','ન':'BA','પ':'AB','ફ':'ACB',
 'બ':'BCA','ભ':'BA','મ':'BA','ય':'BA','ર':'AB','લ':'BCA','વ':'BA','શ':'BCA','ષ':'ACB','સ':'BDCA','હ':'AB',
 'ળ':'A','ક્ષ':'BCA','જ્ઞ':'BCA'}
# (letter, detection index) -> waypoints
ROUTES = {
 ('ભ',1): [(700,860),(440,600),(580,220),(760,280),(770,500),(720,610),(680,570),(710,530),(1000,530)],
 ('મ',1): [(490,176),(620,240),(620,500),(600,620),(540,630),(525,580),(580,560),(940,564)],
 ('ક્ષ',1): [(950,446),(800,456),(610,390),(500,260),(640,144),(760,230),(720,340),(480,520),(450,640),(600,780),(776,680)],
}
raw = json.load(open('raw.json'))
out = {}
for i, g in enumerate(E.LETTERS, 1):
    r = raw[g]; o = ORDER[g]
    assert len(o) == len(r['strokes']), (g, len(r['strokes']))
    if any(k[0] == g for k in ROUTES):
        E.process(os.path.join(PAGES, f'x3-{i:02d}.png'))
        for (gg, k), wp in ROUTES.items():
            if gg == g: r['strokes'][k]['pts'] = E.route(E.LAST_SK, wp)
    out[g] = {'box': r['box'], 'white_bb': r['white_bb'],
              'strokes': [r['strokes'][ord(c)-65] for c in o]}
json.dump(out, open('ordered.json', 'w'))
print('letters', len(out), 'strokes', sum(len(v['strokes']) for v in out.values()))
