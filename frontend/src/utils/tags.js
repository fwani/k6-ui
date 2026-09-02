/** 백엔드 normalize_tag_list 와 동일: trim, 32자, 최대 32개, 중복 제거 */
export function normalizeTagList(arr) {
  const seen = new Set()
  const out = []
  for (const s of arr || []) {
    const t = String(s || '').trim().slice(0, 32)
    if (!t || seen.has(t)) continue
    seen.add(t)
    out.push(t)
    if (out.length >= 32) break
  }
  return out
}

const TAG_COLOR_N = 8

/** 태그 문자열 → 0‥N-1 (항상 동일). UiChip color `tag-${i}` 와 함께 쓰면 된다. */
export function tagColorIndex(tag) {
  const s = String(tag ?? '').trim()
  let h = 2166136261
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return Math.abs(h) % TAG_COLOR_N
}

/** UiChip `:color` 값 — 같은 태그 이름이면 항상 같은 색 */
export function tagColorKey(tag) {
  return `tag-${tagColorIndex(tag)}`
}
