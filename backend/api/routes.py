"""
POST /generate — the core Phase 1 endpoint.

Pipeline:
    1. Classify the brief (scikit-learn → probability distribution)
    2. Call Claude with structured tool use → brand system proposal
    3. Validate the proposal (colour WCAG, typography, spacing)
    4. If critical failures, run one correction pass with Claude
    5. Return the complete structured response
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import anthropic
from fastapi import APIRouter, HTTPException

from backend.api.schemas import (
    ColourEntry,
    ColourValidation,
    ContrastPair,
    DesignArchetype,
    DisplayFont,
    BodyFont,
    GenerateRequest,
    GenerateResponse,
    LayoutRhythm,
    Spacing,
    SpacingValidation,
    Typography,
    TypographyValidation,
    Validation,
)
from backend.classifier.model import get_classifier
from backend.validator.colour import validate_colour, validate_heading_contrast
from backend.validator.spacing import validate_spacing
from backend.validator.typography import validate_typography

router = APIRouter()

# ── Claude configuration ──────────────────────────────────────────────────────

MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-4-6")

SYSTEM_PROMPT = """You are Atelier, R&D Creative Agency's internal AI-powered design aid. You generate rigorous, reasoned brand design foundations from client briefs.

Your role is to augment design thinking, not replace it. You propose; you never prescribe. Every output you produce is a starting point for a design conversation, not a finished answer.

Core principles:
1. Justify every proposal — the reasoning is the product. No rationale field may be empty or generic.
2. Treat accessibility and readability as design inputs, not checkboxes. Reason through how a real person will read the brand system at the intended size and context.
3. Name trade-offs explicitly. If a colour choice involves an accessibility compromise, surface it in the rationale so the designer can decide.
4. Use the classifier's probability distribution as a prior, not a rule. If the brief clearly points elsewhere, weight the brief and note the discrepancy.
5. Write rationale for a designer — plain language, design vocabulary, no technical jargon.

Hard constraints (these will be validated programmatically — violations trigger a correction pass):
- Colour: primary text on background must achieve at least 4.5:1 WCAG AA contrast. Secondary text on background must achieve 4.5:1. Use background and surface as base layers; primary and secondary as text; accent as highlight.
- Typography: body font size_px must be 16 or above. body line_height must be between 1.4 and 1.6. body characters_per_line must be between 45 and 75.
- Spacing: scale_ratio must be exactly one of 1.25, 1.333, 1.5, or 1.618. Scale values must follow that ratio from base_unit within 6% tolerance.

