import { memo, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { reveal } from "../motion.js";
import { fmtMmss, fmtNum, reasonLines } from "../format.js";

const PriorityTile = memo(function PriorityTile({ priority, reasons }) {
  const key = String(priority || "").toLowerCase();
  return (
    <motion.div className="tile-wrap" variants={reveal.tile}>
      <div className={`tile tile-${key}`}>
        <AnimatePresence mode="wait" initial={false}>
          <motion.span
            key={priority}
            className="tile-letter"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.15 }}
          >
            {priority}
          </motion.span>
        </AnimatePresence>
      </div>
      <div className="why">
        <span className="why-label">Why</span>
        <ul className="why-list">
          {reasonLines(reasons).map((line, i) => (
            <li key={`${i}-${line}`}>{line}</li>
          ))}
        </ul>
      </div>
    </motion.div>
  );
});

// Ticks are local to this run: the result view is keyed on run_id, so a new run starts unticked.
const Checklist = memo(function Checklist({ items }) {
  const [done, setDone] = useState({});
  return (
    <div className="prep">
      <h2 className="section-label">Prepare for</h2>
      <motion.ul className="checklist" variants={reveal.list}>
        {items.map((item, i) => (
          <motion.li key={`${i}-${item}`} variants={reveal.item} className={done[i] ? "is-done" : ""}>
            <label>
              <input
                type="checkbox"
                checked={!!done[i]}
                onChange={() => setDone((d) => ({ ...d, [i]: !d[i] }))}
              />
              <span>{item}</span>
            </label>
          </motion.li>
        ))}
      </motion.ul>
    </div>
  );
});

function LeadTime({ fields, etaGap, sim }) {
  const eta = fields.eta_min;
  const quote = fields.evidence ? fields.evidence.eta_min : null;

  if (!sim) {
    return (
      <motion.div className="lead" variants={reveal.fade(0.28)}>
        <div className="section-label">Prep lead time</div>
        <div className="lead-number">{eta != null ? `${fmtNum(eta)} min` : "unknown (no ETA heard)"}</div>
        <p className="caption">The checklist exists before the patient arrives, so prep starts one ETA earlier.</p>
      </motion.div>
    );
  }

  const routeEta = sim.halted ? null : sim.route_eta_min;
  let countdown;
  if (sim.halted) countdown = "Arrival unknown";
  else if (sim.position && sim.position.arrived) countdown = "Arrived (simulated)";
  else countdown = `Arrives in ${fmtMmss(sim.remaining_min || 0)}`;
  const spoken = eta != null ? `${fmtNum(eta)} min` : "not heard";
  const gap = routeEta != null && eta != null && Math.abs(routeEta - eta) > etaGap;

  return (
    <motion.div className="lead" variants={reveal.fade(0.28)}>
      <div className="section-label">Prep lead time</div>
      <div className="lead-number">{routeEta != null ? `${fmtNum(routeEta)} min` : "unknown"}</div>
      <p className="caption">Uses the {routeEta != null ? "route ETA (simulated)" : "no open route"}.</p>
      <div className="countdown">{countdown}</div>
      {sim.status && <div className="simstatus">{sim.status}</div>}
      <p className="mono spoken">
        Spoken ETA: {spoken}
        {quote ? ` — “${quote}”` : ""}
      </p>
      {gap && (
        <p className="gap">
          Route ETA {fmtNum(routeEta)} min · spoken ETA {fmtNum(eta)} min (differ by more than {etaGap} min)
        </p>
      )}
    </motion.div>
  );
}

export default function Hero({ result, sim }) {
  const { plan, fields } = result;
  return (
    <section className="hero">
      <PriorityTile priority={plan.priority} reasons={plan.reasons} />
      <Checklist items={plan.prepare_for} />
      <LeadTime fields={fields} etaGap={result.eta_gap_min} sim={sim} />
    </section>
  );
}
