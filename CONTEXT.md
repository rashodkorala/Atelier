# Atelier

### Internal Design Decision Aid — R&D Creative Agency

-----

## Philosophy

Atelier augments design thinking. It does not replace it.

The goal is not to hand design decisions to a machine. The goal is to give the designer a rigorous, reasoned starting point – one that handles the mechanical, time-consuming groundwork so the designer can focus on the parts that actually require taste, client intuition, and creative judgment.

Atelier surfaces options with reasoning. The designer agrees, challenges, or redirects. That conversation is where the real design work happens. Atelier just makes sure it starts from somewhere defensible.

Accessibility and human readability are not constraints bolted on after the fact. They are design criteria from the start – first-class inputs to every proposal Atelier makes, across colour, typography, spacing, and layout rhythm.

-----

## What Atelier Is

Atelier is R&D Creative Agency's internal AI-powered design aid. It takes a raw client brief and generates a justified brand design foundation – colour palette, typography pairing, and spacing scale – with explicit reasoning behind every proposal.

Atelier is built for speed without sacrificing rigour. It is the first tool R&D reaches for at the start of any branding engagement, compressing what would typically be a multi-day discovery and moodboarding process into a structured, reviewable starting point.

The output is a proposal, not a verdict. Every suggestion is grounded in colour science, typographic principle, and brand strategy – validated programmatically and written in plain language so the designer can engage with it directly.

-----

## The Problem It Solves

Early-stage branding work at R&D involves a recurring bottleneck: translating a client's freeform brief into a coherent visual direction takes significant time, and the reasoning behind early decisions is often undocumented. When a client asks "why this colour?" or "why not a serif?", the answer lives in the designer's head.

Atelier externalises that reasoning. It makes the decision-making process explicit, repeatable, and reviewable – for the agency, for the designer, and eventually for the client.

-----

## How Atelier Thinks

Atelier operates in two stages:

### Stage 1 — Brief Classification (ML Layer)

A scikit-learn classifier, trained on a labelled dataset of brand briefs mapped to design archetypes, reads the incoming brief and predicts a design style category. Categories include:

- `editorial` – typography-led, restrained palette, high contrast, tight layout density, long line lengths
- `warm-minimal` – organic tones, generous whitespace, approachable type, loose rhythm, comfortable reading measure
- `bold-expressive` – saturated colour, strong hierarchy, display-forward, high spatial contrast between elements
- `corporate-clean` – neutral palette, structured grid, professional type, consistent density, predictable layout rhythm
- `luxury-refined` – muted tones, serif-led, precise spacing, generous margins, slow pacing
- `playful-energetic` – high chroma, irregular rhythm, friendly type, variable density, short reading measures

The classifier output is a probability distribution across categories, not a hard label. This distribution is passed directly to Claude as context, preserving uncertainty rather than flattening it.

pandas manages the reference dataset. NumPy handles the vectorisation of brief text features fed into the classifier.

### Stage 2 — AI Reasoning Layer (Claude)

Claude receives the original brief alongside the classifier's probability distribution and proposes three elements, each with written reasoning the designer can engage with directly:

1. **Colour palette** – five colours with hex values, HSL breakdown, and a written rationale for each. Claude considers brand temperature, industry context, audience, palette harmony, and foreground/background readability.
1. **Typography pairing** – a display font and a body font, with rationale covering personality, legibility, pairing logic, and human readability at intended sizes. Claude reasons through line height, optimal reading measure (45-75 characters), and minimum body size for the intended context.
1. **Spacing scale** – a base unit and a scale multiplier, with rationale covering the density, rhythm, and breathing room appropriate to the brand's tone and layout context.
1. **Layout rhythm** – a proposed spatial logic for how type, spacing, and colour interact at a layout level: margin proportions, hierarchy signal strength, and density appropriate to the archetype.

Claude reasons against constraints rather than generating freely: WCAG contrast minimums, typographic pairing principles, and spacing coherence rules. Where a proposal involves a trade-off, Claude names it explicitly so the designer can make an informed call.

### Stage 3 — Validation Layer (Python)

Before output is returned, a Python validation module runs a full accessibility and readability audit across colour, typography, and spacing:

**Colour**

- WCAG AA contrast check – all foreground/background combinations validated (4.5:1 for normal text, 3:1 for large text) using NumPy colour distance calculations
- WCAG AAA flag – combinations that meet AAA (7:1) are flagged as a bonus signal for the designer
- Palette harmony scoring – HSL-based analysis confirming the palette is internally coherent (complementary, analogous, or triadic relationships validated)

**Typography and Readability**

