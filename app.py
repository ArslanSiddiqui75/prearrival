"""PreArrival ER board. Imports decide and score_news. Does not reimplement thresholds."""

import json
import math
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import streamlit as st

from src.confidence import compute_flags, confirm_with_crew
from src.decide import decide
from src.news import PARAMS, score_news
from src.route import load_graph, node
from src.tracking import new_sim, sim_answer, sim_inject, sim_position, total_min

ROOT = Path(__file__).parent
MIC_PATH = Path(tempfile.gettempdir()) / "prearrival_mic.wav"
FIXTURES = {"A — head injury": ROOT / "fixtures/a", "B — ankle": ROOT / "fixtures/b"}
SAFETY = "This prepares the room. It does not diagnose, and it does not replace the nurse's triage."
# Verified 2026-10-10: 2018 AHA/ASA early stroke guideline (the 2019 update dropped the fixed number).
LITERATURE = (
    "Published context, not our measurement: the 2018 AHA/ASA stroke guideline set a target of brain imaging "
    "within 20 minutes of ER arrival for more than half of treatment candidates "
    "(Powers et al., Stroke 2018, doi:10.1161/STR.0000000000000158)."
)
LABELS = {
    "rr": "Resp rate",
    "spo2": "SpO2",
    "on_oxygen": "On oxygen",
    "sbp": "Systolic BP",
    "hr": "Heart rate",
    "consciousness": "Consciousness",
    "temp_c": "Temp °C",
    "dbp": "Diastolic BP",
    "mechanism": "Mechanism",
    "eta_min": "ETA (min)",
}
NOTE_KEYS = ("consciousness", "mechanism", "eta_min", "on_oxygen", "rr", "temp_c")
MONITOR_KEYS = ("hr", "sbp", "dbp", "spo2")
AMBER = "#b26a00"
SIM_LABEL = "SIMULATED POSITION · SIMULATED ROADBLOCK"
MAP_HEIGHT = 340
ETA_GAP_MIN = 3  # show route and spoken ETA side by side when they differ by more than this
PRIORITY_COLOR = {"P1": "#c62828", "P2": "#ef6c00", "P3": "#2e7d32"}

# Layout check only. The board labels this as not live.
FAKE = {
    "fields": {
        "hr": 132, "sbp": 96, "dbp": 60, "spo2": 95, "rr": None, "temp_c": None,
        "consciousness": "not_alert", "on_oxygen": False, "mechanism": "head_injury", "eta_min": 8,
        "evidence": {"hr": "FAKE", "sbp": "FAKE", "consciousness": "FAKE", "mechanism": "FAKE", "eta_min": "FAKE"},
    },
    "transcript": "FAKE FIELDS — layout check, no cloud call.",
    "stamps": {},
}

st.set_page_config(page_title="PreArrival", layout="wide")
st.markdown(
    """
    <style>
      header[data-testid="stHeader"] {display: none;}
      .block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
      h1#prearrival-incoming-patient, .stMarkdown h1 {font-size: 2.1rem; padding: 0 0 .2rem 0;}
      .big-priority {font-size: 7rem; font-weight: 800; color: white; text-align: center;
                     border-radius: 18px; line-height: 1.1; padding: .2em 0;}
      .checklist li {font-size: 2.6rem; font-weight: 700; line-height: 1.35;}
      .leadtime {font-size: 2.4rem; font-weight: 700;}
      .stamp {font-family: monospace; font-size: 1.1rem;}
      .safety {font-size: 1.3rem; font-style: italic;}
      .simlabel {background: #b26a00; color: white; font-weight: 800; letter-spacing: .08em;
                 padding: .3em .7em; border-radius: 6px; display: inline-block;}
      .countdown {font-size: 2.4rem; font-weight: 700; font-variant-numeric: tabular-nums; color: #1f5f8b;}
      .simstatus {font-size: 1.15rem; font-weight: 700; color: #b26a00;}
    </style>
    """,
    unsafe_allow_html=True,
)


