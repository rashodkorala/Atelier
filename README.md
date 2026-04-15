# Atelier

Internal AI-powered brand design aid — R&D Creative Agency.

Takes a freeform client brief and generates a justified brand design foundation: colour palette, typography pairing, spacing scale, and layout rhythm. Every proposal comes with written reasoning the designer can engage with, challenge, or redirect.

---

## What it does

1. **Classifies the brief** using a scikit-learn TF-IDF + LogisticRegression model trained on labelled brand briefs. Output is a probability distribution across six design archetypes — not a hard label. Uncertainty is preserved and passed to Claude as context.

2. **Calls Claude** with the brief and classifier distribution via structured tool use. Claude proposes a complete brand system with substantive rationale on every field.

3. **Validates the proposal** programmatically: WCAG AA/AAA colour contrast, typography readability (body size, line height, reading measure), and spacing scale coherence.

4. **Runs a correction pass** if critical checks fail — Claude receives its own output alongside the specific failures and revises in a single follow-up turn.

5. **Returns structured JSON** rendered in the React frontend with reasoning displayed alongside each proposal.

---

## Design archetypes

| Archetype | Character |
|---|---|
| `editorial` | Typography-led, restrained palette, high contrast, tight density, long line lengths |
| `warm-minimal` | Organic tones, generous whitespace, approachable type, loose rhythm |
| `bold-expressive` | Saturated colour, strong hierarchy, display-forward, high spatial contrast |
| `corporate-clean` | Neutral palette, structured grid, professional type, predictable rhythm |
| `luxury-refined` | Muted tones, serif-led, precise spacing, generous margins, slow pacing |
| `playful-energetic` | High chroma, irregular rhythm, friendly type, short reading measures |

---

## Stack

| Layer | Technology |
|---|---|
| ML classifier | scikit-learn (TF-IDF + LogisticRegression), pandas, NumPy |
| AI reasoning | Anthropic Claude API — structured tool use, prompt caching |
| Backend | Python 3.11+, FastAPI, Pydantic (≥2.12), Uvicorn |
| Frontend | React 18, Vite |
| Validation | Pure Python + NumPy (WCAG luminance formula, HSL harmony) |

---

## Project structure

```
Atelier/
├── requirements.txt
├── .env.example
├── CONTEXT.md                  # Full architecture and philosophy doc
│
├── backend/
│   ├── main.py                 # FastAPI app, CORS, startup hook
│   ├── classifier/
│   │   ├── dataset.py          # 48 labelled training briefs (6 archetypes × 8)
│   │   └── model.py            # TF-IDF pipeline, ArchetypeClassifier singleton
│   ├── validator/
│   │   ├── colour.py           # WCAG contrast (NumPy), HSL harmony scoring
│   │   ├── typography.py       # Body size, line height, CPL checks
│   │   └── spacing.py          # Scale coherence, type-to-space ratio, density
│   └── api/
│       ├── schemas.py          # Pydantic models — exact CONTEXT.md output schema
│       └── routes.py           # POST /api/generate — full pipeline
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js          # Proxies /api → FastAPI on :8000
    └── src/
        ├── main.jsx
        └── App.jsx             # Single-page UI — input, pipeline progress, output
```

---

## Setup

### Prerequisites

- Python **3.11+** (use **Pydantic ≥2.12** so `pydantic-core` has wheels on 3.14 — see `requirements.txt`)
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com)

### Backend

```bash
# Clone and enter the repo
git clone <repo-url>
cd Atelier

# Create and activate a virtual environment (use python3 if `python` is not on PATH)
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Start the API server
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

Open `http://localhost:5173`. The Vite dev server proxies all `/api` requests to FastAPI on port 8000.

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required. Your Anthropic API key. |
| `CLAUDE_MODEL` | `claude-opus-4-6` | Claude model ID. Use `claude-sonnet-4-6` for faster/cheaper dev iteration. |
| `HOST` | `127.0.0.1` | FastAPI bind host. |
| `PORT` | `8000` | FastAPI bind port. |

---

## API

### `POST /api/generate`

Accepts a freeform brand brief and returns a complete brand system proposal.

**Request**

```json
{
  "brief": "We run a small-batch coffee roastery in St. John's. Our customers are locals who take coffee seriously but hate pretension. We want to feel craft and warm but not rustic or folksy."
}
```

Minimum brief length: 20 characters.

**Response** — full schema defined in `CONTEXT.md`:

