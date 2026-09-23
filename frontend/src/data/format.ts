/** Display helpers. gid is handled exclusively as a string. */

/** Ordering identical to integer ordering for non-negative decimal integers
 * without leading zeros, but exact and without any numeric conversion.
 * Used for the contract sort "priority DESC, gid ASC". */
export function compareGidAsc(a: string, b: string): number {
  if (a.length !== b.length) return a.length - b.length
  if (a === b) return 0
  return a < b ? -1 : 1
}

/** Visual truncation only — the full gid stays searchable and copyable. */
export function shortGid(gid: string, tail = 6): string {
  if (gid.length <= tail + 1) return gid
  return `…${gid.slice(-tail)}`
}

const moneyFmt = new Intl.NumberFormat('ru-RU', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

export function formatKzt(value: number): string {
  return `${moneyFmt.format(value)} ₸`
}

export function formatCount(value: number): string {
  return new Intl.NumberFormat('ru-RU').format(value)
}

/** Scores stay 0..1 exactly as in API/CSV. Never rendered as a percentage. */
export function formatScore(value: number): string {
  return value.toFixed(4)
}
