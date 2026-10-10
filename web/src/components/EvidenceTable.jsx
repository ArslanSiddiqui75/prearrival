import { memo, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { fmtField } from "../format.js";

// Shows what the API sent. The audio span and the segments come from the board; nothing is matched here.

// The transcript, segment by segment; the one playing is marked and its quote highlighted inside it.
function Transcript({ transcript, segments, playing }) {
  if (!segments || !segments.length) return <p className="mono">{transcript}</p>;
  return (
    <p className="mono transcript-text">
      {segments.map((seg, i) => {
        const hit = playing && playing.span && seg.start === playing.span.start && seg.end === playing.span.end;
        const text = seg.text || "";
        let body = text;
        if (hit && playing.quote) {
          const idx = text.toLowerCase().indexOf(playing.quote.toLowerCase());
          if (idx >= 0) {
            body = (
              <>
                {text.slice(0, idx)}
                <motion.mark className="quote-mark" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.35 }}>
                  {text.slice(idx, idx + playing.quote.length)}
                </motion.mark>
                {text.slice(idx + playing.quote.length)}
              </>
            );
          }
          if (body === text) {
            body = (
              <motion.mark className="quote-mark" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.35 }}>
                {text}
              </motion.mark>
            );
          }
        }
        return (
          <span key={`${seg.start}-${i}`} className={hit ? "seg seg-on" : "seg"}>
            {body}{" "}
          </span>
        );
      })}
    </p>
  );
}

function HearButton({ row, playing, progress, onPlay, disabled }) {
  const on = playing && playing.key === row.key;
  return (
    <button
      type="button"
      className={on ? "hear hear-on" : "hear"}
      onClick={() => onPlay(row)}
      disabled={disabled}
      aria-label={on ? `Stop ${row.label}` : `Hear ${row.label}`}
      title={disabled ? "No audio for this run" : on ? "Stop" : "Play the words this value came from"}
    >
      <span className="hear-bar" style={{ width: `${on ? Math.round(progress * 100) : 0}%` }} />
      <span className="hear-text">{on ? "■ Stop" : "▶ Hear it"}</span>
    </button>
  );
}

function EvidenceTable({ rows, transcript, segments, audioUrl, photoUrl, photoCaption }) {
  const audioRef = useRef(null);
  const [playing, setPlaying] = useState(null); // { key, span, quote }
  const [progress, setProgress] = useState(0);
  const [photoRow, setPhotoRow] = useState(null);
  const detailsRef = useRef(null);

  // Stop at the end of the span: timeupdate is coarse, so a rAF loop checks the time.
  useEffect(() => {
    if (!playing) return undefined;
    const audio = audioRef.current;
    if (!audio) return undefined;
    let raf = 0;
    const tick = () => {
      const { start, end } = playing.span;
      const len = Math.max(end - start, 0.05);
      setProgress(Math.min(Math.max((audio.currentTime - start) / len, 0), 1));
      if (audio.currentTime >= end || audio.ended) {
        audio.pause();
        setPlaying(null);
        return;
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [playing]);

  useEffect(() => {
    // New run or new source: stop whatever was playing.
    const audio = audioRef.current;
    if (audio) audio.pause();
    setPlaying(null);
    setProgress(0);
  }, [audioUrl, rows]);

  function hear(row) {
    const audio = audioRef.current;
    if (!audio || !row.audio_span) return;
    if (playing && playing.key === row.key) {
      audio.pause();
      setPlaying(null);
      return;
    }
    if (detailsRef.current) detailsRef.current.open = true;
    const begin = () => {
      audio.currentTime = row.audio_span.start;
      setProgress(0);
      setPlaying({ key: row.key, span: row.audio_span, quote: row.evidence });
      audio.play().catch(() => setPlaying(null));
    };
    if (audio.readyState >= 1) begin();
    else {
      audio.addEventListener("loadedmetadata", begin, { once: true });
      audio.load();
    }
  }

  const isMonitor = (r) => r.audio_span == null && /monitor photo/i.test(r.evidence || "");

  return (
    <section className="panel">
      <h2 className="section-label">Extracted fields and evidence</h2>
      {audioUrl && <audio ref={audioRef} src={audioUrl} preload="auto" />}
      <table className="evidence">
        <thead>
          <tr>
            <th>Field</th>
            <th>Value</th>
            <th>Evidence</th>
            <th>Check</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.key} className={playing && playing.key === r.key ? "row-on" : ""}>
              <td className="ev-field">{r.label}</td>
              <td className="mono ev-value">{fmtField(r.key, r.value)}</td>
              <td className="ev-quote">
                {r.evidence ? (
                  isMonitor(r) && photoUrl ? (
                    <button type="button" className="quote-btn" onClick={() => setPhotoRow(r)} title="Show the monitor photo">
                      “{r.evidence}”
                    </button>
                  ) : (
                    `“${r.evidence}”`
                  )
                ) : (
                  ""
                )}
                {r.audio_span && audioUrl && (
                  <HearButton row={r} playing={playing} progress={progress} onPlay={hear} />
                )}
              </td>
              <td className="ev-check">
                {(r.flags || []).map((f) => (
                  <span key={f} className="chip">
                    {f}
                  </span>
                ))}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <details className="transcript" ref={detailsRef}>
        <summary>Transcript</summary>
        <Transcript transcript={transcript} segments={segments} playing={playing} />
      </details>
      <AnimatePresence>
        {photoRow && photoUrl && (
          <motion.div
            className="lightbox"
            role="dialog"
            aria-label="Monitor photo"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={() => setPhotoRow(null)}
          >
            <motion.figure
              className="lightbox-figure"
              initial={{ scale: 0.96, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.96, opacity: 0 }}
              transition={{ duration: 0.2 }}
              onClick={(e) => e.stopPropagation()}
            >
              <img src={photoUrl} alt="Monitor photo (sample device, read live by the vision model)" />
              <figcaption>
                <strong>{photoRow.label}:</strong> “{photoRow.evidence}”
                {photoCaption ? <span className="lightbox-credit"> · {photoCaption}</span> : null}
              </figcaption>
              <button type="button" className="textbtn textbtn-small" onClick={() => setPhotoRow(null)}>
                Close
              </button>
            </motion.figure>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}

export default memo(EvidenceTable);
