"""Extract stroke order from iknowmyabc Gujarati tracing worksheet pages.

Each page has a grey reference box: the letter drawn in white, a black arrow along
the centre line of every stroke, and a red numbered circle at each stroke's start.
Output: raw.json with, per letter, ordered strokes as polylines in page pixels.
usage: python3 extract.py PAGE_DIR OUT_DIR   (PAGE_DIR holds x3-01.png ... x3-46.png)
"""
import json, sys, math, os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage.morphology import skeletonize
import pytesseract
import warnings; warnings.filterwarnings('ignore')
from scipy.spatial import cKDTree

LETTERS = ['અ','આ','ઇ','ઈ','ઉ','ઊ','એ','ઐ','ઓ','ઔ','અં','અઃ',
  'ક','ખ','ગ','ઘ','ચ','છ','જ','ઝ','ટ','ઠ','ડ','ઢ','ણ','ત','થ','દ','ધ','ન',
  'પ','ફ','બ','ભ','મ','ય','ર','લ','વ','શ','ષ','સ','હ','ળ','ક્ષ','જ્ઞ']
N8 = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

def masks(a):
    r, g, b = a[...,0], a[...,1], a[...,2]
    grey = (abs(r-g) < 8) & (abs(g-b) < 8) & (r > 170) & (r < 210)
    white = (r > 232) & (g > 232) & (b > 232)
    black = (r < 110) & (g < 110) & (b < 110)
    red = (r > 160) & (g < 120) & (b < 120) & (r - g > 70)
    return grey, white, black, red

def box_of(grey):
    lab, n = ndi.label(grey)
    sizes = ndi.sum(grey, lab, range(1, n+1))
    k = int(np.argmax(sizes)) + 1
    ys, xs = np.where(lab == k)
    return xs.min(), ys.min(), xs.max(), ys.max()

def circles(red, white):
    grown = ndi.binary_dilation(red, iterations=8)
    lab, n = ndi.label(grown)
    out = []
    for k in range(1, n+1):
        ys, xs = np.where((lab == k) & red)
        if len(xs) < 25: continue
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        out.append({'c': ((x0+x1)/2, (y0+y1)/2), 'r': max(x1-x0, y1-y0)/2, 'bb': (x0, y0, x1, y1)})
    return out

def read_digit(a, c):
    x0, y0, x1, y1 = c['bb']
    pad = 2
    crop = a[max(0,y0-pad):y1+pad+1, max(0,x0-pad):x1+pad+1]
    r, g, b = crop[...,0].astype(int), crop[...,1].astype(int), crop[...,2].astype(int)
    redm = (r - g > 70)
    # keep only the inner digit: drop red pixels near the ring edge
    h, w = redm.shape
    yy, xx = np.mgrid[0:h, 0:w]
    cy, cx = (h-1)/2, (w-1)/2
    rr = np.hypot(yy-cy, xx-cx)
    inner = redm & (rr < min(h, w)/2 - 8)
    img = np.where(inner, 0, 255).astype(np.uint8)
    im = Image.fromarray(img).resize((w*3, h*3), Image.LANCZOS)
    big = Image.new('L', (w*3+80, h*3+80), 255); big.paste(im, (40, 40))
    t = pytesseract.image_to_string(big, config='--psm 10 -c tessedit_char_whitelist=123456789').strip()
    return int(t[0]) if t[:1].isdigit() else None


def graph(sk):
    """Skeleton -> nodes (endpoints / clustered junctions) and edges (pixel chains)."""
    P = set(zip(*np.where(sk)))
    nb = lambda p: [(p[0]+dy, p[1]+dx) for dy, dx in N8 if (p[0]+dy, p[1]+dx) in P]
    deg = {p: len(nb(p)) for p in P}
    special = [p for p in P if deg[p] != 2]
    # cluster junction/end pixels that sit close together into one node
    node_of = {}; nodes = []
    for p in special:
        if p in node_of: continue
        k = len(nodes); stack = [p]; group = []
        node_of[p] = k
        while stack:
            q = stack.pop(); group.append(q)
            for r in special:
                if r not in node_of and abs(r[0]-q[0]) <= 22 and abs(r[1]-q[1]) <= 22:
                    node_of[r] = k; stack.append(r)
        nodes.append(group)
    edges = []; used = set()
    for p in special:
        for q in nb(p):
            if q in node_of:
                if node_of[q] != node_of[p] and (min(p,q), max(p,q)) not in used:
                    used.add((min(p,q), max(p,q))); edges.append([node_of[p], node_of[q], [p, q]])
                continue
            if (p, q) in used: continue
            chain = [p, q]; prev, cur = p, q
            while cur not in node_of:
                n = [r for r in nb(cur) if r != prev]
                if not n: break
                prev, cur = cur, n[0]; chain.append(cur)
            used.add((chain[-1], chain[-2])); used.add((p, q))
            if cur in node_of and not (node_of[cur] == node_of[p] and len(chain) < 20):
                edges.append([node_of[p], node_of[cur], chain])
    return nodes, edges

