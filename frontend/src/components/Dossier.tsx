import { useState, type ReactNode } from 'react'
import type { Entity, EntityResponse } from '@shared/contracts'
import { formatKzt, formatScore } from '../data/format'
import { isKnownLimitation, limitationLabel } from '../data/limitations'
import { DEPTH4_NOTE, ISOLATE_NOTE, ROLE_COLORS, ROLE_LABELS, ROLE_NOTES } from '../data/labels'
import type { Async } from '../data/useAsyncData'
import { EmptyBlock, LoadingBlock, StateBlock } from './States'

const PRIORITY_FEATURE_LABELS: Record<string, string> = {
  priority_component_direct_seed_senders: 'связь с seed: прямые seed-отправители',
  priority_component_seed_reach_4: 'связь с seed: достижимость ≤ 4 хопов',
  priority_component_in_degree: 'входящая степень',
  priority_component_flow_volume: 'наблюдаемый объём потока',
  priority_component_betweenness: 'betweenness направленного графа',
  priority_component_out_degree: 'исходящая степень',
}

// role_score_cap is conditional: the pipeline emits it only for a single observed transaction.
const ROLE_DECOMPOSITION_METRICS = ['role_signal_strength', 'role_support_multiplier']

function featureLabel(metric: string): string {
  return PRIORITY_FEATURE_LABELS[metric] ?? metric
}

function renderValue(value: number | string | null): string {
  return value === null ? '—' : String(value)
}

function Section({ title, children, note }: { title: string; children: ReactNode; note?: ReactNode }) {
  return (
    <section className="dossier-section">
      <h3 className="dossier-section-title">{title}</h3>
      {children}
      {note ? <p className="hint">{note}</p> : null}
    </section>
  )
}

interface Props {
  state: Async<EntityResponse | null>
}

