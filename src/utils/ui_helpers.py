"""
ReelSense - UI Rendering Utilities
Ensures pristine HTML rendering without CommonMark/React-Markdown code block escaping bugs.
"""

import streamlit as st


def render_html(html_str: str) -> None:
    """
    Renders pure HTML without Markdown code-block escaping or indentation issues.
    Strips all leading/trailing whitespace per line to prevent CommonMark
    from treating 4-space indentations as code blocks, and uses st.html when available.
    """
    if not html_str:
        return
    lines = [line.strip() for line in html_str.splitlines() if line.strip()]
    cleaned = "".join(lines)
    if hasattr(st, "html"):
        st.html(cleaned)
    else:
        st.markdown(cleaned, unsafe_allow_html=True)