When proposing fonts: use real typefaces that exist — Google Fonts, Adobe Fonts, or well-known system fonts. Do not invent font names."""

# ── Tool definition ───────────────────────────────────────────────────────────

BRAND_SYSTEM_TOOL: dict = {
    "name": "generate_brand_system",
    "description": (
        "Generate a complete, validated brand design system — colour palette, "
        "typography pairing, spacing scale, and layout rhythm — with full written "
        "rationale for each decision. All rationale fields must be substantive "
        "(minimum 2 sentences). All hard constraints must be satisfied."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "brief_summary": {
                "type": "string",
                "description": (
                    "Concise 2–3 sentence synthesis of the brand brief: "
                    "what it is, who it is for, and the core tonal direction."
                ),
            },
            "colour_palette": {
                "type": "array",
                "description": "Exactly 5 colours forming a complete, harmonious palette.",
                "minItems": 5,
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "properties": {
                        "role": {
                            "type": "string",
                            "enum": ["background", "surface", "primary", "secondary", "accent"],
                            "description": "Semantic role of this colour in the system.",
                        },
                        "hex": {
                            "type": "string",
                            "description": "Hex colour value e.g. #3B2F2F",
                        },
                        "hsl": {
                            "type": "string",
                            "description": "HSL breakdown e.g. '0, 15%, 20%'",
                        },
                        "name": {
                            "type": "string",
                            "description": "Short evocative name for this colour, e.g. 'Deep Roast'.",
                        },
                        "rationale": {
                            "type": "string",
                            "description": (
                                "Why this colour, why this role. Cover: brand temperature, "
                                "industry context, audience, and how it reads against the "
                                "colours it will be paired with. Name any accessibility "
                                "trade-offs explicitly."
                            ),
                        },
                    },
                    "required": ["role", "hex", "hsl", "name", "rationale"],
                },
            },
            "typography": {
                "type": "object",
                "properties": {
                    "display": {
                        "type": "object",
                        "description": "Display / heading typeface.",
                        "properties": {
                            "family": {"type": "string"},
                            "weight": {"type": "string"},
                            "size_px": {
                                "type": "number",
                                "description": "Typical heading size in px (e.g. 48).",
                            },
                            "rationale": {
                                "type": "string",
                                "description": (
                                    "Personality, historical register, pairing logic, "
                                    "and how it signals hierarchy."
                                ),
                            },
                        },
                        "required": ["family", "weight", "size_px", "rationale"],
                    },
                    "body": {
                        "type": "object",
                        "description": "Body / reading typeface.",
                        "properties": {
                            "family": {"type": "string"},
                            "weight": {"type": "string"},
                            "size_px": {
                                "type": "number",
                                "description": "Body text size in px. MUST be 16 or above.",
                            },
                            "line_height": {
                                "type": "number",
                                "description": "Line height ratio. MUST be between 1.4 and 1.6.",
                            },
                            "characters_per_line": {
                                "type": "integer",
                                "description": "Target CPL. MUST be between 45 and 75.",
                            },
                            "rationale": {
                                "type": "string",
                                "description": (
                                    "Legibility at body size, rhythm, optical size behaviour, "
                                    "and why it pairs with the display choice."
                                ),
                            },
                        },
                        "required": [
                            "family",
                            "weight",
                            "size_px",
                            "line_height",
                            "characters_per_line",
                            "rationale",
                        ],
                    },
                    "pairing_rationale": {
                        "type": "string",
                        "description": (
                            "How display and body work together as a system: "
                            "contrast of personality, shared structure, hierarchy clarity."
                        ),
                    },
                },
                "required": ["display", "body", "pairing_rationale"],
            },
            "spacing": {
                "type": "object",
                "properties": {
                    "base_unit": {
                        "type": "integer",
                        "description": "Base spacing unit in px (typically 4 or 8).",
                    },
                    "scale_ratio": {
                        "type": "number",
                        "enum": [1.25, 1.333, 1.5, 1.618],
                        "description": "Scale multiplier. MUST be one of: 1.25, 1.333, 1.5, 1.618.",
                    },
                    "scale": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": (
                            "The full spacing scale derived from base_unit × scale_ratio. "
                            "Each step must be approximately base_unit × ratio^n."
                        ),
                    },
                    "rationale": {
                        "type": "string",
                        "description": (
                            "Why this base unit and ratio: density, rhythm, and breathing "
                            "room appropriate to the brand archetype."
                        ),
                    },
                },
                "required": ["base_unit", "scale_ratio", "scale", "rationale"],
            },
            "layout_rhythm": {
                "type": "object",
                "properties": {
                    "margin_proportion": {
                        "type": "string",
                        "description": "Described margin logic, e.g. '10% of viewport width'.",
                    },
                    "density": {
                        "type": "string",
                        "enum": ["comfortable", "tight", "airy"],
                        "description": "Overall spatial density of the layout.",
                    },
                    "hierarchy_signal": {
                        "type": "string",
                        "description": (
                            "How hierarchy is communicated — through scale, weight, "
                            "space, or colour — and how strong that signal is."
                        ),
                    },
                    "rationale": {
                        "type": "string",
                        "description": (
                            "How type, spacing, and colour interact at layout level: "
                            "margin proportions, rhythm, and density appropriate to "
                            "the predicted archetype."
                        ),
                    },
                },
                "required": ["margin_proportion", "density", "hierarchy_signal", "rationale"],
            },
        },
        "required": [
            "brief_summary",
            "colour_palette",
            "typography",
            "spacing",
            "layout_rhythm",
        ],
    },
}


# ── Claude call helper ────────────────────────────────────────────────────────

def _call_claude(
    client: anthropic.Anthropic,
    brief: str,
    archetype_result: dict,
    correction_context: str | None = None,
) -> dict:
    """
    Call Claude with the brand brief and classifier output.
    Returns the parsed tool input dict.

    correction_context: if provided, appended as a follow-up correction request.
    """
    distribution_str = ", ".join(
        f"{k}: {v:.2f}" for k, v in archetype_result["distribution"].items()
    )
    low_conf_note = (
        "\n\nNote: classifier confidence is low — the brief may span multiple "
        "archetypes or be ambiguous. Weight the brief text heavily and flag "
        "any discrepancy in your rationale."
        if archetype_result.get("low_confidence")
        else ""
    )

    user_content = (
        f"Brand brief:\n\n{brief}\n\n"
        f"Classifier archetype distribution (probability across categories):\n"
        f"{distribution_str}\n"
        f"Primary archetype: {archetype_result['primary']} "
        f"(confidence: {archetype_result['confidence']:.0%})"
        f"{low_conf_note}"
    )

    messages: list[dict] = [{"role": "user", "content": user_content}]

    if correction_context:
        # Add Claude's previous (failed) tool call as assistant turn, then
        # the validator's correction request as the next user turn.
        messages.append({
            "role": "assistant",
            "content": correction_context,
        })
        messages.append({
            "role": "user",
            "content": (
                "The proposal above failed programmatic validation. "
                "Please revise it — use the same tool — and in each revised "
                "rationale field note what you changed and why."
            ),
        })

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        tools=[BRAND_SYSTEM_TOOL],
        tool_choice={"type": "tool", "name": "generate_brand_system"},
        messages=messages,
    )

    # Extract the tool use block
    for block in response.content:
        if block.type == "tool_use" and block.name == "generate_brand_system":
            return block.input

    raise RuntimeError("Claude did not return a generate_brand_system tool call.")


def _tool_call_as_assistant_text(tool_input: dict) -> str:
    """
    Serialise a previous tool call so it can be replayed as an assistant turn
    for the correction pass conversation.
    """
    return json.dumps(tool_input, indent=2)


# ── Validation orchestration ──────────────────────────────────────────────────

def _run_validation(proposal: dict, archetype: str) -> tuple[Validation, list[str]]:
    """
    Run all three validation suites. Return (Validation, list_of_failures).
    failures is empty when all checks pass.
    """
    palette = proposal["colour_palette"]
    typo = proposal["typography"]
    spacing_data = proposal["spacing"]

    # Colour
    colour_result = validate_colour(palette)
    heading_contrast_pass = validate_heading_contrast(palette)

    colour_validation = ColourValidation(
        wcag_aa_pass=colour_result["wcag_aa_pass"],
        wcag_aaa_flag=colour_result["wcag_aaa_flag"],
        harmony_score=colour_result["harmony_score"],
        contrast_pairs=[ContrastPair(**p) for p in colour_result["contrast_pairs"]],
    )

    # Typography
    typo_result = validate_typography(typo)
    typography_validation = TypographyValidation(
        min_body_size_pass=typo_result["min_body_size_pass"],
        line_height_pass=typo_result["line_height_pass"],
        reading_measure_pass=typo_result["reading_measure_pass"],
        heading_contrast_pass=heading_contrast_pass,
    )

    # Spacing
    body_size_px = typo_result["body_size_px"]
    spacing_result = validate_spacing(spacing_data, archetype, body_size_px)
    spacing_validation = SpacingValidation(
        scale_coherent=spacing_result["scale_coherent"],
        type_to_space_ratio_pass=spacing_result["type_to_space_ratio_pass"],
        density_consistent=spacing_result["density_consistent"],
    )

    # Collect all failure messages for the correction pass
    all_failures = (
        colour_result.get("failures", [])
        + typo_result["failures"]
        + spacing_result["failures"]
    )

    # Add colour failures not already in colour_result (WCAG)
    if not colour_result["wcag_aa_pass"]:
        failed_pairs = [
            p for p in colour_result["contrast_pairs"]
            if not p["aa"] and "accent" not in p["pair"]
        ]
        for p in failed_pairs:
            all_failures.append(
                f"WCAG AA contrast failure: {p['pair']} has ratio {p['ratio']:.1f}:1 "
                f"(minimum 4.5:1 for normal text). Adjust the colours to meet AA."
            )

    if not heading_contrast_pass:
        all_failures.append(
            "Heading contrast: primary colour on background does not meet 3:1 "
            "for large text. Increase the contrast between primary and background."
        )

    validation = Validation(
        colour=colour_validation,
        typography=typography_validation,
        spacing=spacing_validation,
        correction_passes=0,
    )

    critical_failures = [
        f for f in all_failures
        if any(
            kw in f.lower()
            for kw in ["wcag", "contrast", "body font size", "body size", "line_height",
                       "scale does not", "scale ratio"]
        )
    ]

    return validation, critical_failures


def _has_critical_failures(validation: Validation) -> bool:
    """Return True when any check that blocks output quality has failed."""
    return (
        not validation.colour.wcag_aa_pass
        or not validation.typography.min_body_size_pass
        or not validation.typography.line_height_pass
        or not validation.spacing.scale_coherent
    )


# ── Route ─────────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest) -> GenerateResponse:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured.")

    client = anthropic.Anthropic(api_key=api_key)

    # ── Step 1: Classify brief ────────────────────────────────────────────────
    classifier = get_classifier()
    archetype_result = classifier.predict(req.brief)

    # ── Step 2: Initial Claude call ───────────────────────────────────────────
    proposal = _call_claude(client, req.brief, archetype_result)

    # ── Step 3: Validate ──────────────────────────────────────────────────────
    validation, failures = _run_validation(proposal, archetype_result["primary"])
    correction_passes = 0

    # ── Step 4: Correction pass (max 1) ───────────────────────────────────────
    if _has_critical_failures(validation) and failures:
        failure_summary = "\n".join(f"- {f}" for f in failures)
        correction_context = (
            f"<previous_proposal>\n"
            f"{_tool_call_as_assistant_text(proposal)}\n"
            f"</previous_proposal>\n\n"
            f"Validation failures that must be corrected:\n{failure_summary}"
        )
        proposal = _call_claude(
            client, req.brief, archetype_result, correction_context=correction_context
        )
        validation, _ = _run_validation(proposal, archetype_result["primary"])
        correction_passes = 1

    validation.correction_passes = correction_passes

    # ── Step 5: Assemble response ─────────────────────────────────────────────
    palette = [ColourEntry(**c) for c in proposal["colour_palette"]]

    display_raw = proposal["typography"]["display"]
    body_raw = proposal["typography"]["body"]

    typography = Typography(
        display=DisplayFont(
            family=display_raw["family"],
            weight=display_raw["weight"],
            size_px=float(display_raw.get("size_px", 48)),
            rationale=display_raw["rationale"],
        ),
        body=BodyFont(
            family=body_raw["family"],
            weight=body_raw["weight"],
            size_px=float(body_raw.get("size_px", 16)),
            line_height=float(body_raw.get("line_height", 1.5)),
            characters_per_line=int(body_raw.get("characters_per_line", 65)),
            rationale=body_raw["rationale"],
        ),
        pairing_rationale=proposal["typography"]["pairing_rationale"],
    )

    spacing_raw = proposal["spacing"]
    spacing = Spacing(
        base_unit=int(spacing_raw["base_unit"]),
        scale_ratio=float(spacing_raw["scale_ratio"]),
        scale=[float(v) for v in spacing_raw["scale"]],
        rationale=spacing_raw["rationale"],
    )

    layout_raw = proposal["layout_rhythm"]
    layout_rhythm = LayoutRhythm(
        margin_proportion=layout_raw["margin_proportion"],
        density=layout_raw["density"],
        hierarchy_signal=layout_raw["hierarchy_signal"],
        rationale=layout_raw["rationale"],
    )

    archetype_schema = DesignArchetype(
        primary=archetype_result["primary"],
        confidence=archetype_result["confidence"],
        distribution=archetype_result["distribution"],
        low_confidence=archetype_result.get("low_confidence", False),
    )

    return GenerateResponse(
        brief_summary=proposal["brief_summary"],
        design_archetype=archetype_schema,
        colour_palette=palette,
        typography=typography,
        spacing=spacing,
        layout_rhythm=layout_rhythm,
        validation=validation,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
