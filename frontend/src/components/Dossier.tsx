import { useState, type ReactNode } from 'react'
import type { Entity, EntityResponse, Evidence } from '@shared/contracts'
import { formatCount, formatKzt, formatScore, readableWhy } from '../data/format'
import { limitationLabel } from '../data/limitations'
import { ROLE_COLORS, ROLE_LABELS, ROLE_NOTES } from '../data/labels'
import type { Async } from '../data/useAsyncData'
import { EmptyBlock, LoadingBlock, StateBlock } from './States'
import './Dossier.css'

const PRIORITY_FEATURE_LABELS: Record<string, string> = {
  priority_component_direct_seed_senders: 'Прямые переводы от исходных участников',
  priority_component_seed_reach_4: 'Достижимость от исходных участников',
  priority_component_in_degree: 'Количество отправителей',
  priority_component_flow_volume: 'Наблюдаемый объём переводов',
  priority_component_betweenness: 'Положение на путях в сети',
  priority_component_out_degree: 'Количество получателей',
}

function renderValue(value: number | string | null): string {
  return value === null ? '—' : String(value)
}

function Section({ title, children, note }: { title: string; children: ReactNode; note?: ReactNode }) {
  return <section className="dossier-section"><h3 className="dossier-section-title">{title}</h3>{children}{note ? <p className="hint">{note}</p> : null}</section>
}

function FactDetails({ facts }: { facts: Evidence[] }) {
  return <ul className="dossier-source-facts">{facts.map((fact) => (
    <li key={fact.evidence_id}>
      <p className="dossier-source-text">{fact.text}</p>
      <div className="dossier-source-value"><code>{fact.metric}</code><strong>{renderValue(fact.value)} {fact.unit}</strong></div>
      <dl>
        <div><dt>ID факта</dt><dd><code>{fact.evidence_id}</code></dd></div>
        <div><dt>Правило / источник</dt><dd>{fact.rule_id} · {fact.source}</dd></div>
        <div><dt>Область наблюдения</dt><dd>{fact.scope}</dd></div>
      </dl>
      {fact.limitations.length > 0 ? <p className="hint">{fact.limitations.map(limitationLabel).join(' · ')}</p> : null}
    </li>
  ))}</ul>
}

interface Props { state: Async<EntityResponse | null> }

