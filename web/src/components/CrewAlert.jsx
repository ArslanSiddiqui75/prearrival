import { AnimatePresence, motion } from "motion/react";
import Button from "./Button.jsx";

const ENTER = {
  opacity: 1,
  x: 0,
  boxShadow: ["0 0 0 0 rgba(178,106,0,0)", "0 0 0 6px rgba(178,106,0,0.35)", "0 0 0 0 rgba(178,106,0,0)"],
};
const ENTER_T = { duration: 0.25, ease: "easeOut", boxShadow: { duration: 0.6, delay: 0.15 } };
const EXIT = { opacity: 0, x: -12, transition: { duration: 0.2 } };

export default function CrewAlert({ sim, onAnswer, disabled }) {
  const show = !!(sim && sim.pending);
  return (
    <AnimatePresence initial={false}>
      {show && (
        <motion.section
          key="crew-alert"
          className="crew"
          role="alert"
          initial={{ opacity: 0, x: -12 }}
          animate={ENTER}
          exit={EXIT}
          transition={ENTER_T}
        >
          <h3 className="crew-title">Crew alert</h3>
          <p className="crew-text">{sim.alert}</p>
          <div className="crew-actions">
            <Button variant="primary" disabled={disabled} onClick={() => onAnswer(true)}>
              Accept
            </Button>
            <Button disabled={disabled} onClick={() => onAnswer(false)}>
              Keep route
            </Button>
          </div>
        </motion.section>
      )}
    </AnimatePresence>
  );
}
