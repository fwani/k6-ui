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
  if (engine === 'browser') return 'pill pill-browser'
  if (engine === 'db') return 'pill pill-db'
  return 'pill pill-k6'
}

/** @param {string | undefined | null} engine */
export function engineLabelShort(engine) {
  if (engine === 'browser') return '브라우저'
  if (engine === 'db') return 'DB'
  return 'HTTP'
}
