"""Conduit — 0010110
Streamlit ritual app. One person casts a working. Another receives it.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

SEQUENCE = "0010110"
VALUE = int(SEQUENCE, 2)  # 22
DEFAULT_BITS = [0, 0, 1, 0, 1, 1, 0]

BIT_LABELS = [
    ("Breath", "the body settles"),
    ("Attention", "the mind narrows"),
    ("Image", "a picture rises"),
    ("Word", "a name is spoken"),
    ("Other", "the second mind opens"),
    ("Record", "the moment is sealed"),
    ("Release", "the working is sent"),
]

ROOT = Path(__file__).resolve().parent
ARCHIVE_PATH = ROOT / "data" / "archive.json"
ARCHIVE_PATH.parent.mkdir(parents=True, exist_ok=True)


def supabase_client():
    try:
        from supabase import create_client
    except Exception:
        return None
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    try:
        if not url or not key:
            url = st.secrets.get("SUPABASE_URL", "")
            key = st.secrets.get("SUPABASE_KEY", "")
    except Exception:
        pass
    if url and key:
        try:
            return create_client(url, key)
        except Exception:
            return None
    return None


SB = supabase_client()


def load_local():
    if ARCHIVE_PATH.exists():
        try:
            data = json.loads(ARCHIVE_PATH.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []
    return []


def save_local(rows):
    ARCHIVE_PATH.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def load_pool():
    if SB is not None:
        try:
            res = SB.table("workings").select("*").order("created_at").execute()
            return res.data or []
        except Exception:
            return load_local()
    return load_local()


def push_working(rec):
    if SB is not None:
        try:
            SB.table("workings").insert(rec).execute()
            return
        except Exception:
            pass
    rows = load_local()
    rows.append(rec)
    save_local(rows)


def make_hash(rec):
    payload = json.dumps(
        {
            "caster": rec.get("caster"),
            "intention": rec.get("intention"),
            "bits": rec.get("bits"),
            "value": rec.get("value"),
            "iterations": rec.get("iterations"),
            "created_at": rec.get("created_at"),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def bits_to_code(bits):
    return "".join(str(int(b)) for b in bits)


st.set_page_config(
    page_title="Conduit — 0010110",
    page_icon="◈",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      .block-container { padding-top: 1.1rem; max-width: 820px; }
      .sigil {
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: clamp(2.2rem, 8vw, 3.6rem);
        letter-spacing: 0.28em;
        text-align: center;
        color: #e8c878;
        text-shadow: 0 0 18px rgba(184,134,11,0.45);
        margin: 0.2rem 0 0.15rem;
      }
      .sub {
        text-align: center;
        color: #9a8b6a;
        font-size: 0.92rem;
        margin-bottom: 0.8rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

if "caster" not in st.session_state:
    st.session_state.caster = "adept"
if "iters" not in st.session_state:
    st.session_state.iters = 0

st.markdown(f'<div class="sigil">{SEQUENCE}</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="sub">the sequence · value {VALUE} · a bridge between two minds</div>',
    unsafe_allow_html=True,
)
st.caption("live pool connected" if SB is not None else "local Streamlit mode")

tab_cast, tab_receive, tab_grimoire = st.tabs(["Cast", "Receive", "Grimoire"])

with tab_cast:
    st.subheader("Cast a working")
    st.session_state.caster = st.text_input(
        "Your name / sigil",
        value=st.session_state.caster,
    )
    intention = st.text_area(
        "Intention — what do you send across the bridge?",
        height=100,
        placeholder="Speak it plainly. The sequence carries it.",
    )

    st.markdown("**Align the seven bits**")
    cols = st.columns(7)
    state = []
    for i, col in enumerate(cols):
        with col:
            on = st.toggle(
                BIT_LABELS[i][0],
                value=bool(DEFAULT_BITS[i]),
                key=f"bit_{i}",
                help=BIT_LABELS[i][1],
            )
            state.append(1 if on else 0)
            st.caption(BIT_LABELS[i][1])

    code = bits_to_code(state)
    cur = int(code, 2)
    left, right = st.columns(2)
    left.metric("code", code)
    right.metric("value", cur)

    c1, c2 = st.columns(2)
    if c1.button("Iterate +1", use_container_width=True):
        st.session_state.iters += 1
        st.rerun()
    c2.metric("iterations", st.session_state.iters)

    if st.button("Seal & send", type="primary", use_container_width=True):
        if not (intention or "").strip():
            st.warning("Speak an intention before you seal it.")
        else:
            rec = {
                "caster": (st.session_state.caster or "unknown").strip(),
                "intention": intention.strip(),
                "bits": state,
                "code": code,
                "value": cur,
                "iterations": int(st.session_state.iters),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            rec["hash"] = make_hash(rec)
            push_working(rec)
            st.session_state.iters = 0
            st.success(f"Sealed — `{rec['hash']}`")
            st.balloons()

with tab_receive:
    st.subheader("The shared pool")
    st.caption("Workings sealed by anyone on this conduit appear here.")
    if st.button("Refresh pool"):
        st.rerun()
    pool = load_pool()
    if not pool:
        st.info("The pool is empty. Cast the first working.")
    else:
        for w in reversed(pool):
            bits = w.get("bits", [])
            shown = w.get("code") or bits_to_code(bits) if bits else "?"
            with st.container(border=True):
                st.markdown(f"**{w.get('caster', '?')}** · `{w.get('hash', '')}`")
                st.write(w.get("intention", ""))
                st.code(f"{shown}  =  {w.get('value', '?')}")
                st.caption(
                    f"{w.get('iterations', 0)} iterations · {w.get('created_at', '')}"
                )
        st.download_button(
            "Download the pool (JSON)",
            data=json.dumps(pool, indent=2),
            file_name="conduit_pool.json",
            mime="application/json",
            use_container_width=True,
        )

with tab_grimoire:
    st.subheader("Your grimoire")
    name = (st.session_state.caster or "").strip()
    mine = [w for w in load_pool() if w.get("caster") == name and name]
    if not mine:
        st.info("No workings under your name yet. Cast one in the Cast tab.")
    else:
        for w in reversed(mine):
            st.markdown(
                f"- `{w.get('hash', '')}` — {str(w.get('intention', ''))[:80]}"
            )
    st.download_button(
        "Download my grimoire (JSON)",
        data=json.dumps(mine, indent=2),
        file_name="grimoire.json",
        mime="application/json",
        use_container_width=True,
    )