def run_live(folder: Path, audio_path: Path) -> dict:
    from src.extract_note import extract_note
    from src.transcribe import transcribe
    from src.vision import read_monitor

    # Speech and photo are independent; send both at once to cut stage wait.
    with ThreadPoolExecutor(max_workers=2) as pool:
        heard_job = pool.submit(transcribe, str(audio_path))
        photo_job = pool.submit(read_monitor, str(next(folder.glob("monitor.*"))))
        heard, photo = heard_job.result(), photo_job.result()
    note = extract_note(heard["text"])
    fields = {k: note[k] for k in NOTE_KEYS} | {k: photo[k] for k in MONITOR_KEYS}
    fields["evidence"] = {**note["evidence"], **photo["evidence"]}
    # Flags only mark values to confirm with the crew; score_news and decide never read them.
    fields["flags"] = compute_flags(note, photo, heard["segments"])
    stamps = {
        "speech-to-text": heard["requested_at"],
        "monitor photo": photo["requested_at"],
        "note extraction": note["requested_at"],
    }
    return {"fields": fields, "transcript": heard["text"], "stamps": stamps}


def tracking_map(sim: dict, graph: dict, pos: dict):
    import pydeck as pdk

    def path(legs):
        if not legs:
            return []
        pts = [node(graph, legs[0]["from"])] + [node(graph, leg["to"]) for leg in legs]
        return [[p["lon"], p["lat"]] for p in pts]

    def seg(seg_id):
        return next(x for x in graph["segments"] if x["id"] == seg_id)

    def seg_path(seg_id):
        return [[node(graph, seg(seg_id)[e])["lon"], node(graph, seg(seg_id)[e])["lat"]] for e in ("from", "to")]

    paths = [{"path": path(sim["route"]["legs"]), "color": [31, 95, 139], "width": 6, "label": "Current route"}]
    if sim["pending"]:
        paths.append({"path": path(sim["pending"]["offer"]["alternate"]["legs"]), "color": [230, 126, 34], "width": 6,
                      "label": "Alternate offered"})
    incidents = [(x, "Closed") for x in sim["closed"]] + [(x, "Heavy traffic") for x in sim["slow"]]
    paths += [{"path": seg_path(x), "color": [198, 40, 40], "width": 10, "label": f"{what} (simulated): {seg(x)['name']}"}
              for x, what in incidents]

    dest = node(graph, graph["destination"])
    pickup = node(graph, sim["route"]["route"][0])
    points = [
        {"lon": pickup["lon"], "lat": pickup["lat"], "fill": [120, 120, 120], "label": "Pickup: " + pickup["name"]},
        {"lon": dest["lon"], "lat": dest["lat"], "fill": [46, 125, 50], "label": "Hospital: " + dest["name"]},
        {"lon": pos["lon"], "lat": pos["lat"], "fill": [198, 40, 40], "label": "Ambulance (simulated)"},
    ]
    labels = [
        {"lon": pickup["lon"], "lat": pickup["lat"], "text": "Pickup"},
        {"lon": dest["lon"], "lat": dest["lat"], "text": "PIMS"},
        {"lon": pos["lon"], "lat": pos["lat"], "text": "Ambulance"},
    ]
    for x, what in incidents:
        a, b = (node(graph, seg(x)[e]) for e in ("from", "to"))
        labels.append({"lon": (a["lon"] + b["lon"]) / 2, "lat": (a["lat"] + b["lat"]) / 2, "text": what})

    # Frame everything drawn (deck.gl world is 512 * 2**zoom px wide; map is ~1000 x MAP_HEIGHT px), with a margin.
    lons = [c[0] for p in paths for c in p["path"]] + [pt["lon"] for pt in points]
    lats = [c[1] for p in paths for c in p["path"]] + [pt["lat"] for pt in points]
    span_lon = max(max(lons) - min(lons), 0.005)
    span_lat = max(max(lats) - min(lats), 0.005)
    cos_lat = math.cos(math.radians((max(lats) + min(lats)) / 2))
    zoom = min(math.log2(1000 * 360 / (512 * span_lon)), math.log2(MAP_HEIGHT * 360 * cos_lat / (512 * span_lat))) - 0.35

    return pdk.Deck(
        layers=[
            # Widths are metres clamped to a pixel range; pydeck would read a string like "pixels" as a field name.
            pdk.Layer("PathLayer", paths, get_path="path", get_color="color", get_width="width",
                      width_scale=10, width_min_pixels=4, width_max_pixels=12, cap_rounded=True, joint_rounded=True,
                      pickable=True),
            pdk.Layer("ScatterplotLayer", points, get_position="[lon, lat]", get_fill_color="fill",
                      get_line_color=[255, 255, 255], stroked=True, line_width_min_pixels=2,
                      get_radius=60, radius_min_pixels=8, radius_max_pixels=12, pickable=True),
            pdk.Layer("TextLayer", labels, get_position="[lon, lat]", get_text="text", get_size=15,
                      get_color=[20, 32, 43], get_text_anchor='"start"', get_alignment_baseline='"center"',
                      get_pixel_offset=[14, 0], font_weight=700, background=True, get_background_color=[255, 255, 255, 220],
                      background_padding=[4, 2]),
        ],
        initial_view_state=pdk.ViewState(latitude=(max(lats) + min(lats)) / 2, longitude=(max(lons) + min(lons)) / 2,
                                         zoom=zoom),
        map_style="light",
        # No scroll-wheel zoom: scrolling the page over the map on stage must scroll the page. +/- buttons still zoom.
        views=[pdk.View(type="MapView", controller={"scrollZoom": False, "dragPan": True, "doubleClickZoom": True})],
        tooltip={"text": "{label}"},
    )


