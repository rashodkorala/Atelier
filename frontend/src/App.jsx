import { useState, useEffect, useRef } from "react";

// ── Google Fonts loader ───────────────────────────────────────────────────────
function loadGoogleFont(family) {
  if (!family) return;
  const encoded = encodeURIComponent(family);
  const id = `gf-${encoded}`;
  if (document.getElementById(id)) return;
  const link = document.createElement("link");
  link.id = id;
  link.rel = "stylesheet";
  link.href = `https://fonts.googleapis.com/css2?family=${encoded.replace(/%20/g, "+")}:wght@300;400;500;600;700&display=swap`;
  document.head.appendChild(link);
}

// ── Inline styles ─────────────────────────────────────────────────────────────
const css = `
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #0e0e0e;
    --surface: #161616;
    --surface-2: #1e1e1e;
    --border: #2a2a2a;
    --text: #e8e8e8;
    --text-muted: #888;
    --text-dim: #555;
    --accent: #c8a97e;
    --accent-dim: rgba(200,169,126,0.12);
    --pass: #4caf50;
    --fail: #ef5350;
    --warn: #ffa726;
    --radius: 6px;
    --font-ui: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font-ui);
    font-size: 14px;
    line-height: 1.6;
    min-height: 100vh;
  }

  /* Layout */
  .app { max-width: 1100px; margin: 0 auto; padding: 48px 24px 96px; }

  /* Header */
  .header { margin-bottom: 56px; }
  .header h1 { font-size: 22px; font-weight: 500; letter-spacing: 0.12em; text-transform: uppercase; color: var(--text); }
  .header p { margin-top: 6px; color: var(--text-muted); font-size: 13px; letter-spacing: 0.04em; }

  /* Brief form */
  .form-section { margin-bottom: 40px; }
  .form-label { display: block; font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-muted); margin-bottom: 10px; }
  textarea {
    width: 100%; min-height: 140px; background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); color: var(--text); font-family: var(--font-ui); font-size: 14px;
    line-height: 1.6; padding: 16px; resize: vertical; outline: none; transition: border-color 0.15s;
  }
  textarea:focus { border-color: var(--accent); }
  textarea::placeholder { color: var(--text-dim); }

  .submit-row { display: flex; align-items: center; gap: 16px; margin-top: 14px; }
  button.generate {
    background: var(--accent); color: #0e0e0e; border: none; border-radius: var(--radius);
    font-family: var(--font-ui); font-size: 12px; font-weight: 600; letter-spacing: 0.1em;
    text-transform: uppercase; padding: 12px 28px; cursor: pointer; transition: opacity 0.15s;
  }
  button.generate:hover { opacity: 0.85; }
  button.generate:disabled { opacity: 0.4; cursor: not-allowed; }
  .char-count { font-size: 11px; color: var(--text-dim); }

  /* Error */
  .error { background: rgba(239,83,80,0.1); border: 1px solid rgba(239,83,80,0.3); border-radius: var(--radius); padding: 14px 16px; color: #ef5350; font-size: 13px; margin-bottom: 24px; }

  /* Loading */
  .loading { text-align: center; padding: 64px 0; }
  .loading-label { font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--text-muted); margin-top: 16px; }
  .spinner { width: 28px; height: 28px; border: 2px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.7s linear infinite; margin: 0 auto; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .pipeline-steps { margin-top: 24px; display: flex; flex-direction: column; gap: 6px; align-items: center; }
  .pipeline-step { font-size: 11px; color: var(--text-dim); letter-spacing: 0.06em; }
  .pipeline-step.active { color: var(--accent); }

  /* Section card */
  .card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 28px 32px; margin-bottom: 20px; }
  .card-title { font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--text-dim); margin-bottom: 20px; }

  /* Brief summary */
  .brief-summary { font-size: 15px; line-height: 1.7; color: var(--text); }
  .brief-summary + .archetype-row { margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--border); }

  /* Archetype */
  .archetype-row { display: flex; align-items: flex-start; gap: 32px; flex-wrap: wrap; }
  .archetype-primary { }
  .archetype-label { font-size: 20px; font-weight: 500; color: var(--accent); letter-spacing: 0.04em; }
  .archetype-confidence { font-size: 11px; color: var(--text-muted); margin-top: 4px; }
  .low-confidence-badge { display: inline-block; margin-left: 8px; font-size: 10px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--warn); background: rgba(255,167,38,0.1); border: 1px solid rgba(255,167,38,0.3); border-radius: 3px; padding: 1px 6px; vertical-align: middle; }
  .archetype-distribution { flex: 1; min-width: 240px; }
  .dist-row { display: flex; align-items: center; gap: 10px; margin-bottom: 7px; }
  .dist-label { font-size: 11px; color: var(--text-muted); width: 130px; flex-shrink: 0; }
  .dist-bar-bg { flex: 1; height: 3px; background: var(--border); border-radius: 2px; overflow: hidden; }
  .dist-bar-fill { height: 100%; background: var(--accent); border-radius: 2px; transition: width 0.4s ease; }
  .dist-bar-fill.dim { background: var(--text-dim); }
  .dist-pct { font-size: 11px; color: var(--text-dim); width: 36px; text-align: right; }

  /* Colour palette */
  .palette-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; }
  @media (max-width: 700px) { .palette-grid { grid-template-columns: repeat(2, 1fr); } }
  .swatch-card { border-radius: var(--radius); overflow: hidden; border: 1px solid var(--border); }
  .swatch-block { height: 80px; width: 100%; }
  .swatch-meta { padding: 10px 12px; background: var(--surface-2); }
  .swatch-role { font-size: 9px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--text-dim); }
  .swatch-name { font-size: 12px; font-weight: 500; color: var(--text); margin-top: 2px; }
  .swatch-hex { font-size: 11px; color: var(--text-muted); font-family: "SF Mono", "Fira Code", monospace; margin-top: 2px; }
  .swatch-hsl { font-size: 10px; color: var(--text-dim); font-family: "SF Mono", "Fira Code", monospace; }

  /* Rationale panels */
  .rationale-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 16px; }
  @media (max-width: 700px) { .rationale-grid { grid-template-columns: 1fr; } }
  .rationale-panel { background: var(--surface-2); border-radius: var(--radius); padding: 14px 16px; border-left: 2px solid var(--accent-dim); }
  .rationale-label { font-size: 9px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--text-dim); margin-bottom: 6px; }
  .rationale-text { font-size: 12px; color: var(--text-muted); line-height: 1.65; }

  /* Full-width rationale */
  .rationale-full { background: var(--surface-2); border-radius: var(--radius); padding: 14px 16px; border-left: 2px solid var(--accent-dim); margin-top: 16px; }

  /* Typography */
  .type-pair { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  @media (max-width: 640px) { .type-pair { grid-template-columns: 1fr; } }
  .type-block { }
  .type-role { font-size: 9px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--text-dim); margin-bottom: 8px; }
  .type-preview-display { font-size: 32px; line-height: 1.2; color: var(--text); margin-bottom: 6px; }
  .type-preview-body { font-size: 15px; line-height: 1.6; color: var(--text); margin-bottom: 6px; }
  .type-meta { display: flex; gap: 12px; flex-wrap: wrap; }
  .type-tag { font-size: 10px; background: var(--surface-2); border: 1px solid var(--border); border-radius: 3px; padding: 2px 8px; color: var(--text-muted); font-family: "SF Mono", "Fira Code", monospace; }
  .pairing-rationale { margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--border); }
  .pairing-rationale-label { font-size: 9px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--text-dim); margin-bottom: 8px; }
  .pairing-rationale-text { font-size: 13px; color: var(--text-muted); line-height: 1.7; }

  /* Spacing scale */
  .scale-visual { display: flex; align-items: flex-end; gap: 6px; margin-bottom: 16px; padding: 20px; background: var(--surface-2); border-radius: var(--radius); }
  .scale-step { display: flex; flex-direction: column; align-items: center; gap: 6px; }
  .scale-bar { background: var(--accent); border-radius: 2px; width: 20px; opacity: 0.8; }
  .scale-value { font-size: 9px; color: var(--text-dim); font-family: "SF Mono", "Fira Code", monospace; }
  .scale-meta { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 14px; }
  .scale-meta-item { font-size: 11px; color: var(--text-muted); }
  .scale-meta-item strong { color: var(--text); }

  /* Layout rhythm */
  .rhythm-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }
  @media (max-width: 600px) { .rhythm-grid { grid-template-columns: 1fr; } }
  .rhythm-item { background: var(--surface-2); border-radius: var(--radius); padding: 14px 16px; }
  .rhythm-item-label { font-size: 9px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--text-dim); margin-bottom: 6px; }
  .rhythm-item-value { font-size: 13px; color: var(--text); font-weight: 500; }
  .density-comfortable { color: #81c784; }
  .density-tight { color: #64b5f6; }
  .density-airy { color: #ce93d8; }

  /* Validation */
  .validation-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
  @media (max-width: 700px) { .validation-grid { grid-template-columns: 1fr; } }
  .validation-group { }
  .validation-group-title { font-size: 9px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--text-dim); margin-bottom: 10px; }
  .validation-check { display: flex; align-items: center; gap: 8px; margin-bottom: 7px; }
  .check-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
  .check-dot.pass { background: var(--pass); }
  .check-dot.fail { background: var(--fail); }
  .check-dot.warn { background: var(--warn); }
  .check-label { font-size: 12px; color: var(--text-muted); }
  .check-value { font-size: 11px; color: var(--text-dim); margin-left: auto; font-family: "SF Mono", "Fira Code", monospace; }
  .correction-note { margin-top: 16px; padding: 10px 14px; background: rgba(200,169,126,0.08); border: 1px solid rgba(200,169,126,0.2); border-radius: var(--radius); font-size: 11px; color: var(--accent); }

  /* Contrast pairs */
  .contrast-table { width: 100%; margin-top: 16px; border-collapse: collapse; }
  .contrast-table th { font-size: 9px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-dim); padding: 0 0 8px; text-align: left; border-bottom: 1px solid var(--border); }
  .contrast-table td { font-size: 11px; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.04); color: var(--text-muted); vertical-align: middle; }
  .contrast-table td:last-child, .contrast-table th:last-child { text-align: right; }
  .badge { display: inline-block; font-size: 9px; letter-spacing: 0.08em; text-transform: uppercase; border-radius: 3px; padding: 1px 6px; margin-left: 4px; }
  .badge.pass { background: rgba(76,175,80,0.15); color: var(--pass); }
  .badge.fail { background: rgba(239,83,80,0.12); color: var(--fail); }

  /* Timestamp */
  .timestamp { margin-top: 32px; text-align: center; font-size: 10px; color: var(--text-dim); letter-spacing: 0.08em; }
`;

