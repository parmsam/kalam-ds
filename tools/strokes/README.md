# Stroke extraction tools

These scripts produce [`strokes/gujarati.json`](../../strokes/gujarati.json), the stroke-order data built into Kalam DS. They read the iknowmyabc.com Gujarati tracing worksheets. Each worksheet page shows one letter in white, with a black arrow along every stroke and a numbered red circle where each stroke starts.

The worksheet PDF is not included in this repo. Download it from [iknowmyabc.com](https://www.iknowmyabc.com) ("Gujarati Alphabet Tracing Worksheets", 46 pages).

## Pipeline

```sh
pip install numpy scipy scikit-image pillow pytesseract playwright
python3 -m playwright install chromium

# 1. Render the top of each page at 3x (216 dpi): the reference box is in the top-left corner
pdftoppm -r 216 -png -x 0 -y 0 -W 2300 -H 1900 Gujarati-Alphabet-Tracing-Worksheets.pdf pages/x3

# 2. Find the numbered circles and trace every arrow from its circle  → raw.json
python3 extract.py pages .

# 3. Put the strokes in the worksheet's numbered order and apply hand fixes  → ordered.json
python3 fix.py pages

# 4. Fit the strokes onto Kalam DS's glyph layout (Noto Sans Gujarati, 192x192 pad)  → fitted.json
python3 run_fit.py

# 5. Render every letter with numbered, arrowed strokes to check by eye
python3 sheet.py fitted.json check.png
```

### How each step works

- **`extract.py`**
  1. Masks the black arrows that lie on the white letter.
  2. Removes thin outlines with a morphological opening. The arrows are about 20px thick, the outlines about 3px.
  3. Skeletonises the arrows.
  4. Traces each stroke "like a pen": it starts at the stroke's circle and keeps stepping along the skeleton, preferring the straightest continuation. This lets it go straight through crossings, as in ક, જ and ફ. It tries 16 starting directions and keeps the longest trace that heads away from the circle.
- **`fix.py`** is where the hand-checked corrections live:
  - **`ORDER`** maps each detected circle (A, B, C, … in detection order) to the number printed in it. OCR can't read the digits reliably at the PDF's resolution, so they were read by eye.
  - **`ROUTES`** gives rough waypoints for the three strokes whose tight curls the tracer can't follow (ભ, મ, ક્ષ). Each leg is snapped to the shortest path along the skeleton.
- **`run_fit.py` / `fit.html`** handle the fact that the worksheet's font differs slightly from Noto Sans Gujarati. They lay out each glyph exactly as the game does (`lay()` in `index.html`). Then they search over scale, aspect ratio and offset so the stroke centre lines sit as deep inside the glyph as possible. Finally the points are thinned to about 3px spacing.

Set `FONTS_CSS=/path/to/fonts.css` if Google Fonts can't be reached from where you run it. The CSS should contain `@font-face` rules pointing at local copies of Noto Sans Gujarati 500.

## Data format

```json
{
  "coordinates": { "pad": 192, "font": "Noto Sans Gujarati, weight 500", ... },
  "letters": {
    "ક": [ [[x, y], [x, y], ...], [[x, y], ...] ]
  }
}
```

Each letter is a list of strokes in writing order. Each stroke is a polyline running from start to end, so it also encodes direction. A one-point stroke is a dot (anusvara અં, visarga અઃ).

**Coverage:** 46 letters with 129 strokes. That's every vowel and consonant in the school chart except ઋ, ઙ and ઞ, which the worksheets don't include. The numerals ૦–૯ aren't covered either. These can be recorded in the game's STROKE LAB.
