import type { Gid } from '@shared/contracts'

export interface Scenario {
  key: string
  label: string
  /** null = соответствующий узел в fixture не найден, кнопка выключена. */
  gid: Gid | null
}

interface Props {
  scenarios: Scenario[]
  activeGid: Gid | null
  onSelect(gid: Gid): void
}

/** Requirement: every state promised by the fixture set must be reachable
 *  in one click. Nothing here hard-codes a gid — the targets are derived from
 *  summary.top_nodes by their own limitations/depth. */
export function FixtureScenarios({ scenarios, activeGid, onSelect }: Props) {
  return (
    <section className="panel">
      <h2 className="panel-title">Состояния fixture</h2>
      <p className="hint">Пять обещанных состояний контракта v1: обычная карточка, изолят, depth=4, урезанное окружение, ENTITY_NOT_FOUND.</p>
      <div className="scenarios">
        {scenarios.map((scenario) => (
          <button
            key={scenario.key}
            type="button"
            className={`btn btn-wide ${scenario.gid !== null && scenario.gid === activeGid ? 'is-active' : ''}`}
            disabled={scenario.gid === null}
            onClick={() => {
              if (scenario.gid !== null) onSelect(scenario.gid)
            }}
            title={scenario.gid ?? 'В fixture нет подходящего узла'}
          >
            {scenario.label}
            <span className="scenario-gid">{scenario.gid ?? '—'}</span>
          </button>
        ))}
      </div>
    </section>
  )
}