def prune_edges(nodes, edges, L):
    for _ in range(4):
        deg = {}
        for a, b, c in edges:
            deg[a] = deg.get(a, 0) + 1; deg[b] = deg.get(b, 0) + 1
        keep = []
        removed = False
        for e in edges:
            a, b, c = e
            leaf = (deg[a] == 1) != (deg[b] == 1)
            if leaf and len(c) < L and max(deg[a], deg[b]) >= 3:
                removed = True; continue
            keep.append(e)
        edges = keep
        if not removed: break
    return edges

def unit(v):
    n = math.hypot(*v) + 1e-9; return (v[0]/n, v[1]/n)

def trace(start_node, edges, nodes):
    inc = {}
    for i, (a, b, c) in enumerate(edges):
        inc.setdefault(a, []).append(i); inc.setdefault(b, []).append(i)
    usedE = set(); node = start_node; path = []
    while True:
        cand = [i for i in inc.get(node, []) if i not in usedE]
        if not cand: break
        def oriented(i):
            a, b, c = edges[i]
            return c if a == node else c[::-1]
        if path:
            dirin = unit((path[-1][0]-path[-45 if len(path) > 45 else 0][0], path[-1][1]-path[-45 if len(path) > 45 else 0][1]))
            def turn(i):
                c = oriented(i); k = min(len(c)-1, 45)
                d = unit((c[k][0]-path[-1][0], c[k][1]-path[-1][1]))
                return -(dirin[0]*d[0] + dirin[1]*d[1])
            cand.sort(key=turn)
            if turn(cand[0]) > -0.2: break   # nothing roughly straight ahead
        i = cand[0]; usedE.add(i); c = oriented(i)
        path.extend(c if not path else c[1:])
        a, b, _ = edges[i]; node = b if a == node else a
    return path


def pen_trace(P, tree, start_xy, center_xy, S=3, max_steps=900, d0=None):
    """Follow skeleton pixels like a pen: always continue roughly straight ahead."""
    step = 2*S
    cur = np.array(start_xy, float)
    d = cur - np.array(center_xy, float) if d0 is None else np.array(d0, float); d /= (np.linalg.norm(d) + 1e-9)
    path = [cur.copy()]; visited = np.zeros(len(P), bool); on_old = 0
    for _ in range(max_steps):
        idx = tree.query_ball_point(cur + d*step, r=step*1.3)
        best = None
        for i in idx:
            v = P[i] - cur; n = np.linalg.norm(v)
            if n < step*0.4: continue
            cosang = float(v @ d) / n
            if cosang < 0.45: continue          # more than ~63 degrees off course
            if visited[i] and cosang < 0.9: continue
            sc = (1 - cosang) + (0.5 if visited[i] else 0)
            if best is None or sc < best[0]: best = (sc, i)
        if best is None:
            # widen the search once before giving up (tight curves, arrow tips)
            idx = tree.query_ball_point(cur, r=step*3)
            cands = [(1 - float((P[i]-cur) @ d)/np.linalg.norm(P[i]-cur), i) for i in idx
                     if np.linalg.norm(P[i]-cur) > step*0.6 and not visited[i] and float((P[i]-cur) @ d)/np.linalg.norm(P[i]-cur) > -0.35]
            if not cands: break
            best = min(cands)
        i = best[1]
        nd = P[i] - cur; nd /= np.linalg.norm(nd)
        d = 0.55*d + 0.45*nd; d /= np.linalg.norm(d)
        on_old = on_old + 1 if visited[i] else 0
        if on_old > 6: break
        for j in tree.query_ball_point(cur, r=step*1.6): visited[j] = True
        cur = P[i].copy(); path.append(cur.copy())
    return [[float(x), float(y)] for x, y in path]

