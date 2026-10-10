"""PreArrival ER board. Imports decide and score_news. Does not reimplement thresholds."""

from pathlib import Path

import streamlit as st

from src.decide import decide
from src.news import PARAMS, score_news

ROOT = Path(__file__).parent
FIXTURES = {"A — head injury": ROOT / "fixtures/a", "B — ankle": ROOT / "fixtures/b"}
SAFETY = "This prepares the room. It does not diagnose, and it does not replace the nurse's triage."
# Talk owner: verify this figure and source before the demo.
LITERATURE = (
    "Published context, not our measurement: AHA/ASA guidance targets brain imaging within "
    "20 minutes of ER arrival for suspected stroke (Powers et al., Stroke 2019)."
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
      .big-priority {font-size: 7rem; font-weight: 800; color: white; text-align: center;
                     border-radius: 18px; line-height: 1.1; padding: .2em 0;}
      .checklist li {font-size: 2.6rem; font-weight: 700; line-height: 1.35;}
      .leadtime {font-size: 2.4rem; font-weight: 700;}
      .stamp {font-family: monospace; font-size: 1.1rem;}
      .safety {font-size: 1.3rem; font-style: italic;}
    </style>
    """,
    unsafe_allow_html=True,
)


def run_live(folder: Path) -> dict:
    from src.extract_note import extract_note
    from src.transcribe import transcribe
    from src.vision import read_monitor

    heard = transcribe(str(folder / "audio.wav"))
    photo = read_monitor(str(next(folder.glob("monitor.*"))))
    note = extract_note(heard["text"])
    fields = {k: v for k, v in {**note, **photo}.items() if k not in ("evidence", "requested_at")}
    fields["evidence"] = {**note["evidence"], **photo["evidence"]}
    stamps = {
        "speech-to-text": heard["requested_at"],
        "monitor photo": photo["requested_at"],
        "note extraction": note["requested_at"],
    }
    return {"fields": fields, "transcript": heard["text"], "stamps": stamps}


# ---------- input panel ----------
st.title("PreArrival — incoming patient")
left, right = st.columns([1, 2], gap="large")

with left:
    st.subheader("Paramedic input")
    choice = st.radio("Fixture", list(FIXTURES), horizontal=True)
    folder = FIXTURES[choice]
    audio = folder / "audio.wav"
    photos = list(folder.glob("monitor.*"))
    if audio.exists():
        st.audio(str(audio))
    else:
        st.warning(f"Missing {audio.relative_to(ROOT)}")
    if photos:
        st.image(str(photos[0]), caption="Monitor photo")
    else:
        st.warning(f"Missing {folder.relative_to(ROOT)}/monitor.jpg")

    live = st.button("Send live", type="primary", use_container_width=True, disabled=not (audio.exists() and photos))
    fake = st.button("Fake fields (layout check)", use_container_width=True)

    if live:
        with st.spinner("Calling the cloud…"):
            try:
                st.session_state.result = {**run_live(folder), "live": True, "fixture": choice}
            except Exception as e:  # show the failure; never fall back to a fixture
                st.session_state.result = None
                st.error(f"Live call failed: {type(e).__name__}: {e}")
    if fake:
        st.session_state.result = {**FAKE, "live": False, "fixture": choice}

result = st.session_state.get("result")

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
    lead = f"{eta} min" if eta is not None else "unknown (no ETA heard)"
    st.markdown(f'<div class="leadtime">Prep lead time: {lead}</div>', unsafe_allow_html=True)
    st.caption("The checklist exists before the patient arrives, so prep starts one ETA earlier. " + LITERATURE)

    if result["stamps"]:
        st.markdown("**Cloud requests sent at**")
        for name, ts in result["stamps"].items():
            st.markdown(f'<span class="stamp">{name}: {ts}</span>', unsafe_allow_html=True)

    st.divider()
    f_col, n_col = st.columns(2, gap="large")
    with f_col:
        st.markdown("#### Extracted fields and evidence")
        evidence = fields.get("evidence", {})
        rows = [
            {"Field": LABELS[k], "Value": "—" if fields.get(k) is None else str(fields[k]), "Evidence": evidence.get(k, "")}
            for k in ["mechanism", "consciousness", "eta_min", "hr", "sbp", "dbp", "spo2", "rr", "temp_c", "on_oxygen"]
        ]
        st.dataframe(rows, hide_index=True, use_container_width=True)
        with st.expander("Transcript"):
            st.write(result["transcript"])
    with n_col:
        st.markdown("#### Partial NEWS2 (Scale 1)")
        parts = [f"{LABELS[k]} {fields[k]} → {score['breakdown'][k]}" for k in PARAMS if k in score["breakdown"]]
        st.markdown("\n".join(f"- {p}" for p in parts))
        st.markdown(f"**Total = {' + '.join(str(score['breakdown'][k]) for k in PARAMS if k in score['breakdown'])} = {score['points']}**")
        if score["missing"]:
            st.markdown("Not scored (missing, not assumed normal): " + ", ".join(LABELS[k] for k in score["missing"]))

    st.markdown(f'<p class="safety">{SAFETY}</p>', unsafe_allow_html=True)
