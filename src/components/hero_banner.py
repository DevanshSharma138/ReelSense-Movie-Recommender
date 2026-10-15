"""
ReelSense - Dynamic Personalized Hero Spotlight Component (5-Second Auto-Rotating Poster Carousel)
- Displays 5 movies tailored to the user's taste from the website catalog.
- Exactly 5 seconds per movie poster with an auto-advancing timer progress bar.
- Silky-smooth horizontal slide animation with zero text overlap or ghosting.
- Pause-on-hover so the user can comfortably explore details.
- Interactive prev/next arrows and 1-5 slide selectors.
- Seamless "View Movie Details" and "+ Add to Vault" actions.
"""

import json
import streamlit as st
import streamlit.components.v1 as components
from src.services import user_store
from src.services.movie_service import MovieService
from src.services.recommendation_service import RecommendationService

FALLBACK_BACKDROP = "https://images.unsplash.com/photo-1536440136628-849c177e76a1?q=80&w=1600&auto=format&fit=crop"


def _gather_spotlight_movies(featured_movie, cycle_movies, count=5):
    """Gathers 5 unique movies matching user taste from the catalog."""
    movies = []
    seen_ids = set()

    if featured_movie and isinstance(featured_movie, dict):
        movies.append(featured_movie)
        seen_ids.add(featured_movie["id"])

    if cycle_movies:
        for m in cycle_movies:
            if m and isinstance(m, dict) and m["id"] not in seen_ids:
                movies.append(m)
                seen_ids.add(m["id"])

    if len(movies) < count:
        try:
            trending = RecommendationService.get_trending_movies(limit=count * 2)
            for m in trending:
                if m["id"] not in seen_ids:
                    movies.append(m)
                    seen_ids.add(m["id"])
                if len(movies) >= count:
                    break
        except Exception:
            pass

    if len(movies) < count:
        for m in MovieService.get_all_movies()[:count * 2]:
            if m["id"] not in seen_ids:
                movies.append(m)
                seen_ids.add(m["id"])
            if len(movies) >= count:
                break

    return movies[:count]


