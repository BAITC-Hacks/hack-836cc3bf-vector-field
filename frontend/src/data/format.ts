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
export function formatScore(value: number, digits = 4): string {
  return value.toFixed(digits)
}

/** Translate known feature labels only; preserve supplied facts and numbers. */
export function readableWhy(text: string): string {
  const labels: Record<string, string> = {
    direct_seed_senders: 'прямые отправители из seed',
    seed_reach_4: 'достижимость от seed',
    in_degree: 'число отправителей',
    flow_volume: 'объём переводов',
    betweenness: 'положение на путях в сети',
    out_degree: 'число получателей',
  }
  return text.replace(/\b(direct_seed_senders|seed_reach_4|in_degree|flow_volume|betweenness|out_degree)\b/g, (metric) => labels[metric])
}