- Minimum body font size – 16px baseline enforced; anything below is flagged
- Line height ratio – validated within the 1.4 to 1.6 range for body text readability
- Optimal reading measure – line length checked against the 45-75 character optimal range based on the proposed font size and scale unit
- Heading contrast – display type validated against background at WCAG AA minimum

**Spacing and Layout**

- Scale coherence – confirms the spacing scale follows a consistent ratio (1.25, 1.333, 1.5, or 1.618)
- Type-to-space ratio – validates that surrounding space is proportionate to type size, ensuring adequate breathing room at each hierarchy level
- Density consistency – checks that the proposed layout rhythm is coherent with the predicted archetype

Validation failures are returned to Claude for a single correction pass. Claude revises the proposal, notes what changed and why, and the corrected output is returned to the designer.

-----

## Architecture Overview

**Phase 1 – Brand System Generation**

```
Client Brief (freeform text)
        │
        ▼
┌─────────────────────┐
│   pandas + NumPy    │  Load reference data, vectorise brief
│   scikit-learn      │  Classify design archetype (probability distribution)
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│    Claude API       │  Propose palette, type, spacing, layout rhythm
│    (vision + tools) │  Structured JSON output with rationale
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│   Python Validator  │  Colour, typography, spacing, readability checks
│   NumPy             │  Correction pass if validation fails
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│     FastAPI         │  Serve structured output via REST endpoint
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│   React Frontend    │  Display system + reasoning side by side
└─────────────────────┘
```

-----

## Input Specification

Atelier accepts a freeform brand brief via a single text field. No structured form. The brief should describe:

- What the brand does
- Who it is for
- The tone or feeling it should convey
- Any reference points, constraints, or explicit preferences

**Example brief:**

> "We run a small-batch coffee roastery in St. John's. Our customers are locals who take coffee seriously but hate pretension. We want to feel craft and warm but not rustic or folksy. Think considered, not precious."

Minimum viable brief: 2 sentences. Atelier degrades gracefully on sparse input but flags low-confidence outputs.

-----

## Output Specification

All output is structured JSON, rendered in the React UI with reasoning displayed alongside each decision.

```json
{
  "brief_summary": "string",
  "design_archetype": {
    "primary": "warm-minimal",
    "confidence": 0.74,
    "distribution": { ... }
  },
  "colour_palette": [
    {
      "role": "primary",
      "hex": "#3B2F2F",
      "hsl": "0, 15%, 20%",
      "name": "Deep Roast",
      "rationale": "string"
    }
  ],
  "typography": {
    "display": {
      "family": "Freight Display Pro",
      "weight": "400",
      "rationale": "string"
    },
    "body": {
      "family": "Söhne",
      "weight": "400",
      "rationale": "string"
    },
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
    "density": "comfortable | tight | airy",
    "hierarchy_signal": "string",
    "rationale": "string"
  },
  "validation": {
    "colour": {
      "wcag_aa_pass": true,
      "wcag_aaa_flag": false,
      "harmony_score": 0.87
    },
    "typography": {
      "min_body_size_pass": true,
      "line_height_pass": true,
      "reading_measure_pass": true,
      "heading_contrast_pass": true
    },
    "spacing": {
      "scale_coherent": true,
      "type_to_space_ratio_pass": true,
      "density_consistent": true
    },
    "correction_passes": 0
  },
  "generated_at": "ISO 8601 timestamp"
}
```

-----

## Claude's Reasoning Principles

Claude operates as a reasoning aid, not a decision-maker. Its role is to surface well-grounded proposals with transparent reasoning so the designer can engage, challenge, or redirect with full context.

When working through a brief, Claude follows these principles:

1. **Propose, don't prescribe.** Every output is a starting point for a design conversation, not a finished answer.
1. **Justify every proposal.** No output without rationale. The reasoning is the product.
1. **Treat accessibility and readability as design inputs, not checkboxes.** Reason through how a real person will read and navigate the brand system – at what size, in what context, with what visual load. Accessibility is not a constraint applied at the end; it informs the proposal from the start.
1. **Name trade-offs explicitly.** If a colour is less accessible but more on-brand, say so and surface the call for the designer to make. Never silently resolve a tension.
1. **Respect the validation layer.** If a proposal fails validation, revise it and note what changed and why.
1. **Use the classifier output as a prior, not a rule.** If the brief clearly contradicts the predicted archetype, weight the brief more heavily and flag the discrepancy.
1. **Write rationale for a designer, not a developer.** Plain language, design vocabulary, no jargon.

-----

## Current Status

Internal alpha. In active use on R&D Creative Agency client briefs.
