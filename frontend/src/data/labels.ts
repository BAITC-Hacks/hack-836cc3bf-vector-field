/** User-facing labels.
 *
 * Role wording is taken from docs/DECISIONS.md D-04: the transport enum stays
 * `coordinator`, the displayed label is «Структурный посредник (кандидат)».
 */
import type { Role } from '@shared/contracts'

export const ROLE_LABELS: Record<Role, string> = {
  consolidator: 'Консолидация',
  transit: 'Транзит — гипотеза',
  distributor: 'Распределение',
  terminal: 'Конечный получатель — гипотеза',
  coordinator: 'Структурный посредник (кандидат)',
  peripheral: 'Недостаточно признаков роли',
}

/** Mandatory caveat per role (BUILD_BRIEF стартовая спецификация, D-04). */
export const ROLE_NOTES: Record<Role, string> = {
  consolidator:
    'Схождение переводов от разных gid; это не доказательство накопления остатка.',
  distributor:
    'Наблюдаемый веерный выход; назначение получателей и тип деятельности неизвестны.',
  transit:
    'Сходство объёмов входа и выхода; без внутридневных дат сквозное движение тех же денег не установлено.',
  terminal:
    'Только кандидат в наблюдаемый конечный получатель: нет остатков и внешних переводов.',
  coordinator:
    'Значим для связности наблюдаемой сети; управление участниками не установлено.',
  peripheral:
    'Достаточных признаков заданных ролей не выявлено. Это не утверждение о низком AML-риске.',
}

/** Role colours. Meaning is never carried by colour alone: every surface also
 * prints the role text (queue row, dossier, legend, node tooltip). */
export const ROLE_COLORS: Record<Role, string> = {
  consolidator: '#38bdf8',
  transit: '#a78bfa',
  distributor: '#34d399',
  terminal: '#fbbf24',
  coordinator: '#f472b6',
  peripheral: '#94a3b8',
}

export const DEPTH4_NOTE =
  'Depth=4 — граница обхода выгрузки. Исходящие переводы следующего колена не наблюдаются. Это ограничение наблюдения, а не признак оседания или отмывания средств.'

export const ISOLATE_NOTE =
  'Узел включён в очередь, но наблюдаемых связей в выборке нет. Приоритет 0 по наблюдаемой сети — это data-gap, а не отсутствие подозрений.'