def fmt_mmss(minutes: float) -> str:
    secs = max(0, round(minutes * 60))
    return f"{secs // 60}:{secs % 60:02d}"


# ---------- input panel ----------
st.title("PreArrival — incoming patient")
left, right = st.columns([1, 2], gap="large")

with left:
    st.subheader("Paramedic input")
    choice = st.radio("Fixture", list(FIXTURES), horizontal=True)
    folder = FIXTURES[choice]
    # Saved file is the stage promise. Live mic is opt-in, only after the file path has worked twice.
    source = st.radio("Voice note", ["Saved file", "Live mic"], horizontal=True)
    photos = list(folder.glob("monitor.*"))
    if source == "Saved file":
        audio = folder / "audio.wav"
        if audio.exists():
            st.audio(str(audio))
        else:
            st.warning(f"Missing {audio.relative_to(ROOT)}")
    else:
        recording = st.audio_input("Speak the handoff in English (ETA, what happened, alert or confused, oxygen)")
        audio = MIC_PATH
        if recording is not None:
            MIC_PATH.write_bytes(recording.getvalue())
        elif MIC_PATH.exists():
            MIC_PATH.unlink()
    live = st.button("Send live", type="primary", width="stretch", disabled=not (audio.exists() and photos))
    fake = st.button("Fake fields (layout check)", width="stretch")

    if live:
        with st.spinner("Calling the cloud… (over ~15 s means the free-tier rate limit is pausing it; it retries on its own)"):
            try:
                st.session_state.result = {**run_live(folder, audio), "live": True, "fixture": choice, "source": source}
            except Exception as e:  # show the failure; never fall back to a fixture
                st.session_state.result = None
                st.error(f"Live call failed: {type(e).__name__}: {e}")
    if fake:
        st.session_state.result = {**FAKE, "live": False, "fixture": choice}
    if live or fake:
        if st.session_state.get("result"):
            st.session_state.result["run_id"] = time.time()

    # Logistics only. Off by default; with it off the board is unchanged.
    tracking_on = st.toggle("Ambulance tracking (simulated)", value=False, key="tracking")
    # Crew alert and presenter controls render here (filled below), above the photo, so Accept stays on screen.
    tracking_slot = st.container()

    if photos:
        caption = "Monitor photo (stand-in, not this patient)"
        meta = folder / "photo.json"
        if meta.exists():
            src = json.loads(meta.read_text()).get("source", {})
            caption += f" — {src.get('author', '')}, {src.get('license', '')}"
        st.image(str(photos[0]), caption=caption)
    else:
        st.warning(f"Missing {folder.relative_to(ROOT)}/monitor.jpg")

