"""
ReelSense - Dynamic Image Fallback & SVG Poster Generator (Phase 3)
Provides attractive, standalone local SVG data URI posters & backdrops
using movie title, release year, and genre.
Zero network dependencies; guaranteed never to 404 or fail.
"""
import html
import urllib.parse

# Last resort external placeholder
FALLBACK_UNSPLASH = "https://images.unsplash.com/photo-1485846234645-a62644f84728?q=80&w=600&auto=format&fit=crop"


def generate_fallback_poster(title: str, year: int = None, genre: str = None) -> str:
    """Generate an obsidian & champagne gold 2:3 vertical movie poster SVG as a data URI."""
    safe_title = html.escape(str(title).strip())
    year_str = str(year) if year and str(year) != "0" else ""
    genre_str = html.escape(str(genre).strip()) if genre else "Cinema"
    meta_line = f"{year_str} · {genre_str}" if year_str else genre_str

    # Wrap title cleanly
    words = safe_title.split()
    line1 = safe_title
    line2 = ""
    if len(safe_title) > 20 and len(words) > 1:
        mid = len(words) // 2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 900" width="600" height="900">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#141316"/>
      <stop offset="60%" stop-color="#1f1e23"/>
      <stop offset="100%" stop-color="#2a282f"/>
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="30%" r="50%">
      <stop offset="0%" stop-color="#f2ca50" stop-opacity="0.12"/>
      <stop offset="100%" stop-color="#f2ca50" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="600" height="900" fill="url(#bg)"/>
  <rect width="600" height="900" fill="url(#glow)"/>
  <rect x="20" y="20" width="560" height="860" rx="16" fill="none" stroke="#f2ca50" stroke-opacity="0.3" stroke-width="1.5"/>
  <circle cx="300" cy="270" r="48" fill="#201f24" stroke="#f2ca50" stroke-width="1.2" stroke-opacity="0.5"/>
  <text x="300" y="287" font-size="44" text-anchor="middle">🎬</text>
  <text x="300" y="415" font-family="'Outfit', 'Segoe UI', sans-serif" font-size="30" font-weight="700" fill="#f4ebd9" text-anchor="middle">{line1}</text>
  {f'<text x="300" y="455" font-family="\'Outfit\', \'Segoe UI\', sans-serif" font-size="24" font-weight="600" fill="#d0c5af" text-anchor="middle">{line2}</text>' if line2 else ''}
  <rect x="200" y="515" width="200" height="36" rx="18" fill="#28262c" stroke="#f2ca50" stroke-width="1" stroke-opacity="0.6"/>
  <text x="300" y="538" font-family="'Segoe UI', sans-serif" font-size="14" font-weight="700" fill="#f2ca50" text-anchor="middle">{meta_line}</text>
  <text x="300" y="820" font-family="'Segoe UI', sans-serif" font-size="12" letter-spacing="4" fill="#99907c" text-anchor="middle">REELSENSE VAULT</text>
</svg>"""
    return "data:image/svg+xml;utf8," + urllib.parse.quote(svg)


def generate_fallback_backdrop(title: str, year: int = None, genre: str = None) -> str:
    """Generate a widescreen 16:9 cinematic backdrop SVG as a data URI."""
    safe_title = html.escape(str(title).strip())
    year_str = str(year) if year and str(year) != "0" else ""
    genre_str = html.escape(str(genre).strip()) if genre else "Cinema Masterwork"
    meta_line = f"{year_str} · {genre_str}" if year_str else genre_str

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" width="1600" height="900">
  <defs>
    <linearGradient id="bbg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0e0d10"/>
      <stop offset="50%" stop-color="#18171c"/>
      <stop offset="100%" stop-color="#232128"/>
    </linearGradient>
    <radialGradient id="bglow" cx="25%" cy="50%" r="60%">
      <stop offset="0%" stop-color="#f2ca50" stop-opacity="0.15"/>
      <stop offset="100%" stop-color="#f2ca50" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="1600" height="900" fill="url(#bbg)"/>
  <rect width="1600" height="900" fill="url(#bglow)"/>
  <text x="140" y="420" font-family="'Outfit', 'Segoe UI', sans-serif" font-size="56" font-weight="800" fill="#f4ebd9">{safe_title}</text>
  <rect x="140" y="460" width="240" height="40" rx="20" fill="#28262c" stroke="#f2ca50" stroke-width="1.2" stroke-opacity="0.7"/>
  <text x="260" y="485" font-family="'Segoe UI', sans-serif" font-size="16" font-weight="700" fill="#f2ca50" text-anchor="middle">{meta_line}</text>
  <text x="140" y="800" font-family="'Segoe UI', sans-serif" font-size="14" letter-spacing="5" fill="#99907c">REELSENSE CINEMATIC SPOTLIGHT</text>
</svg>"""
    return "data:image/svg+xml;utf8," + urllib.parse.quote(svg)
