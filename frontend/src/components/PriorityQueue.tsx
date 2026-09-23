import type { EntityListResponse, Gid, Role } from '@shared/contracts'
import { formatScore, readableWhy } from '../data/format'
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
  totalNodes: number
  mode: 'fixture' | 'live'
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
  totalNodes,
  mode,
}: Props) {
  return (
    <section className="panel panel-queue">
      <div className="panel-head">
        <h2 className="panel-title">Кого проверить</h2>
        <span className="panel-sub">по приоритету ↓</span>
      </div>

      <details className="filters">
        <summary>Фильтры{roleFilter !== 'all' || seedFilter !== 'all' ? ' · применены' : ' · все узлы'}</summary>
        <div className="chips chips-clickable">
          {ROLE_CHIPS.map((chip) => (
            <button
              key={chip.value}
              type="button"
              className={`chip ${roleFilter === chip.value ? 'is-on' : ''}`}
              aria-pressed={roleFilter === chip.value}
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
              aria-pressed={seedFilter === chip.value}
              onClick={() => onSeedFilter(chip.value)}
            >
              {chip.label}
            </button>
          ))}
        </div>
        {mode === 'fixture' ? <p className="hint hint-warning">
          Фильтры применяются только к учебной коллекции из {totalNodes} узлов.
        </p> : <p className="hint">По всей сети из {totalNodes} узлов. Seed — исходный узел сбора данных.</p>}
      </details>

      {state.status === 'idle' || state.status === 'loading' ? (
        <LoadingBlock label="Загрузка очереди…" />
      ) : state.status === 'error' ? (
        <ErrorBlock title="Очередь недоступна" error={state.error} />
      ) : state.data.items.length === 0 ? (
        <EmptyBlock title="Ни один узел не подходит под фильтр">
          Под выбранные фильтры не попал ни один из {state.data.total} узлов. Снимите фильтр, чтобы увидеть
          очередь целиком.
        </EmptyBlock>
      ) : (
        <>
          <p className="count-line">
            Первые {state.data.items.length} из {state.data.total} · баллы от 0 до 1
          </p>
          <ol className="queue">
            {state.data.items.map((item, index) => (
              <li key={item.gid}>
                <button
                  type="button"
                  className={`qrow ${item.gid === selectedGid ? 'is-selected' : ''}`}
                  aria-pressed={item.gid === selectedGid}
                  onClick={() => onSelect(item.gid)}
                >
                  <span className="qrow-position"><span>#{state.data.offset + index + 1}{roleFilter !== 'all' || seedFilter !== 'all' ? ' в выборке' : ''}</span><span>{item.gid === selectedGid ? 'Выбран →' : 'Открыть →'}</span></span>
                  <span className="qrow-gid" title={item.gid}>
                    {item.gid}
                  </span>

                  <span className="qrow-role">
                    <span className="dot" style={{ backgroundColor: ROLE_COLORS[item.role] }} aria-hidden="true" />
                    <span>{ROLE_LABELS[item.role]}</span>
                    {item.is_seed ? <span className="badge badge-seed" title="Исходный узел сбора сети">seed</span> : null}
                    {item.depth === 4 ? <span className="badge badge-boundary">граница</span> : null}
                  </span>

                  <span className="qrow-priority">
                    <span className="qrow-score">{formatScore(item.priority_score, 2)}</span>
                    <span className="qrow-score-label">приоритет проверки</span>
                    <span className="bar" aria-hidden="true">
                      <span style={{ width: `${Math.round(item.priority_score * 100)}%` }} />
                    </span>
                  </span>

                  <span className="qrow-why" title={readableWhy(item.why)}>
                    {readableWhy(item.why)}
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
