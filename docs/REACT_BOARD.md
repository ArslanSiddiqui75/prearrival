# Optional React board

An alternative front end for the same pipeline. It is **not** the default: `streamlit run app.py` remains the stage board and the one the talk is scripted around. All logic stays in Python (`src/`); `api.py` wraps the same functions the Streamlit board calls, and the React app only displays and calls the API.

## Run

```bash
pip install -r requirements.txt
python -m uvicorn api:app --port 8000
# open http://localhost:8000
```

The built UI is committed in `web/dist`, so the presenting laptop does not need Node. The same `.env` with `GROQ_API_KEY` is used.

To rebuild the UI after editing `web/src` (needs Node 22):

```bash
cd web && npm install && npm run build
```

Dev mode with hot reload: `npm run dev` in `web/` (proxies `/api` and `/fixtures` to port 8000).

## What is the same as the Streamlit board

- Same cloud calls, same `run_live` logic (speech + photo in parallel, then extraction), same NEWS2 rules and priority table.
- Same stage flow and button labels: **Send live**, **Fake fields (layout check)**, **Ambulance tracking (simulated)**, **Inject roadblock (closed)**, **Inject heavy traffic (slow)**, **Accept**, **Keep route**.
- Same simulation functions and timing (`src/tracking.py`), so the roadblock is still possible within about 15 s of P1 appearing.
- No silent fallback: a failed live call shows "Live call failed: …". Fake fields are marked NOT LIVE.
- Simulated tracking always shows "SIMULATED POSITION · SIMULATED ROADBLOCK". The map is an SVG drawn from `fixtures/route/map.json`, no map tiles, so it does not depend on the network.

## Go/no-go rule

The React board is used on stage **only if**, at the 10:00 hotspot check on the presenting laptop, it runs Fixture A live twice and the roadblock beat once with no problem, and the team rehearses with it at 10:30. Otherwise present with Streamlit as scripted in `talk/SCRIPT.md`.

## Files

- `api.py`: FastAPI wrapper (`/api/fixtures`, `/api/run`, `/api/fake`, `/api/sim/*`), serves `web/dist` at `/`.
- `tests/test_api.py`: API tests with the cloud calls monkeypatched.
- `web/`: Vite + React + Framer Motion source; `web/dist` is the committed build.