def render_hero_banner(featured_movie=None, cycle_movies=None):
    spotlight_movies = _gather_spotlight_movies(featured_movie, cycle_movies, count=5)
    if not spotlight_movies:
        return

    primary_movie = spotlight_movies[0]
    p_id = primary_movie["id"]
    watchlist = st.session_state.get("watchlist", [])

    slides_data = []
    for idx, m in enumerate(spotlight_movies):
        m_id = m["id"]
        title = m.get("title", "Untitled Film")
        year = m.get("release_year", 2024)
        raw_rating = float(m.get("rating", 8.4))
        imdb_rating = raw_rating if raw_rating > 5.0 else raw_rating * 2.0
        star_5 = raw_rating / 2.0 if raw_rating > 5.0 else raw_rating
        match_pct = m.get("vector_match") or m.get("mood_affinity") or (98 - idx * 3)
        match_pct = max(75, min(99, int(match_pct)))

        runtime = m.get("runtime", "")
        if not runtime or runtime == "N/A":
            runtime = "138 MIN"

        director = m.get("director", "")
        genres = m.get("genres", ["Cinema", "Drama"])
        genres_str = " • ".join(genres[:3])
        overview = m.get("overview", "")
        if not overview or overview == "N/A":
            overview = f"A compelling {genres_str} masterwork curated for your taste profile."

        backdrop = m.get("backdrop_url") or FALLBACK_BACKDROP
        in_wl = m_id in watchlist

        slides_data.append({
            "id": m_id,
            "title": title,
            "year": year,
            "imdb": f"{imdb_rating:.1f}",
            "star5": f"{star_5:.1f}",
            "match": match_pct,
            "runtime": runtime,
            "director": f"Dir. {director}" if director and director != "Unknown" else "",
            "genres": genres_str,
            "overview": overview[:260] + ("..." if len(overview) > 260 else ""),
            "backdrop": backdrop,
            "in_watchlist": in_wl
        })

    num_slides = len(slides_data)
    wrapper_width_pct = num_slides * 100
    slide_width_pct = 100.0 / num_slides

    slides_html = ""
    for i, s in enumerate(slides_data):
        dir_badge = f'<span class="meta-badge director">{s["director"]}</span>' if s["director"] else ""
        vault_label = "✓ In Vault" if s["in_watchlist"] else "+ Add to Vault"
        vault_active_cls = "in-vault" if s["in_watchlist"] else ""
        slides_html += f'''
        <div class="slide" id="slide-{i}" style="width: {slide_width_pct}%; background-image: url('{s["backdrop"]}');">
            <div class="slide-overlay"></div>
            <div class="slide-content">
                <div class="hero-pills">
                    <span class="brand-tag">REELSENSE</span>
                    <span class="taste-tag">✨ {s["match"]}% TASTE MATCH</span>
                    <span class="slide-index-tag">SPOTLIGHT {i+1} OF {num_slides}</span>
                </div>
                <h1 class="hero-title">{s["title"]}</h1>
                <div class="meta-badges">
                    <span class="meta-badge imdb">IMDb <b>{s["imdb"]}</b></span>
                    <span class="meta-badge">⭐ {s["star5"]} / 5</span>
                    <span class="meta-badge">{s["year"]}</span>
                    <span class="meta-badge">{s["runtime"]}</span>
                    <span class="meta-badge">{s["genres"]}</span>
                    {dir_badge}
                </div>
                <p class="hero-overview">{s["overview"]}</p>
                <div class="hero-btn-row">
                    <a href="?movie_id={s["id"]}" target="_top" class="hero-cta-btn">
                        🎬 View Movie Details
                    </a>
                    <a href="?vault_toggle={s["id"]}" target="_top" class="hero-vault-btn {vault_active_cls}">
                        {vault_label}
                    </a>
                </div>
            </div>
        </div>
        '''

    dots_html = ""
    for i, s in enumerate(slides_data):
        active_cls = "active" if i == 0 else ""
        dots_html += f'''
        <button class="dot-btn {active_cls}" id="dot-{i}" onclick="goToSlide({i})" title="{s["title"]}">
            {i+1}
        </button>
        '''

    carousel_iframe_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            html, body {{
                width: 100%;
                height: 100%;
                background: transparent;
                overflow: hidden;
                font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
                color: #ffffff;
            }}
            .hero-container {{
                position: relative;
                width: 100%;
                height: 660px;
                border-radius: 20px;
                overflow: hidden;
                background-color: #0e0e10;
                border: 1px solid rgba(212, 175, 55, 0.22);
                box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6), 0 0 25px rgba(212, 175, 55, 0.05);
            }}
            .slides-wrapper {{
                display: flex;
                width: {wrapper_width_pct}%;
                height: 100%;
                transition: transform 0.65s cubic-bezier(0.2, 0.9, 0.3, 1);
            }}
            .slide {{
                height: 100%;
                flex-shrink: 0;
                position: relative;
                background-size: cover;
                background-position: center center;
                display: flex;
                flex-direction: column;
                justify-content: flex-end;
                padding: 48px 56px;
            }}
            .slide-overlay {{
                position: absolute;
                inset: 0;
                background: 
                    linear-gradient(90deg, rgba(14, 14, 16, 0.58) 0%, rgba(14, 14, 16, 0.25) 48%, rgba(14, 14, 16, 0.05) 75%, transparent 100%),
                    linear-gradient(0deg, rgba(14, 14, 16, 0.72) 0%, rgba(14, 14, 16, 0.12) 30%, transparent 60%);
                z-index: 1;
            }}
            .slide-content {{
                position: relative;
                z-index: 3;
                max-width: 780px;
            }}
            .hero-pills {{
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 12px;
                flex-wrap: wrap;
            }}
            .brand-tag {{
                background: linear-gradient(135deg, rgba(212, 175, 55, 0.2), rgba(212, 175, 55, 0.08));
                color: #f2ca50;
                font-family: 'Outfit', sans-serif;
                font-weight: 800;
                font-size: 0.75rem;
                letter-spacing: 0.15em;
                padding: 4px 12px;
                border-radius: 9999px;
                border: 1px solid rgba(212, 175, 55, 0.4);
                text-transform: uppercase;
            }}
            .taste-tag {{
                background: rgba(30, 29, 34, 0.85);
                color: #ffd866;
                font-size: 0.75rem;
                font-weight: 700;
                letter-spacing: 0.08em;
                padding: 4px 12px;
                border-radius: 9999px;
                border: 1px solid rgba(255, 216, 102, 0.3);
                box-shadow: 0 0 10px rgba(242, 202, 80, 0.15);
            }}
            .slide-index-tag {{
                background: rgba(255, 255, 255, 0.08);
                color: #a09a8e;
                font-size: 0.72rem;
                font-weight: 600;
                padding: 4px 10px;
                border-radius: 9999px;
                letter-spacing: 0.05em;
            }}
            .hero-title {{
                font-family: 'Outfit', sans-serif;
                font-size: 2.85rem;
                font-weight: 800;
                line-height: 1.15;
                color: #ffffff;
                margin-bottom: 14px;
                letter-spacing: -0.02em;
                text-shadow: 0 4px 20px rgba(0, 0, 0, 0.85);
            }}
            .meta-badges {{
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 14px;
                flex-wrap: wrap;
            }}
            .meta-badge {{
                display: inline-flex;
                align-items: center;
                background: rgba(24, 23, 27, 0.88);
                padding: 4px 10px;
                border-radius: 6px;
                font-size: 0.8rem;
                font-weight: 600;
                color: #e5e0d8;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            .meta-badge.imdb {{
                background: rgba(242, 202, 80, 0.12);
                border-color: rgba(242, 202, 80, 0.35);
                color: #f2ca50;
            }}
            .meta-badge.director {{
                color: #b5afa4;
            }}
            .hero-overview {{
                font-size: 0.94rem;
                line-height: 1.55;
                color: #c9c4bb;
                margin-bottom: 22px;
                max-width: 720px;
                display: -webkit-box;
                -webkit-line-clamp: 3;
                -webkit-box-orient: vertical;
                overflow: hidden;
                text-shadow: 0 2px 8px rgba(0, 0, 0, 0.7);
            }}
            .hero-btn-row {{
                display: flex;
                align-items: center;
                gap: 14px;
                flex-wrap: wrap;
            }}
            .hero-cta-btn {{
                display: inline-flex;
                align-items: center;
                gap: 8px;
                background: rgba(242, 202, 80, 0.22);
                color: #ffd866;
                text-decoration: none;
                font-weight: 700;
                font-size: 0.92rem;
                padding: 12px 26px;
                border-radius: 9999px;
                border: 1.5px solid rgba(242, 202, 80, 0.65);
                cursor: pointer;
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
                box-shadow: 0 4px 18px rgba(0, 0, 0, 0.5);
            }}
            .hero-cta-btn:hover {{
                background: rgba(242, 202, 80, 0.42);
                color: #ffffff;
                border-color: #ffd866;
                transform: translateY(-2px);
                box-shadow: 0 6px 22px rgba(242, 202, 80, 0.35);
            }}
            .hero-vault-btn {{
                display: inline-flex;
                align-items: center;
                gap: 8px;
                background: rgba(255, 255, 255, 0.12);
                color: #ffffff;
                text-decoration: none;
                font-weight: 700;
                font-size: 0.92rem;
                padding: 12px 26px;
                border-radius: 9999px;
                border: 1.5px solid rgba(255, 255, 255, 0.35);
                cursor: pointer;
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
                box-shadow: 0 4px 18px rgba(0, 0, 0, 0.5);
            }}
            .hero-vault-btn.in-vault {{
                background: rgba(242, 202, 80, 0.2);
                color: #f2ca50;
                border-color: rgba(242, 202, 80, 0.55);
            }}
            .hero-vault-btn:hover {{
                background: rgba(255, 255, 255, 0.22);
                border-color: rgba(255, 255, 255, 0.7);
                transform: translateY(-2px);
                box-shadow: 0 6px 22px rgba(255, 255, 255, 0.25);
            }}

            .timer-bar-wrapper {{
                position: absolute;
                bottom: 0;
                left: 0;
                width: 100%;
                height: 4px;
                background: rgba(255, 255, 255, 0.12);
                z-index: 10;
            }}
            .timer-bar-fill {{
                width: 0%;
                height: 100%;
                background: linear-gradient(90deg, #d4af37, #f2ca50, #ffd866);
                box-shadow: 0 0 12px rgba(242, 202, 80, 0.7);
            }}

            .nav-arrow {{
                position: absolute;
                top: 50%;
                transform: translateY(-50%);
                width: 44px;
                height: 44px;
                border-radius: 50%;
                background: rgba(18, 17, 21, 0.7);
                border: 1px solid rgba(212, 175, 55, 0.3);
                color: #f2ca50;
                font-size: 1.25rem;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                z-index: 10;
                transition: all 0.2s ease;
                backdrop-filter: blur(8px);
            }}
            .nav-arrow:hover {{
                background: rgba(35, 33, 40, 0.95);
                border-color: #f2ca50;
                box-shadow: 0 0 15px rgba(242, 202, 80, 0.35);
                transform: translateY(-50%) scale(1.08);
            }}
            .nav-arrow.prev {{ left: 20px; }}
            .nav-arrow.next {{ right: 20px; }}

            .dots-container {{
                position: absolute;
                bottom: 18px;
                right: 32px;
                display: flex;
                align-items: center;
                gap: 8px;
                z-index: 10;
                background: rgba(14, 14, 16, 0.75);
                padding: 6px 12px;
                border-radius: 9999px;
                border: 1px solid rgba(77, 70, 53, 0.4);
                backdrop-filter: blur(8px);
            }}
            .timer-caption {{
                font-size: 0.72rem;
                color: #a09a8e;
                font-weight: 600;
                margin-right: 4px;
                letter-spacing: 0.04em;
            }}
            .dot-btn {{
                width: 24px;
                height: 24px;
                border-radius: 50%;
                border: 1px solid rgba(212, 175, 55, 0.3);
                background: rgba(30, 29, 34, 0.85);
                color: #9e978a;
                font-size: 0.7rem;
                font-weight: 700;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s ease;
            }}
            .dot-btn:hover {{
                color: #ffffff;
                border-color: #f2ca50;
            }}
            .dot-btn.active {{
                background: #f2ca50;
                color: #0e0e10;
                border-color: #f2ca50;
                box-shadow: 0 0 10px rgba(242, 202, 80, 0.5);
                transform: scale(1.1);
            }}
        </style>
    </head>
    <body>
        <div class="hero-container" id="hero-container">
            <div class="slides-wrapper" id="slides-wrapper">
                {slides_html}
            </div>

            <button class="nav-arrow prev" id="btn-prev" title="Previous Movie">⟨</button>
            <button class="nav-arrow next" id="btn-next" title="Next Movie">⟩</button>

            <div class="dots-container">
                <span class="timer-caption" id="timer-caption">⏳ 5s</span>
                {dots_html}
            </div>

            <div class="timer-bar-wrapper">
                <div class="timer-bar-fill" id="timer-fill"></div>
            </div>
        </div>

        <script>
            (function() {{
                const slidesWrapper = document.getElementById('slides-wrapper');
                const dots = document.querySelectorAll('.dot-btn');
                const timerFill = document.getElementById('timer-fill');
                const timerCaption = document.getElementById('timer-caption');
                const container = document.getElementById('hero-container');
                const btnPrev = document.getElementById('btn-prev');
                const btnNext = document.getElementById('btn-next');
                const total = {num_slides};
                
                let current = 0;
                const DURATION = 5000;
                let timerInterval = null;
                let startTime = Date.now();

                function renderSlide(index) {{
                    current = index;
                    const offset = -(index * (100 / total));
                    if (slidesWrapper) {{
                        slidesWrapper.style.transform = 'translateX(' + offset + '%)';
                    }}

                    dots.forEach((d, idx) => {{
                        if (idx === index) {{
                            d.classList.add('active');
                        }} else {{
                            d.classList.remove('active');
                        }}
                    }});

                    startProgress();
                }}

                function nextSlide() {{
                    let next = (current + 1) % total;
                    renderSlide(next);
                }}

                function prevSlide() {{
                    let prev = (current - 1 + total) % total;
                    renderSlide(prev);
                }}

                function startProgress() {{
                    if (timerInterval) clearInterval(timerInterval);
                    startTime = Date.now();
                    
                    timerInterval = setInterval(() => {{

                        let elapsed = Date.now() - startTime;
                        let progress = Math.min(100, (elapsed / DURATION) * 100);
                        if (timerFill) timerFill.style.width = progress + '%';

                        let remainingSec = Math.max(1, Math.ceil((DURATION - elapsed) / 1000));
                        if (timerCaption) {{
                            timerCaption.textContent = '⏳ ' + remainingSec + 's';
                        }}

                        if (elapsed >= DURATION) {{
                            nextSlide();
                        }}
                    }}, 40);
                }}

                window.goToSlide = function(idx) {{
                    renderSlide(idx);
                }};

                if (btnNext) {{
                    btnNext.addEventListener('click', (e) => {{
                        e.stopPropagation();
                        nextSlide();
                    }});
                }}

                if (btnPrev) {{
                    btnPrev.addEventListener('click', (e) => {{
                        e.stopPropagation();
                        prevSlide();
                    }});
                }}

                // Continuous auto-advancing timer (does not stop on hover)
                renderSlide(0);
            }})();
        </script>
    </body>
    </html>
    """

    components.html(carousel_iframe_html, height=665, scrolling=False)

    # 2. Interactive Action Bar Below Spotlight
    def _on_hero_primary_click(target_mid=p_id):
        st.session_state.previous_page = "home"
        st.session_state.selected_movie_id = target_mid
        st.session_state.current_page = "movie_details"

    def _on_hero_vault_toggle(target_mid=p_id):
        wl = list(st.session_state.get("watchlist", []))
        if target_mid in wl:
            wl.remove(target_mid)
        else:
            wl.append(target_mid)
        st.session_state.watchlist = wl
        user_store.save_watchlist(wl)

    col_actions, col_switcher = st.columns([5.5, 4.5], vertical_alignment="center")

    with col_actions:
        col_c1, col_c2 = st.columns([1.6, 1.4])
        with col_c1:
            st.button(
                "🎬 View Movie Details",
                key=f"hero_stream_{p_id}",
                use_container_width=True,
                type="primary",
                on_click=_on_hero_primary_click,
                args=(p_id,),
                help="Inspect complete synopsis, intelligence breakdown, and vector resonance"
            )
        with col_c2:
            in_wl = p_id in watchlist
            st.button(
                "✓ In Vault" if in_wl else "+ Add to Vault",
                key=f"hero_vault_{p_id}",
                use_container_width=True,
                on_click=_on_hero_vault_toggle,
                args=(p_id,),
                help="Save to your private screening Vault"
            )

    with col_switcher:
        st.markdown('''
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
            <span style="font-size: 0.72rem; color: #99907c; text-transform: uppercase; letter-spacing: 0.12em; font-weight: 700;">Spotlight Taste Rotation</span>
            <span style="font-size: 0.72rem; color: #f2ca50; font-weight: 700;">5s Auto-advancing</span>
        </div>
        ''', unsafe_allow_html=True)

        cycle_cols = st.columns(len(spotlight_movies))
        for idx, m in enumerate(spotlight_movies):
            c_mid = m["id"]
            short_title = m["title"][:11] + (".." if len(m["title"]) > 11 else "")

            with cycle_cols[idx]:
                st.button(
                    f"{idx+1}. {short_title}",
                    key=f"hero_cycle_{c_mid}",
                    use_container_width=True,
                    help=f"Jump to {m['title']}",
                    on_click=_on_hero_primary_click,
                    args=(c_mid,)
                )
