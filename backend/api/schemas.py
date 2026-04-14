"""
Pydantic models for the Phase 1 API.

These models define the exact output schema specified in CONTEXT.md.
The typography models include size_px, line_height, and characters_per_line
as additional fields (beyond the CONTEXT.md minimum) because they are needed
by the validation layer and are useful design information for the frontend.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ── Request ───────────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    brief: str = Field(..., min_length=20, description="Freeform client brand brief.")


# ── Design archetype ──────────────────────────────────────────────────────────

class DesignArchetype(BaseModel):
    primary: str
    confidence: float
    distribution: dict[str, float]
    low_confidence: bool = False


# ── Colour palette ────────────────────────────────────────────────────────────

class ColourEntry(BaseModel):
    role: Literal["background", "surface", "primary", "secondary", "accent"]
    hex: str
    hsl: str
    name: str
    rationale: str


# ── Typography ────────────────────────────────────────────────────────────────

class DisplayFont(BaseModel):
    family: str
    weight: str
    size_px: float
    rationale: str


class BodyFont(BaseModel):
    family: str
    weight: str
    size_px: float
    line_height: float
    characters_per_line: int
    rationale: str


class Typography(BaseModel):
    display: DisplayFont
    body: BodyFont
    pairing_rationale: str


# ── Spacing ───────────────────────────────────────────────────────────────────

class Spacing(BaseModel):
    base_unit: int
    scale_ratio: float
    scale: list[float]
    rationale: str


# ── Layout rhythm ─────────────────────────────────────────────────────────────

class LayoutRhythm(BaseModel):
    margin_proportion: str
    density: Literal["comfortable", "tight", "airy"]
    hierarchy_signal: str
    rationale: str


# ── Validation ────────────────────────────────────────────────────────────────

class ContrastPair(BaseModel):
    pair: str
    ratio: float
    aa: bool
    aaa: bool


class ColourValidation(BaseModel):
    wcag_aa_pass: bool
    wcag_aaa_flag: bool
    harmony_score: float
    contrast_pairs: list[ContrastPair] = Field(default_factory=list)


class TypographyValidation(BaseModel):
    min_body_size_pass: bool
    line_height_pass: bool
    reading_measure_pass: bool
    heading_contrast_pass: bool


class SpacingValidation(BaseModel):
    scale_coherent: bool
    type_to_space_ratio_pass: bool
    density_consistent: bool


class Validation(BaseModel):
    colour: ColourValidation
    typography: TypographyValidation
    spacing: SpacingValidation
    correction_passes: int = 0


# ── Full response ─────────────────────────────────────────────────────────────

class GenerateResponse(BaseModel):
    brief_summary: str
    design_archetype: DesignArchetype
    colour_palette: list[ColourEntry]
    typography: Typography
    spacing: Spacing
    layout_rhythm: LayoutRhythm
    validation: Validation
    generated_at: str  # ISO 8601