result = st.session_state.get("result")
GRAPH = load_graph() if tracking_on else None
if tracking_on and result:
    sim = st.session_state.get("sim")
    if not sim or sim["run_id"] != result.get("run_id"):
        st.session_state.sim = new_sim(GRAPH, FIXTURES[result["fixture"]].name, result.get("run_id"), time.time())
sim = st.session_state.get("sim") if tracking_on and result else None


def _arrived(sim: dict) -> bool:
    return sim["halted"] or sim_position(sim, GRAPH, time.time())["arrived"]


if sim:
    with tracking_slot:

        @st.fragment(run_every=None if _arrived(sim) else "1s")
        def crew_alert():
            current = st.session_state.sim
            if current["pending"]:
                st.warning(f"**Crew alert:** {current['alert']}")
                accept_col, keep_col = st.columns(2)
                if accept_col.button("Accept", type="primary", width="stretch", key="crew_accept"):
                    st.session_state.sim = sim_answer(current, GRAPH, True, time.time())
                    st.rerun()
                if keep_col.button("Keep route", width="stretch", key="crew_keep"):
                    st.session_state.sim = sim_answer(current, GRAPH, False, time.time())
                    st.rerun()

        crew_alert()

        st.caption("Presenter")
        busy = bool(sim["pending"]) or _arrived(sim)
        block_col, slow_col = st.columns(2)
        if block_col.button("Inject roadblock (closed)", width="stretch", disabled=busy):
            st.session_state.sim = sim_inject(sim, GRAPH, "closed", time.time())
            st.rerun()
        if slow_col.button("Inject heavy traffic (slow)", width="stretch", disabled=busy):
            st.session_state.sim = sim_inject(sim, GRAPH, "slow", time.time())
            st.rerun()

