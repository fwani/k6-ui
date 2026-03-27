/** @param {string | undefined | null} status */
export function statusPillClass(status) {
  const s = (status || '').toLowerCase()
  if (s === 'running') return 'pill pill-running'
  if (s === 'failed') return 'pill pill-error'
  if (s === 'finished') return 'pill pill-finished'
  return 'pill pill-idle'
}

/** @param {string | undefined | null} engine */
export function enginePillClass(engine) {
  return engine === 'browser' ? 'pill pill-browser' : 'pill pill-k6'
}
