import { useEffect, useRef, useState } from "react";
import Button from "./Button.jsx";
import CrewAlert from "./CrewAlert.jsx";
import { fmtMmss } from "../format.js";

// Layout-check button only with ?dev=1 in the URL. Never on stage.
const DEV = new URLSearchParams(window.location.search).get("dev") === "1";

function Segmented({ label, options, value, onChange, disabled }) {
  return (
    <div className="field">
      <div className="field-label">{label}</div>
      <div className="segmented" role="radiogroup" aria-label={label}>
        {options.map((o) => (
          <button
            key={o.value}
            type="button"
            role="radio"
            aria-checked={value === o.value}
            className={value === o.value ? "seg seg-on" : "seg"}
            disabled={disabled}
            onClick={() => onChange(o.value)}
          >
            {o.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function MicRecorder({ mic, onMic, disabled }) {
  const [rec, setRec] = useState(null); // { recorder, stream, start }
  const [secs, setSecs] = useState(0);
  const [err, setErr] = useState(null);
  const chunks = useRef([]);
  const recRef = useRef(null);
  recRef.current = rec;

  useEffect(() => {
    if (!rec) return undefined;
    const id = setInterval(() => setSecs((performance.now() - rec.start) / 1000), 250);
    return () => clearInterval(id);
  }, [rec]);

  // Release the microphone if the panel goes away mid-recording.
  useEffect(
    () => () => {
      const r = recRef.current;
      if (r) {
        if (r.recorder.state !== "inactive") r.recorder.stop();
        r.stream.getTracks().forEach((t) => t.stop());
      }
    },
    []
  );

  async function start() {
    setErr(null);
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || typeof MediaRecorder === "undefined") {
      setErr("This browser cannot record here (needs http://localhost or https).");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mime = ["audio/webm;codecs=opus", "audio/webm"].find((t) => MediaRecorder.isTypeSupported(t));
      const recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
      const startedAt = performance.now();
      chunks.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size) chunks.current.push(e.data);
      };
      recorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunks.current, { type: recorder.mimeType || "audio/webm" });
        onMic(blob.size ? { blob, secs: (performance.now() - startedAt) / 1000 } : null);
        setRec(null);
      };
      onMic(null);
      setSecs(0);
      recorder.start();
      setRec({ recorder, stream, start: startedAt });
    } catch (e) {
      setErr(`Microphone unavailable: ${e.message}`);
    }
  }

  function stop() {
    if (rec && rec.recorder.state !== "inactive") rec.recorder.stop();
  }

  return (
    <div className="mic">
      <div className="mic-row">
        {rec ? (
          <Button variant="danger" onClick={stop}>
            Stop
          </Button>
        ) : (
          <Button onClick={start} disabled={disabled}>
            Record
          </Button>
        )}
        <span className="mono mic-time">
          {rec ? `${fmtMmss(secs / 60)}` : mic ? `Recorded ${fmtMmss(mic.secs / 60)}` : "No recording yet"}
        </span>
        {rec && <span className="mic-dot" aria-hidden="true" />}
      </div>
      {err && <p className="note note-error">{err}</p>}
    </div>
  );
}

export default function InputRail({
  fixtures,
  fixturesError,
  fixtureId,
  onFixture,
  source,
  onSource,
  mic,
  onMic,
  running,
  canSend,
  onSendLive,
  onFake,
  tracking,
  onToggleTracking,
  sim,
  simLocked,
  simError,
  onAnswer,
  onInject,
}) {
  const fixture = fixtures.find((f) => f.id === fixtureId);
  const injectDisabled = !sim || sim.busy || simLocked;

  return (
    <aside className="rail">
      <h2 className="section-label">Paramedic input</h2>

      {fixturesError && <p className="note note-error">Could not load fixtures: {fixturesError}</p>}
      {fixtures.length > 0 && (
        <Segmented
          label="Fixture"
          options={fixtures.map((f) => ({ value: f.id, label: f.label }))}
          value={fixtureId}
          onChange={onFixture}
          disabled={running}
        />
      )}

      <Segmented
        label="Voice note"
        options={[
          { value: "file", label: "Saved file" },
          { value: "mic", label: "Live mic" },
        ]}
        value={source}
        onChange={onSource}
        disabled={running}
      />
      {source === "file" ? (
        fixture && <audio key={fixture.id} className="audio" controls preload="none" src={fixture.audio} />
      ) : (
        <MicRecorder mic={mic} onMic={onMic} disabled={running} />
      )}

      <Button variant="primary" className="btn-send" disabled={!canSend} onClick={onSendLive}>
        Send live
      </Button>
      {DEV && (
        <button type="button" className="textbtn textbtn-small" disabled={running || !fixture} onClick={onFake}>
          Fake fields (layout check)
        </button>
      )}

      <div className="toggle-row">
        <button
          type="button"
          role="switch"
          aria-checked={tracking}
          className={tracking ? "switch switch-on" : "switch"}
          onClick={() => onToggleTracking(!tracking)}
        >
          <span className="switch-knob" />
        </button>
        <span className="toggle-label" onClick={() => onToggleTracking(!tracking)}>
          Ambulance tracking (simulated)
        </span>
      </div>

      <CrewAlert sim={sim} onAnswer={onAnswer} disabled={simLocked} />

      {tracking && (
        <div className="presenter">
          <div className="field-label">Presenter</div>
          <div className="presenter-row">
            <Button className="btn-small" disabled={injectDisabled} onClick={() => onInject("closed")}>
              Inject roadblock (closed)
            </Button>
            <Button className="btn-small" disabled={injectDisabled} onClick={() => onInject("slow")}>
              Inject heavy traffic (slow)
            </Button>
          </div>
          {simError && <p className="note note-error">{simError}</p>}
        </div>
      )}

      {fixture && (
        <figure className="photo">
          <img key={fixture.id} src={fixture.photo} alt="Monitor photo (sample device, read live by the vision model)" />
          <figcaption>{fixture.photo_caption}</figcaption>
        </figure>
      )}
    </aside>
  );
}
