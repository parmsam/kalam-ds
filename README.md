# કલમ Kalam DS

A Nintendo DS–style web game for learning to **write** the Gujarati alphabet. It's the companion to [Akshar Boy](https://github.com/parmsam/akshar-boy), which teaches you to *read* the letters.

*Vibe coded with [Claude](https://claude.ai) by Anthropic.*

**▶ Play: https://parmsam.github.io/kalam-ds/**

The top screen shows the letter, its sound and your grade. You write on the bottom screen with a finger, stylus or mouse.

## Modes

- **TRACE**: write over a faint copy of the letter.
- **GHOST**: the outline is barely visible. If the letter has stroke data, numbered start dots show where each stroke begins.
- **FREE WRITE**: copy the letter from the top screen onto blank paper. Size and position don't matter, because your writing is rescaled before it's scored.
- **RECALL**: you hear the sound and see the romanization and a hint, and write the letter from memory. The letter stays hidden until you check.
- **STROKE LAB**: record the stroke order for each letter (see below).

Pick a letter to practise from the chart, or press START for **Random 10**, a drill that brings up weak and unseen letters more often. Sets: all letters, vowels only, consonants only, or numerals ૦–૯.

## Scoring

The font's glyph (Noto Sans Gujarati) is the answer key. Your ink and the glyph are rasterised and compared:

- **ON SHAPE**: how much of your ink lands on the letter.
- **COVERED**: how much of the letter your ink covers.

The two are combined into a score from 0 to 100, with ink on the shape weighted a little more heavily so that scribbling over the box doesn't pay off. ★ is 60 and up, ★★ is 75 and up, ★★★ is 90 and up. A letter counts as **mastered** when it scores 75 or more in FREE or RECALL. Best scores are saved in your browser's localStorage.

After you check, the top screen draws your writing over the correct letter so you can see where it drifted.

## Stroke order

There's no open dataset of Gujarati stroke order (nothing like KanjiVG for Japanese), so the game includes a tool for recording it:

1. Open **STROKE LAB** and pick a letter with ◀ ▶.
2. Draw each stroke in the order and direction it's written, then **SAVE**. Saving with nothing drawn deletes the letter's recording.
3. That letter then gets:
   - an **ORDER** animation on the top screen (X)
   - numbered start dots in TRACE and GHOST
   - stroke checks when you're graded: wrong stroke count, a stroke drawn backwards, or a stroke starting in the wrong place

Recordings are saved in localStorage. **DATA** shows them as JSON, with COPY and IMPORT buttons. To ship them with the game, paste the JSON into the `BUILTIN` constant near the top of the script in `index.html`.

## Controls

| Key | Button | Action |
|---|---|---|
| Arrow keys | D-pad | move · ◀ ▶ change letter |
| `X` / `Space` | A | choose · check · next |
| `Z` / `Esc` | B | back |
| `C` | Y | clear · retry |
| `W` | X | watch stroke order |
| `Backspace` / `Ctrl+Z` | — | undo last stroke |
| `Shift` / `H` | SELECT | hear the letter |
| `Enter` | START | random 10 · menu |

On touch screens, tap the on-screen buttons or the bottom screen directly.

## Akshar Boy progress

If both games are served from the same origin (both on `parmsam.github.io`), Kalam DS reads Akshar Boy's saved progress. Letters you've mastered there get a magenta dot on the letter chart, so you can write the letters you can already read.

## Pronunciation audio

This works the same way as in Akshar Boy, using the browser's Web Speech API. It uses a Gujarati voice if one is installed, otherwise a Hindi voice (the two scripts map letter for letter), otherwise an English voice reading the romanization.

## Development

It's a single self-contained `index.html` with no build step. Open it in a browser, or serve it locally:

```sh
python3 -m http.server
```

Fonts (Press Start 2P, VT323, Noto Sans Gujarati) load from Google Fonts. Scoring waits for Noto Sans Gujarati to load. If it can't load, scoring falls back to whatever Gujarati font the system has, and still works.

## License

MIT — see [LICENSE](LICENSE).
