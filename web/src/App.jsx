import { memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { MotionConfig, motion } from "motion/react";
import * as api from "./api.js";
import { reveal } from "./motion.js";
import TopBar from "./components/TopBar.jsx";
import InputRail from "./components/InputRail.jsx";
import { Pipeline, StampStrip } from "./components/Pipeline.jsx";
import Hero from "./components/Hero.jsx";
import TrackingMap from "./components/TrackingMap.jsx";
import EvidenceTable from "./components/EvidenceTable.jsx";
import NewsPanel from "./components/NewsPanel.jsx";

// The board only displays what the API returns and calls the API. No thresholds or scoring here.

function readTheme() {
  try {
    const t = localStorage.getItem("prearrival-theme");
    if (t === "dark" || t === "light") return t;
  } catch {
    /* storage unavailable */
  }
  return "light";
}

function applyTheme(t) {
  document.documentElement.setAttribute("data-theme", t);
}

function useTheme() {
  const [theme, setThemeState] = useState(() => {
    const t = readTheme();
    applyTheme(t);
    return t;
  });
  const toggle = useCallback(() => {
    setThemeState((cur) => {
      const next = cur === "dark" ? "light" : "dark";
      applyTheme(next); // before render, so the map reads the new colours
      try {
        localStorage.setItem("prearrival-theme", next);
      } catch {
        /* storage unavailable */
      }
      return next;
    });
  }, []);
  return [theme, toggle];
}

const ResultView = memo(function ResultView({ result, sim, theme, pollNote, audioUrl, fixture }) {
  return (
    <motion.div className="result" variants={reveal.container} initial="hidden" animate="show">
      {result.live ? (
        <StampStrip stamps={result.stamps || {}} source={result.source} />
      ) : (
        <div className="banner banner-notlive">NOT LIVE — fake fields for layout only.</div>
      )}
      <Hero result={result} sim={sim} />
      {sim && <TrackingMap sim={sim} theme={theme} pollNote={pollNote} />}
      <motion.div className="lower" layout="position" variants={reveal.fade(0.36)}>
        <EvidenceTable
          rows={result.rows}
          transcript={result.transcript}
          segments={result.transcript_segments || []}
          audioUrl={audioUrl}
          photoUrl={fixture ? fixture.photo : null}
          photoCaption={fixture ? fixture.photo_caption : ""}
        />
        <NewsPanel terms={result.news_terms} points={result.score.points} missing={result.missing} confirm={result.confirm} />
      </motion.div>
      <motion.footer className="foot" layout="position" variants={reveal.fade(0.42)}>
        <p className="safety">{result.safety}</p>
        <p className="literature">{result.literature}</p>
      </motion.footer>
    </motion.div>
  );
});

export default function App() {
  const [theme, toggleTheme] = useTheme();

  const [fixtures, setFixtures] = useState([]);
  const [fixturesError, setFixturesError] = useState(null);
  const [fixtureId, setFixtureId] = useState("a");
  const [source, setSource] = useState("file");
  const [mic, setMic] = useState(null); // { blob, secs }

  const [running, setRunning] = useState(false);
  const [runStartedAt, setRunStartedAt] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const [tracking, setTracking] = useState(false);
  const [sim, setSim] = useState(null);
  const [simRunId, setSimRunId] = useState(null); // run_id the server-side sim was started for
  const [simLocked, setSimLocked] = useState(false); // a sim POST is in flight
  const [simError, setSimError] = useState(null);
  const [pollNote, setPollNote] = useState(null);
  const simEpoch = useRef(0); // bumps on every sim mutation; stale poll responses are dropped
  const simJson = useRef("");
  const actionInFlight = useRef(false);

  const applySim = useCallback((view) => {
    const j = JSON.stringify(view);
    if (j === simJson.current) return; // identical tick: no re-render
    simJson.current = j;
    setSim(view);
  }, []);

  useEffect(() => {
    api
      .getFixtures()
      .then((list) => {
        setFixtures(list || []);
        if (list && list.length && !list.some((f) => f.id === "a")) setFixtureId(list[0].id);
      })
      .catch((e) => setFixturesError(e.message));
  }, []);

  // ---- live run / fake run ----
  async function sendLive() {
    if (running) return;
    setRunning(true);
    setError(null);
    setResult(null);
    setRunStartedAt(performance.now());
    try {
      const board = await api.runLive({
        fixture: fixtureId,
        source,
        audioBlob: source === "mic" && mic ? mic.blob : null,
      });
      setResult(board);
    } catch (e) {
      // Show the failure; never fall back to fixture data.
      setResult(null);
      const msg = e.message || String(e);
      setError(msg.startsWith("Live call failed") ? msg : `Live call failed: ${msg}`);
    } finally {
      setRunning(false);
    }
  }

  async function sendFake() {
    if (running) return;
    setError(null);
    try {
      setResult(await api.runFake(fixtureId));
    } catch (e) {
      setResult(null);
      setError(`Fake fields failed: ${e.message || e}`);
    }
  }

  // ---- tracking (mirrors app.py: start a sim per result while the toggle is on) ----
  const runId = result ? result.run_id : null;
  const resultFixture = result ? result.fixture : null;

  useEffect(() => {
    if (!tracking || runId == null || simRunId === runId) return;
    const epoch = ++simEpoch.current;
    setSimRunId(runId);
    setSim(null);
    simJson.current = "";
    setSimError(null);
    setPollNote(null);
    actionInFlight.current = true;
    setSimLocked(true);
    api
      .simStart(runId, resultFixture)
      .then((v) => {
        if (epoch === simEpoch.current) applySim(v);
      })
      .catch((e) => {
        if (epoch === simEpoch.current) setSimError(`Tracking start failed: ${e.message || e}`);
      })
      .finally(() => {
        if (epoch === simEpoch.current) {
          actionInFlight.current = false;
          setSimLocked(false);
        }
      });
  }, [tracking, runId, simRunId, resultFixture, applySim]);

  function toggleTracking(on) {
    setTracking(on);
    if (!on) {
      simEpoch.current++;
      actionInFlight.current = false;
      setSimLocked(false);
      setSim(null);
      simJson.current = "";
      setSimRunId(null);
      setSimError(null);
      setPollNote(null);
      api.simStop().catch(() => {});
    }
  }

  async function simAction(fn, label) {
    if (actionInFlight.current) return;
    const epoch = ++simEpoch.current;
    actionInFlight.current = true;
    setSimLocked(true);
    try {
      const v = await fn();
      if (epoch === simEpoch.current) {
        applySim(v);
        setSimError(null);
      }
    } catch (e) {
      if (epoch === simEpoch.current) setSimError(`${label} failed: ${e.message || e}`);
    } finally {
      if (epoch === simEpoch.current) {
        actionInFlight.current = false;
        setSimLocked(false);
      }
    }
  }

  const simActive = !!(sim && sim.active);
  useEffect(() => {
    if (!tracking || !simActive) return undefined;
    let alive = true;
    let inflight = false;
    const id = setInterval(async () => {
      if (inflight || actionInFlight.current) return;
      inflight = true;
      const epoch = simEpoch.current;
      try {
        const v = await api.simGet();
        if (!alive || epoch !== simEpoch.current) return;
        if (v && v.active) {
          applySim(v);
          setPollNote(null);
        } else {
          setPollNote("tracking poll failed: no active simulation on the server");
        }
      } catch (e) {
        // Keep the last view on screen; never blank the map.
        if (alive && epoch === simEpoch.current) setPollNote("tracking poll failed");
      } finally {
        inflight = false;
      }
    }, 1000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [tracking, simActive, applySim]);

  const liveSim = tracking && result && simRunId === result.run_id && sim && sim.active ? sim : null;

  // Voice note behind the result: the fixture's wav for saved-file runs, the recorded blob for live-mic runs.
  const resultFixtureInfo = result ? fixtures.find((f) => f.id === result.fixture) || null : null;
  const resultBlob = result && result.live && result.source === "mic" && mic ? mic.blob : null;
  const blobUrl = useMemo(() => (resultBlob ? URL.createObjectURL(resultBlob) : null), [resultBlob]);
  useEffect(() => () => blobUrl && URL.revokeObjectURL(blobUrl), [blobUrl]);
  let audioUrl = null;
  if (result && result.live) {
    if (result.source === "mic") audioUrl = blobUrl;
    else if (resultFixtureInfo) audioUrl = resultFixtureInfo.audio;
  }
  const fixtureKnown = fixtures.some((f) => f.id === fixtureId);
  const canSend = !running && fixtureKnown && (source === "file" || !!mic);

  return (
    <MotionConfig reducedMotion="user">
      <div className="app">
        <TopBar result={result} theme={theme} onToggleTheme={toggleTheme} />
        <div className="layout">
          <InputRail
            fixtures={fixtures}
            fixturesError={fixturesError}
            fixtureId={fixtureId}
            onFixture={setFixtureId}
            source={source}
            onSource={setSource}
            mic={mic}
            onMic={setMic}
            running={running}
            canSend={canSend}
            onSendLive={sendLive}
            onFake={sendFake}
            tracking={tracking}
            onToggleTracking={toggleTracking}
            sim={liveSim}
            simLocked={simLocked}
            simError={tracking ? simError : null}
            onAnswer={(accept) => simAction(() => api.simAnswer(accept), accept ? "Accept" : "Keep route")}
            onInject={(kind) => simAction(() => api.simInject(kind), "Inject")}
          />
          <main className="main">
            {error && (
              <div className="banner banner-error" role="alert">
                {error}
              </div>
            )}
            {result ? (
              <ResultView
                key={result.run_id}
                result={result}
                sim={liveSim}
                theme={theme}
                pollNote={pollNote}
                audioUrl={audioUrl}
                fixture={resultFixtureInfo}
              />
            ) : (
              <Pipeline running={running} startedAt={runStartedAt} />
            )}
          </main>
        </div>
      </div>
    </MotionConfig>
  );
}
