"""
Colour validation: WCAG contrast checking and palette harmony scoring.

All luminance and contrast calculations use NumPy for correctness and
consistency with the Phase 2 image-analysis layer.

WCAG contrast ratio formula:
    (L_lighter + 0.05) / (L_darker + 0.05)
where L is relative luminance per IEC 61966-2-1.

Thresholds:
    AA  normal text  : 4.5 : 1
    AA  large text   : 3.0 : 1  (≥18 pt regular or ≥14 pt bold)
    AAA normal text  : 7.0 : 1
"""

from __future__ import annotations

import math
import numpy as np


# ── Colour conversion helpers ─────────────────────────────────────────────────

def hex_to_rgb(hex_colour: str) -> np.ndarray:
    """Convert a hex colour string to a NumPy array of [R, G, B] in 0–255."""
    h = hex_colour.lstrip("#")
    if len(h) != 6:
        raise ValueError(f"Invalid hex colour: {hex_colour!r}")
    return np.array([int(h[i : i + 2], 16) for i in (0, 2, 4)], dtype=np.float64)


def rgb_to_relative_luminance(rgb: np.ndarray) -> float:
    """
    Compute WCAG relative luminance from an RGB array (values 0–255).
    IEC 61966-2-1 linearisation.
    """
    srgb = rgb / 255.0
    linear = np.where(
        srgb <= 0.04045,
        srgb / 12.92,
        ((srgb + 0.055) / 1.055) ** 2.4,
    )
    weights = np.array([0.2126, 0.7152, 0.0722])
    return float(np.dot(weights, linear))


def contrast_ratio(hex_a: str, hex_b: str) -> float:
    """Return the WCAG contrast ratio between two hex colours."""
    l_a = rgb_to_relative_luminance(hex_to_rgb(hex_a))
    l_b = rgb_to_relative_luminance(hex_to_rgb(hex_b))
    lighter = max(l_a, l_b)
    darker = min(l_a, l_b)
    return (lighter + 0.05) / (darker + 0.05)


def hex_to_hsl(hex_colour: str) -> tuple[float, float, float]:
    """Convert hex to HSL tuple (h in 0–360, s and l in 0–1)."""
    rgb = hex_to_rgb(hex_colour) / 255.0
    r, g, b = rgb
    c_max = float(np.max(rgb))
    c_min = float(np.min(rgb))
    delta = c_max - c_min

    # Lightness
    l = (c_max + c_min) / 2.0

    # Saturation
    if delta == 0:
        s = 0.0
        h = 0.0
    else:
        s = delta / (1.0 - abs(2.0 * l - 1.0))

        if c_max == r:
            h = 60.0 * (((g - b) / delta) % 6)
        elif c_max == g:
            h = 60.0 * (((b - r) / delta) + 2)
        else:
            h = 60.0 * (((r - g) / delta) + 4)

    return (h % 360, s, l)


# ── WCAG checks ───────────────────────────────────────────────────────────────

WCAG_AA_NORMAL = 4.5
WCAG_AA_LARGE = 3.0
WCAG_AAA_NORMAL = 7.0


def _colour_by_role(palette: list[dict], role: str) -> str | None:
    """Return the hex of the first palette entry matching role, or None."""
    for entry in palette:
        if entry.get("role", "").lower() == role:
            return entry["hex"]
    return None


def validate_colour(palette: list[dict]) -> dict:
    """
    Run WCAG AA/AAA checks and harmony scoring on a 5-colour palette.

    Parameters
    ----------
    palette : list of dicts with keys role, hex, hsl, name, rationale.
              Expected roles: background, surface, primary, secondary, accent.

    Returns
    -------
    {
        "wcag_aa_pass": bool,
        "wcag_aaa_flag": bool,
        "harmony_score": float,
        "contrast_pairs": [{"pair": str, "ratio": float, "aa": bool, "aaa": bool}],
    }
    """
    background = _colour_by_role(palette, "background")
    surface = _colour_by_role(palette, "surface")
    primary = _colour_by_role(palette, "primary")
    secondary = _colour_by_role(palette, "secondary")
    accent = _colour_by_role(palette, "accent")

    contrast_pairs: list[dict] = []
    aa_results: list[bool] = []
    aaa_results: list[bool] = []

    def _check(fg_hex: str | None, bg_hex: str | None, label: str) -> None:
        if fg_hex is None or bg_hex is None:
            return
        ratio = round(contrast_ratio(fg_hex, bg_hex), 2)
        aa = ratio >= WCAG_AA_NORMAL
        aaa = ratio >= WCAG_AAA_NORMAL
        contrast_pairs.append({"pair": label, "ratio": ratio, "aa": aa, "aaa": aaa})
        aa_results.append(aa)
        aaa_results.append(aaa)

    # Text colours on background (normal text threshold: 4.5:1)
    _check(primary, background, "primary on background")
    _check(secondary, background, "secondary on background")
    _check(primary, surface, "primary on surface")

    # Accent is informational — note result but don't fail the suite on it
    if accent and background:
        ratio = round(contrast_ratio(accent, background), 2)
        aaa_flag_accent = ratio >= WCAG_AAA_NORMAL
        contrast_pairs.append({
            "pair": "accent on background",
            "ratio": ratio,
            "aa": ratio >= WCAG_AA_NORMAL,
            "aaa": aaa_flag_accent,
        })
        # Accent informational only — not added to aa_results

    wcag_aa_pass = all(aa_results) if aa_results else False
    wcag_aaa_flag = any(aaa_results) if aaa_results else False

    return {
        "wcag_aa_pass": wcag_aa_pass,
        "wcag_aaa_flag": wcag_aaa_flag,
        "harmony_score": round(_harmony_score(palette), 3),
        "contrast_pairs": contrast_pairs,
    }


