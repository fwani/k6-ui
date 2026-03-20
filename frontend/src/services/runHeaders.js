/**
 * 테스트 목록에서 설정하는 "다음 실행에 붙일 헤더". 브라우저 저장만 (DB 없음).
 */
const KEY = 'graphioPerf.runHeaders.v1'

function writeStorage(useLocal, data) {
  const s = JSON.stringify(data)
  if (useLocal) {
    localStorage.setItem(KEY, s)
    try {
      sessionStorage.removeItem(KEY)
    } catch {
      /* ignore */
    }
  } else {
    sessionStorage.setItem(KEY, s)
    try {
      localStorage.removeItem(KEY)
    } catch {
      /* ignore */
    }
  }
}

export function loadRunHeadersForm() {
  let parsed = null
  let persist = false
  try {
    const ls = localStorage.getItem(KEY)
    if (ls) {
      parsed = JSON.parse(ls)
      persist = true
    }
  } catch {
    /* ignore */
  }
  if (!parsed) {
    try {
      const ss = sessionStorage.getItem(KEY)
      if (ss) {
        parsed = JSON.parse(ss)
        persist = false
      }
    } catch {
      /* ignore */
    }
  }
  if (!parsed || typeof parsed !== 'object') {
    return {
      bearer: '',
      extras: [{ key: '', value: '' }],
      persist: false,
    }
  }
  const extras = Array.isArray(parsed.extras) ? parsed.extras : []
  return {
    bearer: typeof parsed.bearer === 'string' ? parsed.bearer : '',
    extras:
      extras.length > 0
        ? extras.map((r) => ({
            key: r && r.key != null ? String(r.key) : '',
            value: r && r.value != null ? String(r.value) : '',
          }))
        : [{ key: '', value: '' }],
    persist,
  }
}

export function saveRunHeadersForm({ bearer, extras, persist }) {
  writeStorage(Boolean(persist), {
    bearer: bearer != null ? String(bearer) : '',
    extras: Array.isArray(extras) ? extras : [],
  })
}

export function clearRunHeadersForm() {
  try {
    sessionStorage.removeItem(KEY)
    localStorage.removeItem(KEY)
  } catch {
    /* ignore */
  }
}

/** POST /tests/:id/runs 용. 빈 객체면 실행 시 헤더 없음. */
export function getRunHeaderOverridesForApi() {
  const { bearer, extras } = loadRunHeadersForm()
  const out = {}
  const b = (bearer || '').trim()
  if (b) {
    out.Authorization = b.toLowerCase().startsWith('bearer ') ? b : `Bearer ${b}`
  }
  for (const row of extras || []) {
    const k = (row.key || '').trim()
    if (!k) continue
    out[k] = row.value != null ? String(row.value) : ''
  }
  return out
}