export function Dossier({ state }: Props) {
  const [copied, setCopied] = useState(false)

  if (state.status === 'idle' || state.status === 'loading') {
    return <LoadingBlock label="Загрузка карточки…" />
  }
  if (state.status === 'error') {
    return (
      <StateBlock
        title={state.error.code === 'ENTITY_NOT_FOUND' ? 'Карточка недоступна' : 'Ошибка загрузки карточки'}
        error={state.error}
        hint="Dossier другого узла не подставляется: карточка всегда строится ровно для запрошенного gid."
      />
    )
  }
  if (state.data === null) {
    return (
      <EmptyBlock title="Узел не выбран">
        Выберите узел в очереди или найдите его по точному gid — карточка откроется для него одного.
      </EmptyBlock>
    )
  }

  const entity: Entity = state.data.entity
  const priorityFacts = entity.evidence.filter((fact) => fact.rule_id === 'priority_v0')
  const roleFacts = entity.evidence.filter((fact) => fact.rule_id !== 'priority_v0')

  const allNumeric = priorityFacts.every((fact) => typeof fact.value === 'number')
  const prioritySum = allNumeric
    ? priorityFacts.reduce<number>((total, fact) => total + (fact.value as number), 0)
    : null
  const delta = prioritySum === null ? null : Math.abs(prioritySum - entity.priority_score)

  const missingDecomposition = ROLE_DECOMPOSITION_METRICS.filter(
    (metric) => !roleFacts.some((fact) => fact.metric === metric),
  )
  const isBoundary = entity.depth === 4
  const isIsolate = entity.limitations.includes('isolated_seed')

  async function copyGid() {
    try {
      await navigator.clipboard.writeText(entity.gid)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1500)
    } catch {
      setCopied(false)
    }
  }

  return (
    <article className="dossier">
      <header className="dossier-head">
        <div className="dossier-gidline">
          <code className="dossier-gid">{entity.gid}</code>
          <button className="btn btn-tiny" type="button" onClick={copyGid}>
            {copied ? 'скопирован' : 'копировать gid'}
          </button>
        </div>
        <div className="badges">
          {entity.is_seed ? <span className="badge badge-seed">seed</span> : null}
          <span className="badge">depth {entity.depth}</span>
          {isBoundary ? <span className="badge badge-boundary">граница обхода</span> : null}
          {isIsolate ? <span className="badge badge-isolate">изолят</span> : null}
          <span className="badge">cluster {entity.cluster_id}</span>
        </div>
        {isBoundary ? <p className="dossier-warning">{DEPTH4_NOTE}</p> : null}
        {isIsolate ? <p className="dossier-warning">{ISOLATE_NOTE}</p> : null}
      </header>

      {/* ── 1. Почему роль ─────────────────────────────────────────────── */}
      <Section
        title="Почему роль"
        note="role_score — эвристическая уверенность по правилам v0, а не откалиброванная вероятность истинной роли."
      >
        <div className="score-block">
          <div className="score-main">
            <span className="dot" style={{ backgroundColor: ROLE_COLORS[entity.role] }} aria-hidden="true" />
            <span className="score-role-label">{ROLE_LABELS[entity.role]}</span>
            <code className="qrow-enum">{entity.role}</code>
          </div>
          <div className="score-value">
            <span className="score-number">{formatScore(entity.role_score)}</span>
            <span className="score-caption">role_score, баллы 0..1 — не процент и не вероятность</span>
          </div>
          <p className="dossier-note">{ROLE_NOTES[entity.role]}</p>
        </div>

        <p className="dossier-evidence-text">{entity.evidence_text}</p>

        <p className="sub-label">
          Вторичные признаки ролей: {entity.secondary_roles.length > 0 ? '' : 'нет'}
        </p>
        {entity.secondary_roles.length > 0 ? (
          <ul className="chips">
            {entity.secondary_roles.map((role) => (
              <li className="chip" key={role}>
                {ROLE_LABELS[role]} <code>{role}</code>
              </li>
            ))}
          </ul>
        ) : null}

        {roleFacts.length === 0 ? (
          <p className="no-data">Детальные основания роли не переданы. Оценка из snapshot не пересчитывается в интерфейсе.</p>
        ) : (
          <ul className="fact-list">
            {roleFacts.map((fact) => (
              <li key={fact.evidence_id}>
                <div className="fact-head">
                  <code>{fact.metric}</code>
                  <strong>{renderValue(fact.value)}</strong>
                  <span className="fact-unit">{fact.unit}</span>
                  <code className="fact-rule">{fact.rule_id}</code>
                </div>
                <p>{fact.text}</p>
              </li>
            ))}
          </ul>
        )}

        {missingDecomposition.length > 0 ? (
          <p className="no-data">
            Для разложения role_score не переданы {missingDecomposition.join(', ')}. Интерфейс не восполняет эти значения.
          </p>
        ) : null}
      </Section>

      {/* ── 2. Почему приоритет ────────────────────────────────────────── */}
      <Section
        title="Почему приоритет"
        note="priority_score — баллы приоритета дальнейшей проверки в этом деле. Это не вероятность преступления и не риск."
      >
        <div className="score-block score-block-priority">
          <div className="score-value">
            <span className="score-number">{formatScore(entity.priority_score)}</span>
            <span className="score-caption">priority_score, баллы 0..1</span>
          </div>
          <p className="dossier-note">{entity.why}</p>
        </div>

        <p className="sub-label">Вклады priority_v0 (приходят из snapshot, в React не пересчитываются)</p>

        {priorityFacts.length === 0 ? (
          <p className="no-data">
            Вклады приоритета не переданы. Показаны оценка и объяснение из snapshot; разложение не восстанавливается в интерфейсе.
          </p>
        ) : (
          <>
            <ul className="fact-list">
              {priorityFacts.map((fact) => (
                <li key={fact.evidence_id}>
                  <div className="fact-head">
                    <code>{fact.metric}</code>
                    <strong>{renderValue(fact.value)}</strong>
                    <span className="fact-unit">{fact.unit}</span>
                    <code className="fact-rule">{fact.rule_id}</code>
                  </div>
                  <p>{featureLabel(fact.metric)}</p>
                </li>
              ))}
            </ul>
            <p className="sum-line">
              Сумма вкладов: <strong>{prioritySum === null ? 'нечисловые значения' : formatScore(prioritySum)}</strong>{' '}
              · priority_score <strong>{formatScore(entity.priority_score)}</strong>{' '}
              {delta === null ? (
                <span className="no-data">· сверка недоступна</span>
              ) : delta <= 1e-9 ? (
                <span className="sum-ok">· совпадает (допуск 1e-9)</span>
              ) : (
                <span className="sum-bad">· расхождение {delta}</span>
              )}
            </p>
          </>
        )}
      </Section>

      {/* ── 3. Потоки и признаки ───────────────────────────────────────── */}
      <Section
        title="Потоки и признаки"
        note="Метрики рассчитаны по всей наблюдаемой сети и приходят от backend. Они НЕ пересчитываются по показанному ego-графу, который часто урезан."
      >
        <dl className="metrics">
          <div>
            <dt>Входящая степень</dt>
            <dd>{entity.metrics.in_degree}</dd>
          </div>
          <div>
            <dt>Исходящая степень</dt>
            <dd>{entity.metrics.out_degree}</dd>
          </div>
          <div>
            <dt>Вход</dt>
            <dd>{formatKzt(entity.metrics.in_kzt)}</dd>
          </div>
          <div>
            <dt>Выход</dt>
            <dd>{formatKzt(entity.metrics.out_kzt)}</dd>
          </div>
          <div>
            <dt>Входящих операций</dt>
            <dd>{entity.metrics.in_tx}</dd>
          </div>
          <div>
            <dt>Исходящих операций</dt>
            <dd>{entity.metrics.out_tx}</dd>
          </div>
          <div>
            <dt>Наблюдаемый out/in</dt>
            <dd className={entity.metrics.pass_through === null ? 'no-data-inline' : ''}>
              {entity.metrics.pass_through === null ? 'нет данных' : formatScore(entity.metrics.pass_through)}
            </dd>
          </div>
          <div>
            <dt>Прямые seed-отправители</dt>
            <dd>{entity.metrics.direct_seed_senders}</dd>
          </div>
          <div>
            <dt>Достижим от seed ≤4</dt>
            <dd>{entity.metrics.seed_reach_4}</dd>
          </div>
          <div>
            <dt>Betweenness</dt>
            <dd>{formatScore(entity.metrics.betweenness)}</dd>
          </div>
        </dl>
        <p className="hint">
          out/in не является бухгалтерским балансом и не означает долю тех же денег. Нулевой знаменатель даёт
          отсутствующий показатель, а не бесконечность.
        </p>
      </Section>

      {/* ── 4. Evidence ────────────────────────────────────────────────── */}
      <Section title={`Evidence — все факты (${entity.evidence.length})`}>
        {entity.evidence.length === 0 ? (
          <p className="no-data">Факты отсутствуют.</p>
        ) : (
          <div className="table-wrap">
            <table className="fact-table">
              <thead>
                <tr>
                  <th>metric</th>
                  <th>value</th>
                  <th>unit</th>
                  <th>rule_id</th>
                  <th>source</th>
                  <th>text</th>
                </tr>
              </thead>
              <tbody>
                {entity.evidence.map((fact) => (
                  <tr key={fact.evidence_id}>
                    <td>
                      <code>{fact.metric}</code>
                    </td>
                    <td className="num">{renderValue(fact.value)}</td>
                    <td>{fact.unit}</td>
                    <td>
                      <code>{fact.rule_id}</code>
                    </td>
                    <td>{fact.source}</td>
                    <td>{fact.text}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <details className="evidence-ids">
          <summary>ID фактов для проверки</summary>
          <p>{entity.evidence.map((fact) => fact.evidence_id).join(' · ') || '—'}</p>
        </details>
      </Section>

      {/* ── 5. Ограничения ─────────────────────────────────────────────── */}
      <Section
        title="Ограничения"
        note="Что мешает сильному выводу по этому узлу. Не декларативный disclaimer."
      >
        {entity.limitations.length === 0 ? (
          <p className="no-data">Ограничения не переданы.</p>
        ) : (
          <ul className="chips">
            {entity.limitations.map((code) => (
              <li className={`chip ${isKnownLimitation(code) ? '' : 'chip-unknown'}`} key={code} title={code}>
                {limitationLabel(code)}
              </li>
            ))}
          </ul>
        )}
      </Section>

      {/* ── 6. Next checks ─────────────────────────────────────────────── */}
      <Section title="Следующие проверки">
        {entity.next_checks.length === 0 ? (
          <p className="no-data">Следующие шаги не переданы.</p>
        ) : (
          <ul className="next-checks">
            {entity.next_checks.map((check) => (
              <li key={check}>{check}</li>
            ))}
          </ul>
        )}
      </Section>
    </article>
  )
}