# ---------- board ----------
with right:
    if not result:
        st.info("Pick a fixture and press **Send live**.")
        st.stop()

    fields = result["fields"]
    score = score_news(fields)
    plan = decide(fields, score)

    if not result["live"]:
        st.error("NOT LIVE — fake fields for layout only.")

    p_col, list_col = st.columns([1, 2], gap="large")
    with p_col:
        color = PRIORITY_COLOR[plan["priority"]]
        st.markdown(f'<div class="big-priority" style="background:{color}">{plan["priority"]}</div>', unsafe_allow_html=True)
        st.caption("Why: " + "; ".join(plan["reasons"]))
    with list_col:
        st.markdown("### Prepare for")
        items = "".join(f"<li>{x}</li>" for x in plan["prepare_for"])
        st.markdown(f'<ul class="checklist">{items}</ul>', unsafe_allow_html=True)

    eta = fields.get("eta_min")
    if sim:
        route_eta = None if sim["halted"] else total_min(sim["route"])
        lead_col, count_col = st.columns([3, 2], gap="large")
        with lead_col:
            lead = f"{route_eta:g} min" if route_eta is not None else "unknown"
            st.markdown(f'<div class="leadtime">Prep lead time: {lead}</div>', unsafe_allow_html=True)
            spoken = f"{eta} min" if eta is not None else "not heard"
            quote = fields.get("evidence", {}).get("eta_min")
            note = "route ETA (simulated)" if route_eta is not None else "no open route"
            st.markdown(f"Uses the {note}. Spoken ETA: **{spoken}**" + (f" — “{quote}”" if quote else ""))
            if route_eta is not None and eta is not None and abs(route_eta - eta) > ETA_GAP_MIN:
                st.markdown(f"**Route ETA {route_eta:g} min · spoken ETA {eta} min** (differ by more than {ETA_GAP_MIN} min)")
        with count_col:

            @st.fragment(run_every=None if _arrived(sim) else "1s")
            def countdown():
                current = st.session_state.sim
                pos = sim_position(current, GRAPH, time.time())
                if current["halted"]:
                    text = "Arrival unknown"
                elif pos["arrived"]:
                    text = "Arrived (simulated)"
                else:
                    text = f"Arrives in {fmt_mmss(pos['eta_route_min'])}"
                st.markdown(f'<div class="countdown">{text}</div>', unsafe_allow_html=True)
                if current["status"]:
                    st.markdown(f'<div class="simstatus">{current["status"]}</div>', unsafe_allow_html=True)

            countdown()
    else:
        lead = f"{eta} min" if eta is not None else "unknown (no ETA heard)"
        st.markdown(f'<div class="leadtime">Prep lead time: {lead}</div>', unsafe_allow_html=True)
    lead_caption = "The checklist exists before the patient arrives, so prep starts one ETA earlier. " + LITERATURE
    if not sim:
        st.caption(lead_caption)

    if sim:

        @st.fragment(run_every=None if _arrived(sim) else "1s")
        def tracking_board():
            current = st.session_state.sim
            pos = sim_position(current, GRAPH, time.time())
            st.markdown(f'<span class="simlabel">{SIM_LABEL}</span>', unsafe_allow_html=True)
            st.pydeck_chart(tracking_map(current, GRAPH, pos), height=MAP_HEIGHT, key="tracking_map")  # stable key: update in place, no blank remount
            st.caption("Blue: current route · orange: alternate offered · red: simulated incident. "
                       "Illustrative road graph, not a real road network. Map tiles © CARTO, © OpenStreetMap contributors.")

        tracking_board()
        st.caption(lead_caption)

    if result["stamps"]:
        st.markdown(f"**Cloud requests sent at** · voice: {result.get('source', 'Saved file').lower()}")
        for name, ts in result["stamps"].items():
            st.markdown(f'<span class="stamp">{name}: {ts}</span>', unsafe_allow_html=True)

    st.divider()
    f_col, n_col = st.columns(2, gap="large")
    with f_col:
        st.markdown("#### Extracted fields and evidence")
        evidence = fields.get("evidence", {})
        flags = fields.get("flags", {})
        rows = pd.DataFrame(
            [
                {
                    "Field": LABELS[k],
                    "Value": "—" if fields.get(k) is None else str(fields[k]),
                    "Evidence": evidence.get(k, ""),
                    "Check": ", ".join(flags.get(k, [])),
                }
                for k in ["mechanism", "consciousness", "eta_min", "hr", "sbp", "dbp", "spo2", "rr", "temp_c", "on_oxygen"]
            ]
        )
        styled = rows.style.map(lambda v: f"color: {AMBER}; font-weight: 600" if v else "", subset=["Check"])
        st.dataframe(styled, hide_index=True, width="stretch")
        with st.expander("Transcript"):
            st.write(result["transcript"])
    with n_col:
        st.markdown("#### Partial NEWS2 (Scale 1)")
        parts = [f"{LABELS[k]} {fields[k]} → {score['breakdown'][k]}" for k in PARAMS if k in score["breakdown"]]
        st.markdown("\n".join(f"- {p}" for p in parts))
        st.markdown(f"**Total = {' + '.join(str(score['breakdown'][k]) for k in PARAMS if k in score['breakdown'])} = {score['points']}**")
        if score["missing"]:
            st.markdown("Not scored (missing, not assumed normal): " + ", ".join(LABELS[k] for k in score["missing"]))
        to_confirm = confirm_with_crew(fields.get("flags", {}), score["missing"])
        if to_confirm:
            st.markdown(
                f'<p style="color:{AMBER};font-weight:600;font-size:1.15rem">Confirm with crew: {", ".join(to_confirm)}</p>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown("Nothing to confirm")

    st.markdown(f'<p class="safety">{SAFETY}</p>', unsafe_allow_html=True)