export function Dossier({ state }: Props) {
  const [copiedGid, setCopiedGid] = useState<string | null>(null)
  if (state.status === 'idle' || state.status === 'loading') return <LoadingBlock label="Загрузка выбранного узла…" />
  if (state.status === 'error') return <StateBlock title={state.error.code === 'ENTITY_NOT_FOUND' ? 'Узел не найден' : 'Не удалось загрузить карточку'} error={state.error} hint="Проверьте полный GID в поиске. Карточка появится после успешной загрузки выбранного узла." />
  if (state.data === null) return <EmptyBlock title="Выберите узел">Нажмите на участника в очереди или найдите его по полному GID.</EmptyBlock>

  const entity: Entity = state.data.entity
  const priorityFacts = entity.evidence.filter((fact) => fact.rule_id === 'priority_v0')
  const roleFacts = entity.evidence.filter((fact) => fact.rule_id !== 'priority_v0')
  const allNumeric = priorityFacts.length > 0 && priorityFacts.every((fact) => typeof fact.value === 'number')
  // Verify supplied additive facts for display; never calculate a new priority.
  const prioritySum = allNumeric ? priorityFacts.reduce<number>((total, fact) => total + (fact.value as number), 0) : null
  const delta = prioritySum === null ? null : Math.abs(prioritySum - entity.priority_score)
  const rankedFacts = [...priorityFacts].sort((a, b) => typeof a.value === 'number' && typeof b.value === 'number' ? b.value - a.value : 0)
  const leadingFacts = rankedFacts.slice(0, 3)
  const otherContribution = allNumeric ? rankedFacts.slice(3).reduce<number>((total, fact) => total + (fact.value as number), 0) : null
  const isBoundary = entity.depth === 4
  const isIsolate = entity.limitations.includes('isolated_seed')

  async function copyGid() {
    try {
      await navigator.clipboard.writeText(entity.gid)
      setCopiedGid(entity.gid)
      window.setTimeout(() => setCopiedGid(null), 1500)
    } catch { setCopiedGid(null) }
  }

  return (
    <article className="dossier dossier-review">
      <header className="dossier-head">
        <p className="dossier-eyebrow">Выбранный участник</p>
        <div className="dossier-gidline">
          <code className="dossier-gid">{entity.gid}</code>
          <button className="btn btn-tiny" type="button" onClick={copyGid} aria-label="Скопировать полный GID">{copiedGid === entity.gid ? 'Скопирован' : 'Копировать'}</button>
        </div>
        <div className="badges">
          <span className="badge"><span className="dot" style={{ backgroundColor: ROLE_COLORS[entity.role] }} aria-hidden="true" />{ROLE_LABELS[entity.role]}</span>
          {entity.is_seed ? <span className="badge badge-seed" title="Участник, от которого начат сбор сети">Исходный участник · seed</span> : null}
          <span className="badge">Глубина {entity.depth}</span><span className="badge">Кластер {entity.cluster_id}</span>
        </div>
        {isBoundary ? <p className="dossier-warning"><strong>Граница наблюдения · глубина 4</strong>Исходящие переводы за пределами обхода неизвестны. Их отсутствие здесь не доказывает, что узел — конечный получатель.</p> : null}
        {isIsolate ? <p className="dossier-warning"><strong>Нет наблюдаемых связей</strong>Участник есть в исходной выборке, но переводы не наблюдаются. Приоритет отражает доступные признаки, а не отсутствие оснований для проверки.</p> : null}
      </header>

      <Section title="Почему проверить этот узел">
        <div className="dossier-priority-summary">
          <div className="dossier-priority-number"><strong title={`Точное значение: ${entity.priority_score}`}>{entity.priority_score.toFixed(2)}</strong><span>Приоритет проверки<br />баллы от 0 до 1</span></div>
          <p>{readableWhy(entity.why)}</p>
        </div>
        <p className="hint">Порядок дальнейшей проверки в этой выборке. Не вероятность нарушения.</p>
        {leadingFacts.length > 0 ? <>
          <p className="dossier-small-label">Главные вклады в приоритет</p>
          <ul className="dossier-contributions">
            {leadingFacts.map((fact) => <li key={fact.evidence_id}><span>{PRIORITY_FEATURE_LABELS[fact.metric] ?? fact.metric}</span><strong title={renderValue(fact.value)}>{typeof fact.value === 'number' ? formatScore(fact.value) : renderValue(fact.value)}</strong></li>)}
            {otherContribution !== null && rankedFacts.length > 3 ? <li className="dossier-contribution-other"><span>Прочие вклады · {rankedFacts.length - 3}</span><strong>{formatScore(otherContribution)}</strong></li> : null}
          </ul>
          <details className="dossier-details">
            <summary>Проверить расчёт приоритета · {priorityFacts.length} фактов</summary>
            <p className="hint">Вклады рассчитаны по всей наблюдаемой сети. Фильтры и размер графа не изменяют оценку.</p>
            <p className="sum-line">Сумма вкладов: <strong>{prioritySum === null ? 'недоступна' : formatScore(prioritySum)}</strong> · приоритет: <strong>{formatScore(entity.priority_score)}</strong>{' '}
              {delta === null ? <span>· сверка недоступна</span> : delta <= 1e-9 ? <span className="sum-ok">· совпадает</span> : <span className="sum-bad">· расхождение {delta}</span>}
            </p>
            <FactDetails facts={priorityFacts} />
          </details>
        </> : <p className="no-data">Подробные вклады приоритета не переданы.</p>}
      </Section>

      <Section title="Наблюдаемые переводы" note="За июль 2026, внутри банка, от 5 000 ₸. Входящие переводы за пределами выборки неизвестны.">
        <div className="dossier-flows">
          <div><span className="dossier-flow-label">↙ Входящие</span><strong>{formatKzt(entity.metrics.in_kzt)}</strong><span>Отправителей: {formatCount(entity.metrics.in_degree)}</span><span>Операций: {formatCount(entity.metrics.in_tx)}</span></div>
          <div><span className="dossier-flow-label">↗ Исходящие</span><strong>{formatKzt(entity.metrics.out_kzt)}</strong><span>Получателей: {formatCount(entity.metrics.out_degree)}</span><span>Операций: {formatCount(entity.metrics.out_tx)}</span></div>
        </div>
        <details className="dossier-details">
          <summary>Дополнительные признаки сети</summary>
          <dl className="metrics dossier-extra-metrics">
            <div><dt>Исходящие / входящие</dt><dd>{entity.metrics.pass_through === null ? 'Не определено' : formatScore(entity.metrics.pass_through)}</dd></div>
            <div><dt>Прямые отправители из seed</dt><dd>{entity.metrics.direct_seed_senders}</dd></div>
            <div><dt>Достижим от seed за ≤ 4 шага</dt><dd>{entity.metrics.seed_reach_4}</dd></div>
            <div><dt>Посредничество на путях · betweenness</dt><dd>{formatScore(entity.metrics.betweenness)}</dd></div>
          </dl>
          <p className="hint">Соотношение исходящих и входящих не является балансом и не показывает долю тех же денег. Структурный путь не доказывает хронологию переводов.</p>
        </details>
      </Section>

      <Section title="Роль в наблюдаемой сети">
        <div className="dossier-role-summary">
          <div className="score-main"><span className="dot" style={{ backgroundColor: ROLE_COLORS[entity.role] }} aria-hidden="true" /><strong>{ROLE_LABELS[entity.role]}</strong></div>
          <p>{ROLE_NOTES[entity.role]}</p>
          <div className="dossier-role-score"><span>Поддержка гипотезы по правилам</span><strong title={`Точное значение: ${entity.role_score}`}>{entity.role_score.toFixed(2)} / 1</strong></div>
        </div>
        <p className="hint">Эвристическая оценка роли, отдельно от приоритета проверки. Не измеренная точность.</p>
        <details className="dossier-details">
          <summary>Основания роли{entity.secondary_roles.length > 0 ? ' и вторичные признаки' : ''}</summary>
          <p className="dossier-evidence-text">{entity.evidence_text}</p>
          {entity.secondary_roles.length > 0 ? <><p className="dossier-small-label">Дополнительные структурные признаки</p><ul className="chips">{entity.secondary_roles.map((role) => <li className="chip" key={role}>{ROLE_LABELS[role]}</li>)}</ul></> : null}
          {roleFacts.length > 0 ? <FactDetails facts={roleFacts} /> : <p className="no-data">Подробные факты роли не переданы.</p>}
        </details>
      </Section>

      <Section title="Границы выводов">
        {entity.limitations.length > 0 ? <ul className="dossier-limitations">{entity.limitations.map((code) => <li key={code} title={code}>{limitationLabel(code)}</li>)}</ul> : <p className="no-data">Ограничения по узлу не переданы.</p>}
      </Section>
      <Section title="Что проверить дальше">
        {entity.next_checks.length > 0 ? <ol className="next-checks">{entity.next_checks.map((check) => <li key={check}>{check}</li>)}</ol> : <p className="no-data">Дополнительные шаги не указаны.</p>}
      </Section>
      <p className="dossier-foot">Все {entity.evidence.length} фактов доступны в основаниях приоритета и роли. Метрики относятся ко всей наблюдаемой сети, даже если граф показывает её часть.</p>
    </article>
  )
}
