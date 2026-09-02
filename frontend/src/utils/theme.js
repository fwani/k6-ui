const STORAGE_KEY = 'theme'

/** @returns {'dark' | 'light'} */
export function getStoredTheme() {
  if (typeof localStorage === 'undefined') return 'dark'
  const raw = localStorage.getItem(STORAGE_KEY) ?? 'dark'
  if (raw === 'light' || raw === 'lightTheme') return 'light'
  return 'dark'
}

/** Syncs `html[data-theme]`. Call before mount. */
export function initTheme() {
  const t = getStoredTheme()
  document.documentElement.dataset.theme = t
  if (typeof localStorage !== 'undefined') {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw === 'darkTheme' || raw === 'lightTheme') {
      localStorage.setItem(STORAGE_KEY, t)
    }
  }
  return t
}

export function toggleTheme() {
  const html = document.documentElement
  const next = html.dataset.theme === 'dark' ? 'light' : 'dark'
  html.dataset.theme = next
  localStorage.setItem(STORAGE_KEY, next)
  return next
}
