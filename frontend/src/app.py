"""NerdFarm — Streamlit frontend.

The frontend never imports backend modules. It speaks to the FastAPI surface
over HTTP only — preserving the microservice boundary even though both ship
in the same monolith today.
"""

from __future__ import annotations

import os

import httpx
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
HTTP_TIMEOUT = 10.0

st.set_page_config(
    page_title="NerdFarm — Legal Document AI",
    page_icon="📑",
    layout="wide",
)

st.title("NerdFarm")
st.caption("Agentic legal-document AI — ingest, retrieve, draft, learn.")

with st.sidebar:
    st.header("Backend")
    st.code(BACKEND_URL, language="text")
    if st.button("Health check"):
        try:
            r = httpx.get(f"{BACKEND_URL}/health", timeout=HTTP_TIMEOUT)
            st.success(r.json())
        except httpx.HTTPError as exc:
            st.error(f"Unreachable: {exc}")

st.info(
    "Frontend skeleton. Upload, draft viewer, evidence inspector, and inline "
    "edit land in subsequent commits."
)
