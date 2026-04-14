"""
Labelled training dataset: brand briefs mapped to design archetypes.

Each entry is (brief_text, archetype_label). The briefs are short,
freeform descriptions representative of real client inputs. Labels map
to the six archetypes defined in CONTEXT.md.

pandas loads this at runtime to feed the scikit-learn pipeline.
"""

import pandas as pd

ARCHETYPES = [
    "editorial",
    "warm-minimal",
    "bold-expressive",
    "corporate-clean",
    "luxury-refined",
    "playful-energetic",
]

RAW_DATA = [
    # ── editorial ────────────────────────────────────────────────────────────
    (
        "A fashion magazine for architecture and design enthusiasts. "
        "Black, white, and one accent colour at most. No decoration — "
        "just typography and tension. Think Wallpaper* meets Apartamento.",
        "editorial",
    ),
    (
        "A literary journal publishing emerging writers. Serious, "
        "considered, typographically precise. Long-form. Dense. "
        "The writing is the design.",
        "editorial",
    ),
    (
        "Art book publisher specialising in photography monographs. "
        "Restrained, intellectual, white space as a design element. "
        "Serif headings, generous margins, no ornamentation.",
        "editorial",
    ),
    (
        "Online publication covering contemporary art criticism. "
        "Dense editorial layout, long line lengths, high-contrast "
        "black and white palette with a single editorial accent.",
        "editorial",
    ),
    (
        "An independent design studio portfolio. White background, "
        "typography as structure, work speaks for itself. Zero decoration. "
        "Case studies, not carousels.",
        "editorial",
    ),
    (
        "A fashion label targeting design-literate consumers. "
        "High contrast. Restrained palette — black, off-white, one "
        "seasonal accent. Type leads. Images support.",
        "editorial",
    ),
    (
        "Cultural institution gallery. Museum-quality digital presence. "
        "Tight grid, sophisticated hierarchy, neutral tones, serif-forward. "
        "Content is the visual.",
        "editorial",
    ),
    (
        "Academic research institute publishing long-form papers. "
        "No colour beyond black and paper white. Dense type, footnotes, "
        "systematic hierarchy. Rigorous.",
        "editorial",
    ),

    # ── warm-minimal ─────────────────────────────────────────────────────────
    (
        "Small-batch coffee roastery in St. John's. Craft, warm, "
        "considered. Not rustic or folksy. Locals who take coffee seriously "
        "but hate pretension.",
        "warm-minimal",
    ),
    (
        "Wellness retreat in Vermont. Calm, organic, approachable. "
        "Natural materials, earthy palette, generous whitespace. "
        "Feels like linen and morning light.",
        "warm-minimal",
    ),
    (
        "Independent ceramics studio. Handmade goods, warm earth tones, "
        "gentle minimalism. Approachable craft, not precious. "
        "Local, tactile, quiet.",
        "warm-minimal",
    ),
    (
        "Organic skincare brand for women 30–50. Natural, transparent "
        "ingredients, no synthetics. Soft, warm, clean. "
        "Feels honest, not clinical.",
        "warm-minimal",
    ),
    (
        "Boutique yoga studio. Serene, warm, community-focused. "
        "Not a gym, not a luxury spa — somewhere in between. "
        "Accessible but considered.",
        "warm-minimal",
    ),
    (
        "Home goods brand for considered living. Warm, soft, understated. "
        "Natural fibres, honest materials, slow living. "
        "Think Kinfolk but with a smaller ego.",
        "warm-minimal",
    ),
    (
        "Farmer's market collective brand. Fresh, honest, locally sourced. "
        "Warm palette, approachable type, generous breathing room. "
        "Earthy but not rustic.",
        "warm-minimal",
    ),
    (
        "A slow travel journal and agency. Quiet adventure, considered "
        "experiences, off the beaten path. Warm, unhurried, "
        "rich in texture and place.",
        "warm-minimal",
    ),

    # ── bold-expressive ───────────────────────────────────────────────────────
    (
        "Streetwear brand targeting Gen Z. High energy, bold graphics, "
        "loud saturated colour. Urban, unapologetic, loud. "
        "Seen from fifty metres.",
        "bold-expressive",
    ),
    (
        "Music festival brand. Vibrant, maximalist, electric. "
        "Neon and black. Designed to be felt before it's read. "
        "Hierarchy through scale, not subtlety.",
        "bold-expressive",
    ),
    (
        "Sports apparel brand targeting competitive athletes. "
        "Strong, saturated, no compromises. Bold hierarchy, "
        "high spatial contrast, performance aesthetic.",
        "bold-expressive",
    ),
    (
        "Sneaker resale platform. Hype culture, urban energy. "
        "Strong typographic hierarchy, saturated accent colours, "
        "bold display type. The drop is the moment.",
        "bold-expressive",
    ),
    (
        "Energy drink brand for extreme sports. Loud, intense, "
        "high chroma. Feels dangerous in a good way. "
        "Display type heavy, dense layout at hero level.",
        "bold-expressive",
    ),
    (
        "Record label for electronic and club music. Bold, neon, "
        "unapologetic. High visual contrast. Type as texture. "
        "Black backgrounds, saturated primaries.",
        "bold-expressive",
    ),
    (
        "A skateboarding brand rooted in 90s culture. Loud graphics, "
        "irreverent tone, bold colour combinations. "
        "High energy layout, irregular rhythm.",
        "bold-expressive",
    ),

    # ── corporate-clean ───────────────────────────────────────────────────────
    (
        "B2B SaaS platform for enterprise HR and people teams. "
        "Professional, trustworthy, structured. Fortune 500 clients. "
        "Reliability over personality.",
        "corporate-clean",
    ),
    (
        "Financial advisory firm serving high-net-worth individuals. "
        "Conservative, credible, clean grid. Client trust is "
        "the entire brand. No risk, no flair.",
        "corporate-clean",
    ),
    (
        "Healthcare technology company selling to hospital systems. "
        "Clinical, clear, reliable. Regulated environment. "
        "Neutral palette, structured hierarchy, consistent density.",
        "corporate-clean",
    ),
    (
        "Management consulting firm serving Fortune 500 clients. "
        "Professional, authoritative, structured. Neutral tones, "
        "predictable grid, clean system.",
        "corporate-clean",
    ),
    (
        "Insurance company targeting small and medium businesses. "
        "Trustworthy, stable, approachable professionalism. "
        "No personality, just competence.",
        "corporate-clean",
    ),
    (
        "Cloud infrastructure and DevOps platform. Technical, reliable, "
        "enterprise-grade. Neutral palette, structured layout, "
        "clear hierarchy, consistent density.",
        "corporate-clean",
    ),
    (
        "Legal services firm for corporate clients. Authoritative, "
        "structured, credible. Navy or grey palette, serif or neutral "
        "sans-serif, tight predictable grid.",
        "corporate-clean",
    ),

    # ── luxury-refined ────────────────────────────────────────────────────────
    (
        "High-end Swiss watch brand. Precise, understated, timeless. "
        "Heritage craftsmanship. Muted tones, serif typography, "
        "generous margins, slow pacing.",
        "luxury-refined",
    ),
    (
        "Bespoke tailoring house on Savile Row. Impeccable, restrained, "
        "generational. No trends. Serif-led, precise spacing, "
        "quiet confidence.",
        "luxury-refined",
    ),
    (
        "Fine dining restaurant with Michelin ambitions. Refined, "
        "quiet elegance. Muted palette, precise typography, "
        "airy layout, unhurried rhythm.",
        "luxury-refined",
    ),
    (
        "Luxury real estate agency for ultra-premium properties. "
        "Premium, sophisticated, white-glove. Muted tones, "
        "serif display, restrained detail, generous whitespace.",
        "luxury-refined",
    ),
    (
        "Private members club with heritage. Exclusive, understated "
        "wealth, generational quality. Dark muted tones, serif type, "
        "slow layout rhythm, impeccable spacing.",
        "luxury-refined",
    ),
    (
        "Prestige skincare brand targeting affluent women. "
        "Scientific rigour meets luxury positioning. Muted, "
        "precise, elegant. Gold or champagne accent, serif type.",
        "luxury-refined",
    ),
    (
        "Auction house for fine art and antiques. Heritage, gravitas, "
        "understated authority. Restrained muted palette, "
        "editorial serif typography, airy layout.",
        "luxury-refined",
    ),

    # ── playful-energetic ─────────────────────────────────────────────────────
    (
        "Children's educational app for ages 6–12. Fun, approachable, "
        "friendly. High chroma colours, rounded type, short reading "
        "measures, irregular energetic rhythm.",
        "playful-energetic",
    ),
    (
        "Fast-casual food brand targeting millennials. Playful, colourful, "
        "irreverent. Not taking itself seriously. Friendly type, "
        "bright palette, dense cheerful layout.",
        "playful-energetic",
    ),
    (
        "Youth community sports league. Energetic, inclusive, bright. "
        "High chroma, accessible, friendly. Feels like summer "
        "and team spirit.",
        "playful-energetic",
    ),
    (
        "Ice cream brand for families. Bright, joyful, fun. "
        "High chroma palette, rounded friendly type, lots of energy. "
        "Should make you smile before you read a word.",
        "playful-energetic",
    ),
    (
        "Casual gaming platform for non-hardcore players. "
        "Fun, accessible, bright colours. Friendly type, "
        "high energy layout, variable density. Feels like play.",
        "playful-energetic",
    ),
    (
        "Summer family festival brand. Happy, colourful, community. "
        "Lots of energy, playful type combinations, high chroma. "
        "Feels like confetti and sunshine.",
        "playful-energetic",
    ),
    (
        "Toy brand for kids under 10. Bright primary colours, "
        "rounded display type, irregular playful layout. "
        "Maximum energy, zero restraint.",
        "playful-energetic",
    ),
]


def load_dataframe() -> pd.DataFrame:
    """Return the training data as a pandas DataFrame."""
    return pd.DataFrame(RAW_DATA, columns=["brief", "archetype"])