def process(path, S=3):
    a = np.array(Image.open(path).convert('RGB')).astype(int)
    grey, white, black, red = masks(a)
    bx0, by0, bx1, by1 = box_of(grey)
    roi = np.zeros(grey.shape, bool); roi[by0:by1+1, bx0:bx1+1] = True
    near_white = ndi.binary_dilation(white & roi, iterations=4*S)
    cs = [c for c in circles(red & roi, white) if c['r'] > 4*S]
    arrow = black & near_white & roi
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    cmask = np.zeros_like(arrow)
    for c in cs:
        cmask |= np.hypot(xx - c['c'][0], yy - c['c'][1]) < c['r'] + 4*S
    arrow = ndi.binary_closing(arrow, structure=np.ones((3,3)), iterations=3)
    from skimage.morphology import disk
    arrow = ndi.binary_opening(arrow, structure=disk(4))  # drop thin outlines, keep ~20px arrows
    from skimage.morphology import remove_small_holes
    arrow = remove_small_holes(arrow, area_threshold=40*S*S)
    arrow &= ~cmask
    lab, n = ndi.label(arrow, structure=np.ones((3,3)))
    sizes = ndi.sum(arrow, lab, range(1, n+1))
    for k, s in enumerate(sizes, 1):
        if s < 60*S: arrow[lab == k] = False
    sk = skeletonize(arrow)
    global LAST_SK; LAST_SK = sk  # used by route() overrides in fix.py
    ys, xs = np.where(sk)
    P = np.stack([xs, ys], 1).astype(float)
    tree = cKDTree(P)
    for c in cs: c['d'] = read_digit(a, c)
    strokes = []
    for c in cs:
        cx, cy = c['c']
        dist, i = tree.query([cx, cy])
        if dist > c['r'] + 30*S:
            strokes.append({'d': c['d'], 'pts': [[cx, cy]], 'dot': True, 'start': [cx, cy]}); continue
        best = None
        for k in range(16):
            ang = k*math.pi/8
            pth = pen_trace(P, tree, P[i], (cx, cy), S, d0=(math.cos(ang), math.sin(ang)))
            if len(pth) < 3: continue
            # must head away from the circle
            if math.hypot(pth[min(6,len(pth)-1)][0]-cx, pth[min(6,len(pth)-1)][1]-cy) <= math.hypot(pth[0][0]-cx, pth[0][1]-cy): continue
            L = sum(math.hypot(pth[j][0]-pth[j-1][0], pth[j][1]-pth[j-1][1]) for j in range(1, len(pth)))
            if best is None or L > best[0]: best = (L, pth)
        pth = best[1] if best else [[float(P[i][0]), float(P[i][1])]]
        strokes.append({'d': c['d'], 'pts': pth, 'start': [cx, cy]})
    wy, wx = np.where(white & roi & ~cmask)
    return {'box': [int(bx0), int(by0), int(bx1), int(by1)],
            'white_bb': [int(wx.min()), int(wy.min()), int(wx.max()), int(wy.max())],
            'strokes': strokes}

def route(sk, waypoints):
    """Shortest path along skeleton pixels through each waypoint in turn (page px)."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import dijkstra
    ys, xs = np.where(sk); idx = -np.ones(sk.shape, int); idx[ys, xs] = np.arange(len(ys))
    rows, cols, w = [], [], []
    for dy, dx in N8:
        y2, x2 = ys+dy, xs+dx
        ok = (y2 >= 0) & (y2 < sk.shape[0]) & (x2 >= 0) & (x2 < sk.shape[1])
        j = np.full(len(ys), -1); j[ok] = idx[y2[ok], x2[ok]]
        m = j >= 0; rows += list(np.where(m)[0]); cols += list(j[m]); w += [math.hypot(dy, dx)]*int(m.sum())
    G = coo_matrix((w, (rows, cols)), shape=(len(ys), len(ys))).tocsr()
    tree = cKDTree(np.stack([xs, ys], 1))
    snap = [int(tree.query(p)[1]) for p in waypoints]
    out = []
    for a, b in zip(snap, snap[1:]):
        _, pred = dijkstra(G, indices=a, return_predecessors=True)
        seg = [b]
        while seg[-1] != a and pred[seg[-1]] >= 0: seg.append(pred[seg[-1]])
        if seg[-1] != a:   # disconnected skeleton (tight curl): bridge with a straight line
            n = max(2, int(math.hypot(xs[b]-xs[a], ys[b]-ys[a]) // 3))
            seg = [('p', xs[a] + (xs[b]-xs[a])*k/n, ys[a] + (ys[b]-ys[a])*k/n) for k in range(n+1)]
        else:
            seg = [('p', float(xs[i]), float(ys[i])) for i in seg[::-1]]
        out += seg if not out else seg[1:]
    pts = [[float(x), float(y)] for _, x, y in out]
    return pts[::2] + [pts[-1]]

if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]
    res = {}
    for i, g in enumerate(LETTERS, 1):
        r = process(os.path.join(src, f'x3-{i:02d}.png'))
        res[g] = r
        ds = [s['d'] for s in r['strokes']]
        flag = '' if sorted(d for d in ds if d) == list(range(1, len(ds)+1)) else '  <-- CHECK DIGITS'
        print(i, g, 'digits', ds, 'lens', [len(s['pts']) for s in r['strokes']], flag, flush=True)
    json.dump(res, open(os.path.join(out, 'raw.json'), 'w'))