// ── Small components ──────────────────────────────────────────────────────────

function PassDot({ pass, warn = false }) {
  const cls = warn ? "warn" : pass ? "pass" : "fail";
  return <span className={`check-dot ${cls}`} />;
}

function Badge({ pass }) {
  return <span className={`badge ${pass ? "pass" : "fail"}`}>{pass ? "Pass" : "Fail"}</span>;
}

function RationalePanel({ label, text }) {
  return (
    <div className="rationale-panel">
      {label && <div className="rationale-label">{label}</div>}
      <div className="rationale-text">{text}</div>
    </div>
  );
}

// ── Section: Brief summary + archetype ────────────────────────────────────────

function ArchetypeSection({ data }) {
  const { brief_summary, design_archetype } = data;
  const isPrimary = (label) => label === design_archetype.primary;

  return (
    <div className="card">
      <div className="card-title">Brief Interpretation</div>
      <p className="brief-summary">{brief_summary}</p>

      <div className="archetype-row brief-summary">
        <div className="archetype-primary">
          <div className="archetype-label">
            {design_archetype.primary}
            {design_archetype.low_confidence && (
              <span className="low-confidence-badge">Low Confidence</span>
            )}
          </div>
          <div className="archetype-confidence">
            {(design_archetype.confidence * 100).toFixed(0)}% classifier confidence
          </div>
        </div>
        <div className="archetype-distribution">
          {Object.entries(design_archetype.distribution).map(([label, prob]) => (
            <div key={label} className="dist-row">
              <span className="dist-label">{label}</span>
              <div className="dist-bar-bg">
                <div
                  className={`dist-bar-fill ${isPrimary(label) ? "" : "dim"}`}
                  style={{ width: `${(prob * 100).toFixed(1)}%` }}
                />
              </div>
              <span className="dist-pct">{(prob * 100).toFixed(0)}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Section: Colour palette ───────────────────────────────────────────────────

function ColourSection({ palette }) {
  return (
    <div className="card">
      <div className="card-title">Colour Palette</div>
      <div className="palette-grid">
        {palette.map((colour) => (
          <div key={colour.role} className="swatch-card">
            <div className="swatch-block" style={{ background: colour.hex }} />
            <div className="swatch-meta">
              <div className="swatch-role">{colour.role}</div>
              <div className="swatch-name">{colour.name}</div>
              <div className="swatch-hex">{colour.hex}</div>
              <div className="swatch-hsl">hsl({colour.hsl})</div>
            </div>
          </div>
        ))}
      </div>
      <div className="rationale-grid">
        {palette.map((colour) => (
          <RationalePanel key={colour.role} label={`${colour.name} — ${colour.role}`} text={colour.rationale} />
        ))}
      </div>
    </div>
  );
}

// ── Section: Typography ───────────────────────────────────────────────────────

function TypographySection({ typography }) {
  const { display, body, pairing_rationale } = typography;

  useEffect(() => {
    loadGoogleFont(display.family);
    loadGoogleFont(body.family);
  }, [display.family, body.family]);

  return (
    <div className="card">
      <div className="card-title">Typography</div>
      <div className="type-pair">
        <div className="type-block">
          <div className="type-role">Display — {display.family}</div>
          <div
            className="type-preview-display"
            style={{ fontFamily: `"${display.family}", serif` }}
          >
            Brand Voice
          </div>
          <div className="type-meta">
            <span className="type-tag">{display.weight}</span>
            <span className="type-tag">{display.size_px}px</span>
          </div>
          <div className="rationale-full" style={{ marginTop: 12 }}>
            <div className="rationale-label">Rationale</div>
            <div className="rationale-text">{display.rationale}</div>
          </div>
        </div>

        <div className="type-block">
          <div className="type-role">Body — {body.family}</div>
          <div
            className="type-preview-body"
            style={{
              fontFamily: `"${body.family}", sans-serif`,
              lineHeight: body.line_height,
              fontSize: Math.min(body.size_px, 16),
            }}
          >
            The quick brown fox jumps over the lazy dog. Comfortable reading at intended scale.
          </div>
          <div className="type-meta">
            <span className="type-tag">{body.weight}</span>
            <span className="type-tag">{body.size_px}px</span>
            <span className="type-tag">lh {body.line_height}</span>
            <span className="type-tag">~{body.characters_per_line} CPL</span>
          </div>
          <div className="rationale-full" style={{ marginTop: 12 }}>
            <div className="rationale-label">Rationale</div>
            <div className="rationale-text">{body.rationale}</div>
          </div>
        </div>
      </div>

      <div className="pairing-rationale">
        <div className="pairing-rationale-label">Pairing Rationale</div>
        <p className="pairing-rationale-text">{pairing_rationale}</p>
      </div>
    </div>
  );
}

// ── Section: Spacing ──────────────────────────────────────────────────────────

function SpacingSection({ spacing }) {
  const MAX_BAR = 72;
  const maxVal = Math.max(...spacing.scale);

  return (
    <div className="card">
      <div className="card-title">Spacing Scale</div>
      <div className="scale-meta">
        <span className="scale-meta-item">Base unit <strong>{spacing.base_unit}px</strong></span>
        <span className="scale-meta-item">Ratio <strong>×{spacing.scale_ratio}</strong></span>
        <span className="scale-meta-item">Steps <strong>{spacing.scale.length}</strong></span>
      </div>
      <div className="scale-visual">
        {spacing.scale.map((val, i) => {
          const height = Math.max(4, (val / maxVal) * MAX_BAR);
          return (
            <div key={i} className="scale-step">
              <div className="scale-bar" style={{ height }} />
              <span className="scale-value">{val}</span>
            </div>
          );
        })}
      </div>
      <RationalePanel text={spacing.rationale} />
    </div>
  );
}

// ── Section: Layout rhythm ────────────────────────────────────────────────────

function LayoutRhythmSection({ layout_rhythm }) {
  const densityClass = `density-${layout_rhythm.density}`;
  return (
    <div className="card">
      <div className="card-title">Layout Rhythm</div>
      <div className="rhythm-grid">
        <div className="rhythm-item">
          <div className="rhythm-item-label">Density</div>
          <div className={`rhythm-item-value ${densityClass}`}>{layout_rhythm.density}</div>
        </div>
        <div className="rhythm-item">
          <div className="rhythm-item-label">Margins</div>
          <div className="rhythm-item-value">{layout_rhythm.margin_proportion}</div>
        </div>
        <div className="rhythm-item">
          <div className="rhythm-item-label">Hierarchy Signal</div>
          <div className="rhythm-item-value" style={{ fontSize: 12 }}>{layout_rhythm.hierarchy_signal}</div>
        </div>
      </div>
      <RationalePanel text={layout_rhythm.rationale} />
    </div>
  );
}

// ── Section: Validation ───────────────────────────────────────────────────────

function ValidationSection({ validation }) {
  const { colour, typography, spacing, correction_passes } = validation;

  return (
    <div className="card">
      <div className="card-title">Validation Report</div>
      <div className="validation-grid">
        {/* Colour */}
        <div className="validation-group">
          <div className="validation-group-title">Colour</div>
          <div className="validation-check">
            <PassDot pass={colour.wcag_aa_pass} />
            <span className="check-label">WCAG AA</span>
          </div>
          <div className="validation-check">
            <PassDot pass={colour.wcag_aaa_flag} warn={!colour.wcag_aaa_flag} />
            <span className="check-label">WCAG AAA flag</span>
          </div>
          <div className="validation-check">
            <PassDot pass={colour.harmony_score >= 0.7} />
            <span className="check-label">Harmony</span>
            <span className="check-value">{colour.harmony_score.toFixed(2)}</span>
          </div>
        </div>

        {/* Typography */}
        <div className="validation-group">
          <div className="validation-group-title">Typography</div>
          <div className="validation-check">
            <PassDot pass={typography.min_body_size_pass} />
            <span className="check-label">Min body size</span>
          </div>
          <div className="validation-check">
            <PassDot pass={typography.line_height_pass} />
            <span className="check-label">Line height</span>
          </div>
          <div className="validation-check">
            <PassDot pass={typography.reading_measure_pass} />
            <span className="check-label">Reading measure</span>
          </div>
          <div className="validation-check">
            <PassDot pass={typography.heading_contrast_pass} />
            <span className="check-label">Heading contrast</span>
          </div>
        </div>

        {/* Spacing */}
        <div className="validation-group">
          <div className="validation-group-title">Spacing</div>
          <div className="validation-check">
            <PassDot pass={spacing.scale_coherent} />
            <span className="check-label">Scale coherence</span>
          </div>
          <div className="validation-check">
            <PassDot pass={spacing.type_to_space_ratio_pass} />
            <span className="check-label">Type-to-space ratio</span>
          </div>
          <div className="validation-check">
            <PassDot pass={spacing.density_consistent} />
            <span className="check-label">Density consistency</span>
          </div>
        </div>
      </div>

      {/* Contrast pairs table */}
      {colour.contrast_pairs && colour.contrast_pairs.length > 0 && (
        <table className="contrast-table">
          <thead>
            <tr>
              <th>Pair</th>
              <th>Ratio</th>
              <th>AA / AAA</th>
            </tr>
          </thead>
          <tbody>
            {colour.contrast_pairs.map((pair) => (
              <tr key={pair.pair}>
                <td>{pair.pair}</td>
                <td style={{ fontFamily: "monospace" }}>{pair.ratio}:1</td>
                <td>
                  <Badge pass={pair.aa} />
                  <Badge pass={pair.aaa} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {correction_passes > 0 && (
        <div className="correction-note">
          ↺ This output required {correction_passes} correction pass{correction_passes > 1 ? "es" : ""}.
          Rationale fields note what was revised and why.
        </div>
      )}
    </div>
  );
}

// ── Pipeline steps for loading UI ─────────────────────────────────────────────

const PIPELINE_STEPS = [
  "Vectorising brief…",
  "Classifying design archetype…",
  "Calling Claude with structured tool use…",
  "Generating colour palette…",
  "Proposing typography pairing…",
  "Building spacing scale…",
  "Running WCAG validation…",
  "Finalising output…",
];

function usePipelineProgress(active) {
  const [step, setStep] = useState(0);
  const timer = useRef(null);

  useEffect(() => {
    if (!active) {
      setStep(0);
      if (timer.current) clearInterval(timer.current);
      return;
    }
    timer.current = setInterval(() => {
      setStep((s) => Math.min(s + 1, PIPELINE_STEPS.length - 1));
    }, 1800);
    return () => clearInterval(timer.current);
  }, [active]);

  return step;
}

// ── Main App ──────────────────────────────────────────────────────────────────

const EXAMPLE_BRIEF =
  "We run a small-batch coffee roastery in St. John's. Our customers are locals who take coffee seriously but hate pretension. We want to feel craft and warm but not rustic or folksy. Think considered, not precious.";

export default function App() {
  const [brief, setBrief] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const pipelineStep = usePipelineProgress(loading);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!brief.trim() || brief.trim().length < 20) return;

    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ brief: brief.trim() }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Request failed: ${res.status}`);
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  function handleExample() {
    setBrief(EXAMPLE_BRIEF);
  }

  return (
    <>
      <style>{css}</style>
      <div className="app">
        <header className="header">
          <h1>Atelier</h1>
          <p>Brand design foundation generator — R&D Creative Agency</p>
        </header>

        <form onSubmit={handleSubmit} className="form-section">
          <label className="form-label" htmlFor="brief">
            Client Brief
          </label>
          <textarea
            id="brief"
            value={brief}
            onChange={(e) => setBrief(e.target.value)}
            placeholder="Describe the brand: what it does, who it's for, the tone it should convey, any reference points or constraints…"
            disabled={loading}
          />
          <div className="submit-row">
            <button
              type="submit"
              className="generate"
              disabled={loading || brief.trim().length < 20}
            >
              {loading ? "Generating…" : "Generate"}
            </button>
            {!brief && (
              <button
                type="button"
                onClick={handleExample}
                style={{ background: "none", border: "1px solid var(--border)", color: "var(--text-muted)", borderRadius: "var(--radius)", padding: "10px 16px", cursor: "pointer", fontSize: 12, letterSpacing: "0.06em" }}
              >
                Use example brief
              </button>
            )}
            <span className="char-count">{brief.length} chars</span>
          </div>
        </form>

        {error && <div className="error">{error}</div>}

        {loading && (
          <div className="loading">
            <div className="spinner" />
            <div className="loading-label">Running pipeline</div>
            <div className="pipeline-steps">
              {PIPELINE_STEPS.map((s, i) => (
                <div key={s} className={`pipeline-step ${i === pipelineStep ? "active" : ""}`}>
                  {i < pipelineStep ? "✓ " : i === pipelineStep ? "→ " : "  "}
                  {s}
                </div>
              ))}
            </div>
          </div>
        )}

        {result && !loading && (
          <>
            <ArchetypeSection data={result} />
            <ColourSection palette={result.colour_palette} />
            <TypographySection typography={result.typography} />
            <SpacingSection spacing={result.spacing} />
            <LayoutRhythmSection layout_rhythm={result.layout_rhythm} />
            <ValidationSection validation={result.validation} />
            <div className="timestamp">
              Generated {new Date(result.generated_at).toLocaleString()}
            </div>
          </>
        )}
      </div>
    </>
  );
}
