"""
ReelSense - Application Configuration & Design System
"""

APP_NAME = "ReelSense"
APP_TAGLINE = "Cinematic Curation & AI Vector Discovery"
APP_DESCRIPTION = "An AI-powered personalized movie discovery and recommendation platform."

# Color Palette Constants (Matches UI Spec)
# Color Palette Constants (Matches UI Spec - Obsidian & Champagne Gold)
COLOR_PALETTE = {
    "bg_main": "#131315",
    "surface_lowest": "#0e0e10",
    "surface_low": "#1c1b1e",
    "surface_container": "#201f22",
    "surface_high": "#2a2a2c",
    "surface_highest": "#353437",
    "surface_bright": "#39393b",
    "primary_gold": "#f2ca50",
    "primary_container": "#d4af37",
    "on_primary_container": "#554300",
    "secondary_gold": "#e7c17c",
    "secondary_container": "#5c4308",
    "tertiary_gold": "#f1c97d",
    "text_surface": "#e5e1e4",
    "text_variant": "#d0c5af",
    "text_outline": "#99907c",
    "outline_variant": "#4d4635"
}

# Navigation Items (Aligned with latest Stitch Spec)
NAV_ITEMS = [
    {"id": "home", "label": "Home / Discover", "icon": "movie"},
    {"id": "discover-movies", "label": "Discover Movies", "icon": "explore"},
    {"id": "mood-explorer", "label": "Mood Explorer", "icon": "tune"},
    {"id": "my-watchlist", "label": "My Watchlist", "icon": "bookmark"},
    {"id": "my-ratings", "label": "My Ratings", "icon": "star"},
    {"id": "about-the-ai", "label": "Sense AI / About the AI", "icon": "psychology"},
    {"id": "my-profile", "label": "My Profile", "icon": "person"}
]

# Centralized Icons Map (Material Symbols Outlined)
ICONS = {
    "app_logo": "movie",
    "home": "movie",
    "discover": "explore",
    "mood": "tune",
    "watchlist": "bookmark",
    "ratings": "star",
    "sense_ai": "psychology",
    "profile": "person",
    "search": "search",
    "filter": "tune",
    "sparkles": "auto_awesome",
    "check": "check",
    "arrow_forward": "arrow_forward",
    "volume": "volume_up",
    "terminal": "terminal",
    "acoustic": "graphic_eq",
    "luminance": "contrast",
    "pacing": "speed",
    "movie_filter": "movie_filter",
    "reset": "restart_alt"
}

# Sensory Spectrum Discovery Moods (Matching latest Stitch Mood Explorer)
MOODS = [
    {
        "id": "Happy",
        "tier": "Harmonic Tier",
        "label": "Happy",
        "icon": "wb_sunny",
        "color_class": "text-primary",
        "count": "2,118 Available",
        "tagline": "Warm euphoria, upbeat vitality, vibrant storytelling, and uplifting human journeys bathed in radiant chromatic warmth.",
        "frequency": "528 Hz",
        "acoustic": "Upbeat Lyrical",
        "luminance": "Vibrant High Key",
        "pacing": "Rhythmic",
        "genres": ["Comedy", "Animation", "Adventure", "Music"],
        "default_rating": 8.0
    },
    {
        "id": "Relaxed",
        "tier": "Atmosphere Tier",
        "label": "Relaxed",
        "icon": "spa",
        "color_class": "text-secondary",
        "count": "1,840 Available",
        "tagline": "Meditative pacing, gentle ambient scores, serene widescreen landscapes, and quiet contemplation with zero sensory exhaustion.",
        "frequency": "432 Hz",
        "acoustic": "Minimalist Neo-Classical",
        "luminance": "Soft Pastel Twilight",
        "pacing": "Meditative",
        "genres": ["Drama", "Poetic", "Slow Cinema", "Documentary"],
        "default_rating": 8.2
    },
    {
        "id": "Thrilling",
        "tier": "Adrenaline Tier",
        "label": "Thrilling",
        "icon": "bolt",
        "color_class": "text-error",
        "count": "2,945 Available",
        "tagline": "Heart-pounding suspense, relentless tension, edge-of-seat rhythmic cuts, visceral stakes, and unpredictable plot accelerations.",
        "frequency": "963 Hz",
        "acoustic": "Synthesizer Dissonance",
        "luminance": "High Contrast Chiaroscuro",
        "pacing": "Frenetic Kinetic",
        "genres": ["Thriller", "Action", "Crime", "Mystery"],
        "default_rating": 8.4
    },
    {
        "id": "Romantic",
        "tier": "Intimacy Tier",
        "label": "Romantic",
        "icon": "favorite",
        "color_class": "text-secondary-fixed",
        "count": "1,310 Available",
        "tagline": "Tender emotional intimacy, golden hour nostalgic lighting, poetic natural dialogue, and deeply lingering human bonds.",
        "frequency": "639 Hz",
        "acoustic": "Warm Acoustic Ensemble",
        "luminance": "Amber Golden Hour",
        "pacing": "Lyrical Flow",
        "genres": ["Romance", "Drama", "Music"],
        "default_rating": 8.1
    },
    {
        "id": "Emotional",
        "tier": "Catharsis Tier",
        "label": "Emotional",
        "icon": "water_drop",
        "color_class": "text-tertiary",
        "count": "1,720 Available",
        "tagline": "Poignant human drama, cathartic release, bittersweet melancholy, and profound character vulnerability that lingers.",
        "frequency": "741 Hz",
        "acoustic": "Melancholic Solo Cello",
        "luminance": "Desaturated Sepia",
        "pacing": "Deep Resonance",
        "genres": ["Drama", "Biography", "History"],
        "default_rating": 8.5
    },
    {
        "id": "Mind-blown",
        "tier": "Cerebral Tier",
        "label": "Mind-blown",
        "icon": "psychology",
        "color_class": "text-primary",
        "count": "1,482 Available",
        "tagline": "Non-linear timelines, philosophical paradoxes, reality-shifting existential labyrinths, and architectural visual trickery.",
        "frequency": "852 Hz",
        "acoustic": "Microtonal Drone",
        "luminance": "Fractured Neon Dark",
        "pacing": "Non-Linear Matrix",
        "genres": ["Surrealism", "Cyberpunk", "Sci-Fi", "Mystery", "Thriller"],
        "default_rating": 8.5
    }
]

DEFAULT_USER = {
    "name": "Film Curator",
    "favorite_genres": ["Drama", "Sci-Fi", "Thriller", "Action"],
    "preferred_language": "English",
    "preferred_era": "2010s & Newer",
    "min_rating_pref": 7.5
}