```json
{
  "brief_summary": "string",
  "design_archetype": {
    "primary": "warm-minimal",
    "confidence": 0.74,
    "distribution": { "warm-minimal": 0.74, "editorial": 0.11, ... },
    "low_confidence": false
  },
  "colour_palette": [
    {
      "role": "background",
      "hex": "#F5F0EB",
      "hsl": "30, 33%, 94%",
      "name": "Parchment",
      "rationale": "string"
    }
    // ... 4 more (surface, primary, secondary, accent)
  ],
  "typography": {
    "display": { "family": "string", "weight": "string", "size_px": 48, "rationale": "string" },
    "body": { "family": "string", "weight": "string", "size_px": 16, "line_height": 1.5, "characters_per_line": 65, "rationale": "string" },
    "pairing_rationale": "string"
  },
  "spacing": {
    "base_unit": 8,
    "scale_ratio": 1.5,
    "scale": [4, 8, 12, 16, 24, 32, 48, 64, 96],
    "rationale": "string"
  },
  "layout_rhythm": {
    "margin_proportion": "string",
    "density": "comfortable",
    "hierarchy_signal": "string",
    "rationale": "string"
  },
  "validation": {
    "colour": { "wcag_aa_pass": true, "wcag_aaa_flag": false, "harmony_score": 0.87, "contrast_pairs": [...] },
    "typography": { "min_body_size_pass": true, "line_height_pass": true, "reading_measure_pass": true, "heading_contrast_pass": true },
    "spacing": { "scale_coherent": true, "type_to_space_ratio_pass": true, "density_consistent": true },
    "correction_passes": 0
  },
  "generated_at": "2026-04-14T20:00:00+00:00"
}
```

### `GET /health`

```json
{ "status": "ok", "service": "atelier-phase-1" }
```

---

## Validation rules

### Colour

| Check | Threshold |
|---|---|
| WCAG AA (normal text) | ≥ 4.5:1 contrast ratio |
| WCAG AA (large text) | ≥ 3.0:1 contrast ratio |
| WCAG AAA flag | ≥ 7.0:1 (informational) |
| Harmony score | HSL hue proximity to recognised harmonic intervals |

Pairs checked: `primary on background`, `secondary on background`, `primary on surface`. Accent on background is reported but does not fail the suite.

### Typography

| Check | Rule |
|---|---|
| Minimum body size | ≥ 16px |
| Line height | 1.4 – 1.6 |
| Reading measure | 45 – 75 characters per line |
| Heading contrast | Primary colour on background ≥ 3.0:1 (large text AA) |

### Spacing

| Check | Rule |
|---|---|
| Scale coherence | Consecutive values must follow declared ratio within ±6% |
| Valid ratios | 1.25, 1.333, 1.5, or 1.618 only |
| Type-to-space ratio | `base_unit` between 0.375× and 0.75× body size |
| Density consistency | Proposed density must align with archetype expectations |

---

## Correction pass

If any critical check fails (WCAG AA, body size, line height, or scale coherence), the validator collects human-readable failure descriptions and makes one additional Claude call. The failed proposal is serialised back into the conversation alongside the specific failures. Claude revises and notes what changed in each rationale field. `correction_passes` in the response reflects how many passes were needed.

---

## Classifier

The ML layer uses a scikit-learn pipeline: `TfidfVectorizer(ngram_range=(1,2), sublinear_tf=True)` → `LogisticRegression(C=2.0, multi_class='multinomial')`, trained on 48 hand-labelled briefs (8 per archetype).

The classifier is trained once at startup and cached as a module singleton. The probability distribution — not just the top label — is passed to Claude, so Claude can reason about ambiguous briefs. Outputs with confidence below 40% are flagged as `low_confidence` and noted in Claude's system prompt.

---

## Roadmap

| Phase | Scope |
|---|---|
| v0.1 (current) | Core pipeline, FastAPI, React UI, localhost only |
| v0.2 | Phase 2 visual audit layer — image input, colour extraction, mathematical layout analysis |
| v0.3 | Figma MCP integration — push generated system directly as Figma variables and styles |
| v0.4 | Session logging to pandas dataframe, building a proprietary R&D brief-to-system dataset |
| v0.5 | Fine-tune classifier on R&D's own dataset |
| v1.0 | Client-facing mode — shareable output links, PDF export, revision history |

---

## Maintainer

R&D Creative Agency — Rashod Korala, St. John's, Newfoundland.
