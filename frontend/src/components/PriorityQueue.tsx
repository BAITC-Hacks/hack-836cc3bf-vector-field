import type { EntityListResponse, Gid, Role } from '@shared/contracts'
import { formatScore } from '../data/format'
import { ROLES, type Async } from '../data'
import { ROLE_COLORS, ROLE_LABELS } from '../data/labels'
import { EmptyBlock, ErrorBlock, LoadingBlock } from './States'

export type SeedFilter = 'all' | 'seed' | 'non-seed'

interface Props {
  state: Async<EntityListResponse>
  selectedGid: Gid | null
  onSelect(gid: Gid): void
  roleFilter: Role | 'all'
  onRoleFilter(value: Role | 'all'): void
  seedFilter: SeedFilter
  onSeedFilter(value: SeedFilter): void
  /** Size of the whole fixture collection, taken from summary.counts. */
  fixtureTotal: number
}

const ROLE_CHIPS: { value: Role | 'all'; label: string }[] = [
  { value: 'all', label: 'Все роли' },
  ...ROLES.map((role) => ({ value: role as Role | 'all', label: ROLE_LABELS[role] })),
]

const SEED_CHIPS: { value: SeedFilter; label: string }[] = [
  { value: 'all', label: 'Все' },
  { value: 'seed', label: 'Только seed' },
  { value: 'non-seed', label: 'Без seed' },
]

export function PriorityQueue({
  state,
  selectedGid,
  onSelect,
  roleFilter,
  onRoleFilter,
  seedFilter,
  onSeedFilter,
  fixtureTotal,
}: Props) {
  return (
    <section className="panel panel-queue">
      <div className="panel-head">
        <h2 className="panel-title">Очередь приоритетов</h2>
        <span className="panel-sub">роль · priority · why</span>
      </div>

      <div className="filters" role="group" aria-label="Фильтры очереди">
        <div className="chips chips-clickable">
          {ROLE_CHIPS.map((chip) => (
            <button
              key={chip.value}
              type="button"
              className={`chip ${roleFilter === chip.value ? 'is-on' : ''}`}
              onClick={() => onRoleFilter(chip.value)}
            >
              {chip.label}
            </button>
          ))}
        </div>
        <div className="chips chips-clickable">
          {SEED_CHIPS.map((chip) => (
            <button
              key={chip.value}
              type="button"
              className={`chip ${seedFilter === chip.value ? 'is-on' : ''}`}
              onClick={() => onSeedFilter(chip.value)}
            >
              {chip.label}
            </button>
          ))}
        </div>
        <p className="hint hint-warning">
          Фильтры применяются только к fixture-коллекции из {fixtureTotal} узлов. Это не поиск по полной сети кейса
          (2248 узлов): полный список и фильтры всей сети даст <code>GET /api/entities</code>.
        </p>
      </div>

      {state.status === 'idle' || state.status === 'loading' ? (
        <LoadingBlock label="Загрузка очереди…" />
      ) : state.status === 'error' ? (
        <ErrorBlock title="Очередь недоступна" error={state.error} />
      ) : state.data.items.length === 0 ? (
        <EmptyBlock title="Ни один узел не подходит под фильтр">
          Под выбранные фильтры не попал ни один из {state.data.total} fixture-узлов. Снимите фильтр, чтобы увидеть
          очередь целиком.
        </EmptyBlock>
      ) : (
        <>
          <p className="count-line">
            показано {state.data.items.length} из {state.data.total} fixture-узлов
          </p>
          <ol className="queue">
            {state.data.items.map((item) => (
              <li key={item.gid}>
                <button
                  type="button"
                  className={`qrow ${item.gid === selectedGid ? 'is-selected' : ''}`}
                  onClick={() => onSelect(item.gid)}
                >
                  <span className="qrow-gid" title={item.gid}>
                    {item.gid}
                    {item.is_seed ? <span className="badge badge-seed">seed</span> : null}
                    {item.depth === 4 ? <span className="badge badge-boundary">depth 4</span> : null}
                  </span>

                  <span className="qrow-role">
                    <span className="dot" style={{ backgroundColor: ROLE_COLORS[item.role] }} aria-hidden="true" />
                    <span>{ROLE_LABELS[item.role]}</span>
                    <code className="qrow-enum">{item.role}</code>
                  </span>

                  <span className="qrow-priority">
                    <span className="qrow-score">{formatScore(item.priority_score)}</span>
                    <span className="qrow-score-label">priority, баллы</span>
                    <span className="bar" aria-hidden="true">
                      <span style={{ width: `${Math.round(item.priority_score * 100)}%` }} />
                    </span>
                  </span>

                  <span className="qrow-why" title={item.why}>
                    {item.why}
                  </span>
                </button>
              </li>
            ))}
          </ol>
        </>
      )}
    </section>
  )
}
