from __future__ import annotations

import os

import httpx
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
HTTP_TIMEOUT = 30.0

st.set_page_config(page_title="NerdFarm — Legal Document AI", page_icon="📑", layout="wide")
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


@st.cache_data(ttl=30)
def fetch_matters() -> list[dict]:
    return httpx.get(f"{BACKEND_URL}/matters", timeout=HTTP_TIMEOUT).json()


tab_draft, tab_edit, tab_evidence = st.tabs(["Draft", "Edit", "Evidence"])

with tab_draft:
    st.subheader("Generate a draft")
    matters = []
    try:
        matters = fetch_matters()
    except httpx.HTTPError as exc:
        st.error(f"Cannot reach backend: {exc}")

    if matters:
        labels = {m["matter_id"]: f"{m['name']} ({'held-out' if m['held_out'] else 'training'})" for m in matters}
        selected = st.selectbox("Matter", options=list(labels), format_func=lambda x: labels[x])
        if st.button("Draft now", type="primary"):
            with st.spinner("Drafting..."):
                resp = httpx.post(f"{BACKEND_URL}/matters/{selected}/draft", timeout=300)
                resp.raise_for_status()
                payload = resp.json()
            st.session_state["last_draft_id"] = payload["draft_id"]
            st.markdown(payload["markdown"])

with tab_edit:
    st.subheader("Submit operator edits")
    draft_id = st.text_input("Draft ID", value=st.session_state.get("last_draft_id", ""))
    matter_id = st.text_input("Matter ID")
    matter_type = st.text_input("Matter type (optional)")
    edited = st.text_area("Edited draft (markdown)", height=400)
    if st.button("Apply edit"):
        if not (draft_id and matter_id and edited):
            st.warning("draft_id, matter_id, and edited markdown are required")
        else:
            resp = httpx.post(
                f"{BACKEND_URL}/drafts/{draft_id}/edit",
                json={
                    "matter_id": matter_id,
                    "matter_type": matter_type or None,
                    "edited_markdown": edited,
                },
                timeout=120,
            )
            if resp.is_error:
                st.error(resp.text)
            else:
                st.success(f"Style memory now at version {resp.json()['version']}")

with tab_evidence:
    st.subheader("Inspect evidence for a bullet")
    draft_id = st.text_input("Draft ID", key="ev_draft", value=st.session_state.get("last_draft_id", ""))
    bullet_id = st.text_input("Bullet ID")
    if st.button("Show sources") and draft_id and bullet_id:
        resp = httpx.get(f"{BACKEND_URL}/evidence/{draft_id}/{bullet_id}", timeout=30)
        if resp.is_error:
            st.error(resp.text)
        else:
            for item in resp.json():
                with st.expander(f"{item['chunk_id']} (pages {item['page_range'][0]}–{item['page_range'][1]})"):
                    st.write(item["text"])
