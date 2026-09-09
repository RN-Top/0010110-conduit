# Conduit — 0010110

**A two-person ritual app built around the sequence 0010110 (value 22).**

One person casts a working. The other receives it in a shared pool. The sequence is the bridge. The app is the conduit.

## What it is

Conduit is a ritual framework for structured intent between two people. Two people align on the same seven-bit sequence, each carrying an intention across a shared pool. The app seals the exchange with a cryptographic hash so both sides can verify it happened.

The sequence carries the intention. The seal verifies the exchange. The bridge is the alignment.

## How it works

1. Open **Cast**. Enter your name or sigil.
2. Write your intention — what you send across the bridge.
3. Leave the seven bits on `0010110`, or flip them if that is the working.
4. Tap **Iterate +1** for each pass of structured intent.
5. Tap **Seal & send**. You receive a short SHA-256 hash. That is the seal.
6. The other person opens **Receive** and taps **Refresh pool**.
7. **Grimoire** keeps only the workings under your name.

## The sequence

`0010110` — seven bits, decimal value 22. Each bit maps to a stage of the working:

| Bit | Name | Stage |
|---|---|---|
| 0 | Breath | the body settles |
| 0 | Attention | the mind narrows |
| 1 | Image | a picture rises |
| 0 | Word | a name is spoken |
| 1 | Other | the second mind opens |
| 1 | Record | the moment is sealed |
| 0 | Release | the working is sent |

## Architecture

- **Cast** — the sender's side. Intention, bit alignment, iteration, seal.
- **Receive** — the receiver's side. Live pool of sealed workings.
- **Grimoire** — personal archive. Only your workings, filtered by sigil.

## Modes

- **Local** — zero setup. Workings stored in a local JSON file. Single-user mode.
- **Live** — add Supabase credentials. Workings sync to a shared pool. Two-person bridge active.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

For the live two-person bridge, set `SUPABASE_URL` and `SUPABASE_KEY` in the environment or in Streamlit secrets.

## Live

https://0010110-conduit-mxgj7mjdwstodweeeq2hth.streamlit.app/
