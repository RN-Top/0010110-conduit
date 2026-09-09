import os
import json
import hashlib
from datetime import datetime
from pathlib import Path

import streamlit as st

SEQUENCE = "0010110"
VALUE = int(SEQUENCE, 2)

BIT_LABELS = [
    ("Breath", "the body settles"),
    ("Attention", "the mind narrows"),
    ("Image", "a picture rises"),
    ("Word", "a name is spoken"),
    ("Other", "the second mind opens"),
    ("Record", "the moment is sealed"),
    ("Release", "the working is sent"),
]

ARCHIVE_PATH = Path("data/archive.json")
ARCHIVE_PATH.parent.mkdir(parents=True, exist_ok=True)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
USE_CLOUD = bool(SUPABASE_URL and SUPABASE_KEY)

try:
    from supabase import create_client, Client
    _sb: Client | None = create_client(SUPABASE_URL, SUPABASE_KEY) if USE_CLOUD else None
except Exception:
    _sb = None
    USE_CLOUD = False


def load_local():
    if ARCHIVE_PATH.exists():
        try:
            return json.loads(ARCHIVE_PATH.read_text())
        except Exception:
            return [ ]


def save_local(rows):
    ARCHIVE_PATH.write_text(json.dumps(rows, indent=2))


def load_pool():
    if _sb is not None:
        try:
            res = _sb.table("workings").select("*").order("created_at").execute()
            return res.data or []
        except Exception:
            return load_local()
    return load_local()


def push_working(rec):
    if _sb is not None:
        try:
            _sb.table("workings").insert(rec).execute()
            return
        except Exception:
            pass
    rows = load_local()
    rows.append(rec)
    save_local(rows)


def make_hash(rec):
    payload = json.dumps(
        {k: rec for k in ("caster", "intention", "bits", "value", "iterations", "created_at")},
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:12]


st.set_page_config(page_title="Conduit — 0010110", page_icon=" Ritual", layout="centered")

st.markdown(
    """
    <style>
    .big-seq { font-family: monospace; font-size: 3.4rem; letter-spacing: .35em;
               text-align: center; color: #e8c878; text-shadow: 0 0 18px #b8860b88; }
    .sub { text-align: center; color: #9a8b6a; font-size: .95rem; }
    div.stButton > button { background: linear-gradient(180deg,#3a2a12,#1a1208);
        color:#e8c878; border:1px solid #b8860b; border-radius:10px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(f'<div class="big-seq">{SEQUENCE}</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="sub">the sequence · value {VALUE} · a bridge between two minds</div>',
    unsafe_allow_html=True,
)
st.caption("local mode" if not USE_CLOUD else "live pool connected")

tab_cast, tab_receive, tab_grimoire = st.tabs( )

with tab_cast:
    st.subheader("Cast a working")
    caster = st.text_input("Your name / sigil", value=st.session_state.get("caster", "adept"))
    st.session_state = caster
    intention = st.text_area(
        "Intention — what do you send across the bridge?",
        height=90,
        placeholder="e.g. clarity for the one who receives this",
    )

    st.markdown("**Align the seven bits**")
    cols = st.columns(7)
    state = []
    for i, c in enumerate(cols):
        on = c.toggle(BIT_LABELS [0], value=bool(int(SEQUENCE )), key=f"bit_{i}")
        state.append(1 if on else 0)
        c.caption(BIT_LABELS [1])

    cur = int("".join(map(str, state)), 2)
    st.metric("current value", cur)

    if "iters" not in st.session_state:
        st.session_state = 0
    if st.button("Iterate +1"):
        st.session_state += 1
    st.write(f"iterations this working: **{st.session_state }**")

    if st.button("Seal & send"):
        if not intention.strip():
            st.warning("speak the intention first.")
        else:
            rec = {
                "caster": caster,
                "intention": intention.strip(),
                "bits": state,
                "value": cur,
                "iterations": st.session_state ,
                "created_at": datetime.utcnow().isoformat() + "Z",
            }
            rec = make_hash(rec)
            push_working(rec)
            st.session_state = 0
            st.success(f"sealed — {rec['hash']}")
            st.balloons()

with tab_receive:
    st.subheader("The shared pool")
    st.caption("workings sealed by anyone on this conduit appear here.")
    pool = load_pool()
    if not pool:
        st.info("the pool is empty. cast the first working.")
    else:
        for w in reversed(pool):
            with st.container(border=True):
                st.markdown(f"**{w.get('caster','?')}** · `{w.get('hash','')}`")
                st.write(w.get("intention", ""))
                bits = w.get("bits", [])
                st.code("".join(map(str, bits)) + f"  = {w.get('value','?')}")
                st.caption(f"{w.get('iterations',0)} iterations · {w.get('created_at','')}")
    if st.button("Refresh pool"):
        st.rerun()

with tab_grimoire:
    st.subheader("Your grimoire")
    mine = [w for w in load_pool() if w.get("caster") == st.session_state.get("caster", "")]
    if not mine:
        st.info("no workings under your name yet.")
    else:
        for w in reversed(mine):
            st.markdown(f"- `{w.get('hash','')}` — {w.get('intention','')[:60]}")
    st.download_button(
        "Download my grimoire (JSON)",
        data=json.dumps(mine, indent=2),
        file_name="grimoire.json",
        mime="application/json",
    )