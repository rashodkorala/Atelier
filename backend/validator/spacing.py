"""
Spacing and layout rhythm validation.

Checks defined in CONTEXT.md:

    • Scale coherence — spacing values must follow one of the recognised
      ratios: 1.25, 1.333, 1.5, or 1.618, within a 6 % tolerance.
    • Type-to-space ratio — base spacing unit should be proportionate to
      body type size (base_unit ≈ body_size_px / 2, within 60 % tolerance).
    • Density consistency — proposed layout density should align with the
      archetype's characteristic density.

NumPy is used for the ratio-deviation calculations.
"""

from __future__ import annotations

import numpy as np


VALID_RATIOS = [1.25, 1.333, 1.5, 1.618]
RATIO_TOLERANCE = 0.06  # ±6 % from the declared ratio

# Expected density per archetype (from CONTEXT.md archetype descriptions)
ARCHETYPE_DENSITY: dict[str, list[str]] = {
    "editorial": ["tight", "comfortable"],
    "warm-minimal": ["comfortable", "airy"],
    "bold-expressive": ["tight", "comfortable"],
    "corporate-clean": ["comfortable"],
    "luxury-refined": ["airy", "comfortable"],
    "playful-energetic": ["comfortable", "airy"],
}


def validate_spacing(spacing: dict, archetype: str, body_size_px: float) -> dict:
    """
    Validate the spacing block from the Claude tool response.

    Parameters
    ----------
    spacing : {
        "base_unit": int,
        "scale_ratio": float,
        "scale": list[float],
        "rationale": str,
    }
    archetype : str — primary archetype label from the classifier.
    body_size_px : float — body font size, for type-to-space ratio check.

    Returns
    -------
    {
        "scale_coherent": bool,
        "type_to_space_ratio_pass": bool,
        "density_consistent": bool,
        "detected_ratio": float | None,
        "failures": [str],
    }
    """
    failures: list[str] = []

    base_unit = float(spacing.get("base_unit", 0))
    scale_ratio = float(spacing.get("scale_ratio", 0))
    scale: list[float] = [float(v) for v in spacing.get("scale", [])]
    density: str = spacing.get("density", "").lower()

    # ── Scale coherence ───────────────────────────────────────────────────────
    scale_coherent, detected_ratio = _check_scale_coherence(scale, scale_ratio)
    if not scale_coherent:
        closest = _nearest_valid_ratio(scale_ratio)
        failures.append(
            f"Spacing scale does not follow a coherent ratio. "
            f"Declared ratio is {scale_ratio}; nearest valid ratio is {closest}. "
            f"Rebuild the scale values from base_unit {int(base_unit)} × {closest}."
        )

    # ── Type-to-space ratio ───────────────────────────────────────────────────
    type_to_space_ratio_pass = _check_type_to_space(base_unit, body_size_px)
    if not type_to_space_ratio_pass and body_size_px > 0 and base_unit > 0:
        ideal = round(body_size_px / 2, 1)
        failures.append(
            f"Type-to-space ratio is off: base_unit is {int(base_unit)}px "
            f"against a body size of {body_size_px}px. "
            f"Ideal base_unit is around {ideal}px for this type size."
        )

    # ── Density consistency ───────────────────────────────────────────────────
    density_consistent = _check_density(density, archetype)
    if not density_consistent:
        expected = ARCHETYPE_DENSITY.get(archetype, ["comfortable"])
        failures.append(
            f"Proposed density '{density}' is inconsistent with the "
            f"'{archetype}' archetype. Expected one of: {expected}."
        )

    return {
        "scale_coherent": scale_coherent,
        "type_to_space_ratio_pass": type_to_space_ratio_pass,
        "density_consistent": density_consistent,
        "detected_ratio": detected_ratio,
        "failures": failures,
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _check_scale_coherence(
    scale: list[float], declared_ratio: float
) -> tuple[bool, float | None]:
    """
    Verify that consecutive scale values follow the declared ratio within
    RATIO_TOLERANCE, AND that the declared ratio is one of the valid options.

    Returns (is_coherent, detected_mean_ratio).
    """
    if declared_ratio not in VALID_RATIOS:
        # Check if it's close to a valid ratio within tolerance
        nearest = _nearest_valid_ratio(declared_ratio)
        if abs(declared_ratio - nearest) / nearest > RATIO_TOLERANCE:
            return False, None

    if len(scale) < 2:
        return True, declared_ratio  # can't verify a single value

    # Compute observed ratios between consecutive pairs (skip zero values)
    observed: list[float] = []
    for i in range(len(scale) - 1):
        a, b = scale[i], scale[i + 1]
        if a > 0 and b > 0:
            observed.append(b / a)

    if not observed:
        return True, declared_ratio

    observed_arr = np.array(observed)
    mean_ratio = float(np.mean(observed_arr))
    max_deviation = float(np.max(np.abs(observed_arr - declared_ratio) / declared_ratio))

    coherent = max_deviation <= RATIO_TOLERANCE
    return coherent, round(mean_ratio, 4)


def _nearest_valid_ratio(ratio: float) -> float:
    """Return the valid ratio closest to the given value."""
    return min(VALID_RATIOS, key=lambda r: abs(r - ratio))


def _check_type_to_space(base_unit: float, body_size_px: float) -> bool:
    """
    Validate that the base spacing unit is proportionate to body type size.
    Rule: base_unit should be between 0.375× and 0.75× of body_size_px.
    (For a 16px body: ideal range is 6–12px; default 8px is canonical.)
    """
    if base_unit <= 0 or body_size_px <= 0:
        return True  # missing data — don't block
    ratio = base_unit / body_size_px
    return 0.375 <= ratio <= 0.75


def _check_density(density: str, archetype: str) -> bool:
    """Check the proposed density against the archetype's expected values."""
    expected = ARCHETYPE_DENSITY.get(archetype, ["comfortable", "tight", "airy"])
    return density in expected
