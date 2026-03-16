/**
 * 백엔드 API 클라이언트. base URL은 VITE_API_URL 환경 변수 사용.
 */

const baseURL = typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL
  ? import.meta.env.VITE_API_URL
  : (typeof process !== 'undefined' && process.env?.VITE_API_URL) || 'http://localhost:8080'

function url(path) {
  const p = path.startsWith('/') ? path : `/${path}`
  return `${baseURL.replace(/\/$/, '')}${p}`
}

/**
 * API 오류 응답(400/404/422 등)에서 사용자에게 보여줄 메시지 추출.
 * @param {Error} err - api get/post/put/del에서 throw된 오류
 * @returns {string}
 */
export function getApiErrorMessage(err) {
  if (!err) return '오류가 발생했습니다.'
  const body = err.body || {}
  const msg = body.message || err.message || '요청에 실패했습니다.'
  if (body.details && Array.isArray(body.details) && body.details.length > 0) {
    const detail = body.details[0]
    const loc = (detail.loc || []).filter(Boolean).join('.')
    if (loc) return `${msg} (${loc})`
  }
  return msg
}

async function handleResponse(res) {
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const msg = data.message || res.statusText || 'Request failed'
    const err = new Error(msg)
    err.status = res.status
    err.body = data
    throw err
  }
  return data
}

export async function get(path, options = {}) {
  const res = await fetch(url(path), {
    method: 'GET',
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  return handleResponse(res)
}

export async function post(path, body, options = {}) {
  const res = await fetch(url(path), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...options.headers },
    body: body != null ? JSON.stringify(body) : undefined,
    ...options,
  })
  return handleResponse(res)
}

export async function put(path, body, options = {}) {
  const res = await fetch(url(path), {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...options.headers },
    body: body != null ? JSON.stringify(body) : undefined,
    ...options,
  })
  return handleResponse(res)
}

export async function del(path, options = {}) {
  const res = await fetch(url(path), {
    method: 'DELETE',
    headers: { ...options.headers },
    ...options,
  })
  if (res.status === 204) return undefined
  return handleResponse(res)
}

export { baseURL }