# ── Harmony scoring ───────────────────────────────────────────────────────────

_HARMONIC_INTERVALS = [0.0, 30.0, 60.0, 90.0, 120.0, 150.0, 180.0]
_HARMONIC_TOLERANCE = 20.0  # degrees


def _angular_distance(a: float, b: float) -> float:
    """Shortest angular distance between two hue values (0–360)."""
    diff = abs(a - b) % 360
    return min(diff, 360 - diff)


def _proximity_to_harmonic(diff: float) -> float:
    """
    Score 0–1 for how close a hue difference is to a recognised harmonic interval.
    1.0 = exactly on a harmonic; drops linearly to 0.0 at ±_HARMONIC_TOLERANCE.
    """
    best = min(abs(diff - interval) for interval in _HARMONIC_INTERVALS)
    if best >= _HARMONIC_TOLERANCE:
        return 0.0
    return 1.0 - (best / _HARMONIC_TOLERANCE)


def _harmony_score(palette: list[dict]) -> float:
    """
    HSL-based palette harmony score in [0, 1].

    Chromatic colours (saturation > 8 %) are extracted and their pairwise
    hue differences are scored against known harmonic intervals. Achromatic
    palettes (e.g. pure black/white/grey) are treated as coherent by design.
    """
    hsl_values = []
    for entry in palette:
        try:
            h, s, l = hex_to_hsl(entry["hex"])
            hsl_values.append((h, s, l))
        except (ValueError, KeyError):
            continue

    chromatic = [(h, s, l) for h, s, l in hsl_values if s > 0.08]

    if len(chromatic) < 2:
        # Monochromatic or near-achromatic palette — inherently coherent
        return 0.93

    hues = [h for h, s, l in chromatic]

    # Check for near-monochromatic (all hues within 30°)
    hue_range = _hue_arc(hues)
    if hue_range <= 30:
        return 0.92

    # Check for analogous (all within 60°)
    if hue_range <= 60:
        return 0.88

    # Score pairwise harmonic proximity
    scores = []
    for i in range(len(hues)):
        for j in range(i + 1, len(hues)):
            diff = _angular_distance(hues[i], hues[j])
            scores.append(_proximity_to_harmonic(diff))

    if not scores:
        return 0.50

    mean_score = float(np.mean(scores))

    # Apply a soft penalty for completely spread hues (no harmonic pattern)
    if hue_range > 180 and mean_score < 0.3:
        mean_score *= 0.75

    # Clamp to [0.1, 0.98]
    return max(0.10, min(0.98, mean_score))


def _hue_arc(hues: list[float]) -> float:
    """
    Compute the smallest arc (degrees) that covers all hues.
    Handles wrap-around at 360°.
    """
    if not hues:
        return 0.0
    sorted_h = sorted(hues)
    # Gaps between consecutive hues + the wrap-around gap
    gaps = [
        sorted_h[i + 1] - sorted_h[i] for i in range(len(sorted_h) - 1)
    ]
    wrap_gap = (sorted_h[0] + 360) - sorted_h[-1]
    largest_gap = max(gaps + [wrap_gap])
    return 360.0 - largest_gap


# ── Heading contrast convenience check ───────────────────────────────────────

def validate_heading_contrast(palette: list[dict]) -> bool:
    """
    Check that display/heading colour (primary role) meets WCAG AA on
    background — using large-text threshold (3:1) since headings are large.
    """
    primary = _colour_by_role(palette, "primary")
    background = _colour_by_role(palette, "background")
    if primary is None or background is None:
        return True  # can't check — don't block on missing data
    ratio = contrast_ratio(primary, background)
    return ratio >= WCAG_AA_LARGE
