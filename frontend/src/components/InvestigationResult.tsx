import type { Evidence, Gid, InvestigationResponse } from '@shared/contracts'
import { limitationLabel } from '../data/limitations'
import { EmptyBlock } from './States'

export interface SubmittedQuestion {
  text: string
  gid: Gid | null
}

interface Props {
  result: InvestigationResponse
  submitted: SubmittedQuestion
  onSelect(gid: Gid): void
}

const TOOL_LABELS: Record<string, string> = {
  get_entity_profile: 'Профиль узла',
  get_subgraph: 'Окружение узла',
  rank_entities: 'Очередь приоритетов',
  find_common_recipients: 'Общие получатели',
}

function factValue(fact: Evidence): string {
  if (fact.value === null) return 'значение не передано'
  if (fact.unit === 'text') return String(fact.value)
  const value = typeof fact.value === 'number'
    ? fact.value !== 0 && Math.abs(fact.value) < 0.000001 && fact.unit !== 'KZT'
      ? fact.value.toExponential(2)
      : new Intl.NumberFormat('ru-RU', { maximumFractionDigits: fact.unit === 'KZT' ? 2 : 6 }).format(fact.value)
    : fact.value
  return `${value} ${fact.unit === 'KZT' ? 'KZT' : fact.unit === 'count' ? 'шт.' : ''}`.trim()
}

function LimitationList({ items, compact = false }: { items: string[]; compact?: boolean }) {
  if (items.length === 0) return null
  const visible = compact ? items.slice(0, 3) : items
  return (
    <>
      <ul className="investigator-limitations">
        {visible.map((code) => <li key={code}>{limitationLabel(code)}</li>)}
      </ul>
      {compact && items.length > visible.length ? (
        <details className="investigator-more-limitations">
          <summary>Ещё {items.length - visible.length} ограничения</summary>
          <ul className="investigator-limitations">
            {items.slice(visible.length).map((code) => <li key={code}>{limitationLabel(code)}</li>)}
          </ul>
        </details>
      ) : null}
    </>
  )
}

export function InvestigationResult({ result, submitted, onSelect }: Props) {
  const factNumbers = new Map(result.evidence.map((fact, index) => [fact.evidence_id, index + 1]))
  const completed = result.status === 'completed'

  return (
    <div className="investigator-result" role="status" aria-live="polite">
      <div className="investigator-result-head">
        <span className={`investigator-status investigator-status-${result.status}`}>
          {completed ? 'Проверка завершена' : result.status === 'unavailable' ? 'AI недоступен' :
            result.status === 'timeout' ? 'Время ожидания истекло' : 'Ответ не получен'}
        </span>
        <p className="investigator-asked">{submitted.text}</p>
        <p className="investigator-context">
          {submitted.gid ? <>Вопрос по узлу <code>{submitted.gid}</code></> : 'Вопрос по наблюдаемой сети'}
        </p>
      </div>

      {!completed ? (
        <div className={`state ${result.status === 'failed' ? 'state-error' : 'state-unavailable'}`}>
          <p className="state-title">{result.message}</p>
          <p className="state-message">Очередь, поиск, граф и карточки продолжают работать.</p>
        </div>
      ) : result.findings.length === 0 ? (
        <EmptyBlock title="Подтверждённых находок нет">
          По этому вопросу не вернулись проверяемые факты.
        </EmptyBlock>
      ) : (
        <>
          <p className="investigator-summary">{result.message}</p>
          <h3 className="investigator-section-title">Что найдено</h3>
          <ol className="investigator-findings">
            {result.findings.map((finding, index) => (
              <li className="investigator-finding" key={`${index}-${finding.text}`}>
                <div className="investigator-finding-heading">Наблюдение {index + 1}</div>
                <p>{finding.text}</p>
                {finding.gids.length > 0 ? (
                  <div className="investigator-references">
                    <span>Открыть узел:</span>
                    {finding.gids.map((gid) => (
                      <button className="investigator-gid" type="button" key={gid} onClick={() => onSelect(gid)}
                        title={`Открыть карточку и граф узла ${gid}`}>
                        {gid}
                      </button>
                    ))}
                  </div>
                ) : null}
                {finding.evidence_ids.length > 0 ? (
                  <div className="investigator-references">
                    <span>Основания:</span>
                    {finding.evidence_ids.map((id) => {
                      const number = factNumbers.get(id)
                      return number ? <a className="investigator-fact-link" href={`#investigator-fact-${number}`} key={id}>
                        Факт {number}
                      </a> : <span className="investigator-missing-fact" key={id}>Факт недоступен</span>
                    })}
                  </div>
                ) : null}
                {finding.limitations.length > 0 ? (
                  <details className="investigator-finding-limitations">
                    <summary>Ограничения наблюдения · {finding.limitations.length}</summary>
                    <LimitationList items={finding.limitations} />
                  </details>
                ) : null}
              </li>
            ))}
          </ol>
        </>
      )}

      {completed && result.evidence.length > 0 ? (
        <section className="investigator-result-section" aria-label="Основания ответа">
          <h3 className="investigator-section-title">Основания · {result.evidence.length}</h3>
          <ol className="investigator-facts">
            {result.evidence.map((fact, index) => (
              <li id={`investigator-fact-${index + 1}`} key={fact.evidence_id}>
                <div className="investigator-fact-top">
                  <span>Факт {index + 1}</span>
                  <strong title={String(fact.value)}>{factValue(fact)}</strong>
                </div>
                <p>{fact.text}</p>
                <div className="investigator-fact-meta">
                  <button className="investigator-gid" type="button" onClick={() => onSelect(fact.gid)}
                    title={`Открыть карточку и граф узла ${fact.gid}`}>{fact.gid}</button>
                  <span>{fact.source === 'derived' ? 'расчёт по данным' : fact.source}</span>
                </div>
              </li>
            ))}
          </ol>
        </section>
      ) : null}

      {result.limitations.length > 0 ? (
        <section className="investigator-result-section">
          <h3 className="investigator-section-title">Что пока нельзя заключить</h3>
          <LimitationList items={result.limitations} compact />
        </section>
      ) : null}

      {result.next_checks.length > 0 ? (
        <section className="investigator-result-section">
          <h3 className="investigator-section-title">Следующие проверки</h3>
          <ol className="investigator-next-checks">
            {result.next_checks.map((check) => <li key={check}>{check}</li>)}
          </ol>
        </section>
      ) : null}

      {result.tool_calls.length > 0 ? (
        <details className="investigator-trace">
          <summary>Выполненные операции · {result.tool_calls.length}</summary>
          <ol>
            {result.tool_calls.map((call, index) => (
              <li key={`${call.name}-${index}`}>
                <span>{TOOL_LABELS[call.name] ?? call.name}</span>
                <span>{call.status === 'completed' ? 'выполнено' : 'ошибка'} · {call.duration_ms} мс</span>
              </li>
            ))}
          </ol>
        </details>
      ) : null}
    </div>
  )
}
