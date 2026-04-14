"""
Typography and readability validation.

Checks defined in CONTEXT.md:

    • Minimum body font size — 16 px baseline; below is flagged.
    • Line height ratio — 1.4 to 1.6 for body text.
    • Optimal reading measure — 45–75 characters per line (CPL).
    • Heading contrast — delegated to colour.validate_heading_contrast().

The CPL the designer specifies is taken at face value; this module validates
it against the 45–75 optimal range. If Claude doesn't supply CPL, the
validator estimates it from font size (a rough heuristic at ~2.3 chars/px).
"""

from __future__ import annotations

BODY_SIZE_MIN_PX = 16.0
LINE_HEIGHT_MIN = 1.4
LINE_HEIGHT_MAX = 1.6
CPL_MIN = 45
CPL_MAX = 75

# Approximate characters-per-pixel for a typical proportional font at body size.
# Used only when CPL is not explicitly supplied by Claude.
_CHARS_PER_PX_ESTIMATE = 2.3


def validate_typography(typography: dict) -> dict:
    """
    Validate the typography block from the Claude tool response.

    Parameters
    ----------
    typography : {
        "display": { "family", "weight", "size_px", "rationale" },
        "body":    { "family", "weight", "size_px", "line_height",
                     "characters_per_line", "rationale" },
        "pairing_rationale": str,
    }

    Returns
    -------
    {
        "min_body_size_pass": bool,
        "line_height_pass": bool,
        "reading_measure_pass": bool,
        "body_size_px": float,
        "line_height": float,
        "characters_per_line": int,
        "failures": [str],   # human-readable failure descriptions for Claude
    }
    """
    body = typography.get("body", {})
    failures: list[str] = []

    # ── Body size ─────────────────────────────────────────────────────────────
    body_size_px = float(body.get("size_px", 0))
    min_body_size_pass = body_size_px >= BODY_SIZE_MIN_PX
    if not min_body_size_pass:
        failures.append(
            f"Body font size is {body_size_px}px — below the 16px minimum. "
            "Increase body size_px to at least 16."
        )

    # ── Line height ───────────────────────────────────────────────────────────
    line_height = float(body.get("line_height", 0))
    line_height_pass = LINE_HEIGHT_MIN <= line_height <= LINE_HEIGHT_MAX
    if not line_height_pass:
        if line_height < LINE_HEIGHT_MIN:
            failures.append(
                f"Body line_height is {line_height} — too tight for comfortable "
                f"reading. Target 1.4–1.6."
            )
        else:
            failures.append(
                f"Body line_height is {line_height} — too loose. "
                "Target 1.4–1.6."
            )

    # ── Reading measure ───────────────────────────────────────────────────────
    cpl = body.get("characters_per_line")
    if cpl is None:
        # Estimate from font size if not provided
        if body_size_px > 0:
            cpl = int(body_size_px * _CHARS_PER_PX_ESTIMATE)
        else:
            cpl = CPL_MIN  # can't check — assume pass
    cpl = int(cpl)
    reading_measure_pass = CPL_MIN <= cpl <= CPL_MAX
    if not reading_measure_pass:
        if cpl < CPL_MIN:
            failures.append(
                f"Reading measure is ~{cpl} characters per line — too narrow. "
                "Target 45–75 CPL."
            )
        else:
            failures.append(
                f"Reading measure is ~{cpl} characters per line — too wide "
                "for comfortable reading. Target 45–75 CPL."
            )

    return {
        "min_body_size_pass": min_body_size_pass,
        "line_height_pass": line_height_pass,
        "reading_measure_pass": reading_measure_pass,
        "body_size_px": body_size_px,
        "line_height": line_height,
        "characters_per_line": cpl,
        "failures": failures,
    }
