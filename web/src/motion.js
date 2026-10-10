// Shared reveal variants. The result view is keyed on run_id, so these play once per run and never on poll ticks.
export const reveal = {
  container: { hidden: {}, show: {} },
  tile: {
    hidden: { opacity: 0, scale: 0.92 },
    show: {
      opacity: 1,
      scale: 1,
      transition: { type: "spring", stiffness: 520, damping: 32, opacity: { duration: 0.12 } },
    },
  },
  list: { hidden: {}, show: { transition: { delayChildren: 0.1, staggerChildren: 0.06 } } },
  item: { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.24, ease: "easeOut" } } },
  fade: (delay) => ({
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { duration: 0.3, delay } },
  }),
};

export const press = { whileHover: { scale: 1.01 }, whileTap: { scale: 0.98 } };
