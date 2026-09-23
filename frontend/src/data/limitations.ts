/** Limitation code dictionary (docs/API_CONTRACT.md «Коды limitations v1»).
 * Unknown codes are rendered verbatim and never crash the UI. */

export const LIMITATION_LABELS: Readonly<Record<string, string>> = {
  inflow_incomplete: 'Входящие за пределами наблюдаемой сети неизвестны',
  depth_truncated: 'Исходящие ограничены глубиной обхода',
  seed_inflow_incomplete: 'Выборка собрана от seed; вход особенно неполон',
  outflow_exceeds_observed_inflow: 'Выход превышает наблюдаемый вход; полный баланс неизвестен',
  isolated_seed: 'У исходного участника нет наблюдаемых связей',
  insufficient_evidence: 'Недостаточно признаков для уверенной роли',
  date_only: 'Внутридневной порядок операций неизвестен',
  period_censored: 'Операции за пределами июля неизвестны',
  threshold_5000: 'Переводы менее 5000 KZT не наблюдаются',
  intrabank_only: 'Наблюдаются только внутрибанковские переводы',
  path_not_money_provenance: 'Структурный путь не доказывает движение тех же средств',
  subgraph_truncated: 'Показана часть окружения',
}

export function limitationLabel(code: string): string {
  return LIMITATION_LABELS[code] ?? code
}

export function isKnownLimitation(code: string): boolean {
  return Object.prototype.hasOwnProperty.call(LIMITATION_LABELS, code)
}
