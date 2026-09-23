import { useEffect, useRef, useState, type FormEvent } from 'react'
import type { ErrorResponse, Gid, InvestigationResponse } from '@shared/contracts'
import { InvestigationResult, type SubmittedQuestion } from './InvestigationResult'
import { LoadingBlock } from './States'
import './Investigator.css'

interface Props {
  mode: 'fixture' | 'live'
  selectedGid: Gid | null
  snapshotId: string | null
  onSelect(gid: Gid): void
}

const BASE = (import.meta.env.VITE_API_BASE ?? '').replace(/\/+$/, '')
const CLIENT_TIMEOUT_MS = 40_000

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === 'string')
}

// Validate nested render inputs as well as the response envelope. A malformed
// response stays a local Investigator error rather than crashing the workspace.
function isInvestigationResponse(value: unknown): value is InvestigationResponse {
  if (!isRecord(value) || !isRecord(value.meta) || typeof value.meta.snapshot_id !== 'string' ||
      typeof value.status !== 'string' || !['completed', 'unavailable', 'timeout', 'failed'].includes(value.status) ||
      typeof value.message !== 'string' || !isStringArray(value.limitations) || !isStringArray(value.next_checks) ||
      !Array.isArray(value.findings) || !Array.isArray(value.evidence) || !Array.isArray(value.tool_calls)) return false

  return value.findings.every((finding) => isRecord(finding) && typeof finding.text === 'string' &&
    isStringArray(finding.gids) && finding.gids.every((gid) => /^\d+$/.test(gid)) &&
    isStringArray(finding.evidence_ids) && isStringArray(finding.limitations)) &&
    value.evidence.every((fact) => isRecord(fact) && typeof fact.evidence_id === 'string' &&
      typeof fact.gid === 'string' && /^\d+$/.test(fact.gid) && typeof fact.metric === 'string' &&
      (fact.value === null || typeof fact.value === 'string' || (typeof fact.value === 'number' && Number.isFinite(fact.value))) &&
      typeof fact.unit === 'string' && ['count', 'KZT', 'ratio', 'text'].includes(fact.unit) &&
      typeof fact.rule_id === 'string' && typeof fact.source === 'string' &&
      ['nodes.parquet', 'edges.parquet', 'transactions.parquet', 'derived'].includes(fact.source) &&
      typeof fact.scope === 'string' && typeof fact.text === 'string' && isStringArray(fact.limitations)) &&
    value.tool_calls.every((call) => isRecord(call) && typeof call.name === 'string' &&
      (call.status === 'completed' || call.status === 'failed') && typeof call.duration_ms === 'number' &&
      Number.isFinite(call.duration_ms) && call.duration_ms >= 0 && isStringArray(call.evidence_ids))
}

function httpError(status: number, body: ErrorResponse | null): string {
  if (status === 409) return 'Snapshot изменился. Обновите страницу и повторите вопрос.'
  if ([404, 422, 503].includes(status) && body?.error?.message) return body.error.message
  return 'Investigator не ответил. Попробуйте ещё раз; очередь, граф и карточки доступны.'
}

export function InvestigatorPanel({ mode, selectedGid, snapshotId, onSelect }: Props) {
  const [question, setQuestion] = useState('')
  const [contextMode, setContextMode] = useState<'network' | 'selected'>('network')
  const [submitted, setSubmitted] = useState<SubmittedQuestion | null>(null)
  const [result, setResult] = useState<InvestigationResponse | null>(null)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const questionInput = useRef<HTMLTextAreaElement | null>(null)
  const requestId = useRef(0)
  const activeRequest = useRef<AbortController | null>(null)
  const contextGid = contextMode === 'selected' ? selectedGid : null
  const selectedContextUnavailable = contextMode === 'selected' && selectedGid === null

  useEffect(() => {
    if (!pending) return
    const startedAt = Date.now()
    const timer = window.setInterval(() => setElapsedSeconds(Math.floor((Date.now() - startedAt) / 1000)), 1000)
    return () => window.clearInterval(timer)
  }, [pending])

  useEffect(() => {
    requestId.current += 1
    activeRequest.current?.abort()
    activeRequest.current = null
    setResult(null)
    setSubmitted(null)
    setError(null)
    setPending(false)
    return () => {
      requestId.current += 1
      activeRequest.current?.abort()
    }
  }, [mode, snapshotId])

  async function investigate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const text = question.trim()
    if (mode !== 'live' || pending || !snapshotId || !text || selectedContextUnavailable) return

    const currentId = ++requestId.current
    const controller = new AbortController()
    activeRequest.current = controller
    const submittedQuestion = { text, gid: contextGid }
    const timer = window.setTimeout(() => controller.abort(), CLIENT_TIMEOUT_MS)
    setSubmitted(submittedQuestion)
    setPending(true)
    setElapsedSeconds(0)
    setResult(null)
    setError(null)

    try {
      const response = await fetch(`${BASE}/api/investigate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({
          question: text,
          selected_gids: contextGid === null ? [] : [contextGid],
          snapshot_id: snapshotId,
        }),
        signal: controller.signal,
      })
      const body = await response.json().catch(() => null) as InvestigationResponse | ErrorResponse | null
      if (!response.ok) throw new Error(httpError(response.status, body as ErrorResponse | null))
      if (!isInvestigationResponse(body)) {
        throw new Error('Investigator вернул неполный ответ. Попробуйте ещё раз.')
      }
      const data = body
      if (data.meta.snapshot_id !== snapshotId) {
        throw new Error('Snapshot изменился. Обновите страницу и повторите вопрос.')
      }
      if (currentId === requestId.current) setResult(data)
    } catch (cause) {
      if (currentId === requestId.current) {
        setError(controller.signal.aborted
          ? 'Время ожидания Investigator истекло. Попробуйте ещё раз.'
          : cause instanceof TypeError ? 'Связь с Investigator временно недоступна. Попробуйте ещё раз.'
          : cause instanceof Error ? cause.message : 'Investigator не ответил. Попробуйте ещё раз.')
      }
    } finally {
      window.clearTimeout(timer)
      if (currentId === requestId.current) {
        activeRequest.current = null
        setPending(false)
      }
    }
  }

  return (
    <section className="panel investigator-panel" id="investigator" aria-label="Investigator">
      <div className="panel-head">
        <h2 className="panel-title">Спросить Investigator</h2>
        <span className="panel-sub">проверка наблюдаемых фактов</span>
      </div>
      {mode === 'fixture' ? (
        <p className="hint">Учебный режим: Investigator недоступен. Ответы AI не имитируются.</p>
      ) : (
        <>
          <p className="investigator-intro">Уточните, кого проверить и почему. Ответ связывает наблюдения с фактами, узлами и графом.</p>
          <form className="investigator-form" onSubmit={investigate}>
            <fieldset className="investigator-context-picker" disabled={pending}>
              <legend>Область вопроса</legend>
              <label className={contextMode === 'network' ? 'is-active' : ''}>
                <input type="radio" name="investigator-context" value="network" checked={contextMode === 'network'}
                  onChange={() => setContextMode('network')} />
                Вся сеть
              </label>
              <label className={contextMode === 'selected' ? 'is-active' : ''}>
                <input type="radio" name="investigator-context" value="selected" checked={contextMode === 'selected'}
                  disabled={!selectedGid} onChange={() => setContextMode('selected')} />
                Выбранный узел
              </label>
            </fieldset>
            <div className="investigator-examples" aria-label="Примеры вопросов">
              {(contextMode === 'network'
                ? ['Какие узлы проверить первыми и почему?', 'Какие ограничения есть у этих данных?']
                : ['Почему выбранный узел приоритетен для проверки?', 'Какие ограничения влияют на выводы об этом узле?']
              ).map((example) => (
                <button className="investigator-example" type="button" key={example} disabled={pending}
                  onClick={() => { setQuestion(example); questionInput.current?.focus() }}>
                  {example}
                </button>
              ))}
            </div>
            <label className="investigator-label" htmlFor="investigator-question">Ваш вопрос</label>
            <textarea id="investigator-question" ref={questionInput} className="search-input investigator-question" value={question}
              onChange={(event) => setQuestion(event.target.value)} rows={3} maxLength={2000}
              aria-describedby="investigator-question-context"
              placeholder="Например: какие узлы проверить первыми и почему?" />
            <div className="investigator-form-bottom">
              <span className="investigator-scope" id="investigator-question-context">{selectedContextUnavailable
                ? 'Выбранный узел недоступен. Выберите найденный узел или переключитесь на всю сеть.'
                : contextGid ? <>Контекст: <code>{contextGid}</code></> : 'Контекст: вся наблюдаемая сеть'}</span>
              <button type="submit" className="btn investigator-submit" disabled={pending || !snapshotId || !question.trim() || selectedContextUnavailable}>
                {pending ? 'Проверка…' : 'Отправить вопрос'}
              </button>
            </div>
          </form>
          {!snapshotId ? <p className="hint">Ожидание snapshot для вопроса.</p> : null}
          {pending ? <div className="investigator-pending">
            <LoadingBlock label={`Ожидание ответа Investigator · ${elapsedSeconds} с`} />
            <p className="investigator-context">Запрос выполняется. Вызовы инструментов появятся с ответом. Поиск и граф доступны.</p>
            {submitted ? <p className="investigator-context">Отправлен вопрос: {submitted.text}<br />
              {submitted.gid ? <>По узлу <code>{submitted.gid}</code></> : 'По всей наблюдаемой сети'}
            </p> : null}
          </div> : null}
          {error ? <div className="state state-error" role="alert"><span className="state-title">Не удалось получить ответ</span><p className="state-message">{error}</p>
            <p className="state-message">Вопрос сохранён. Отправьте его повторно; поиск, граф и карточки доступны.</p>
          </div> : null}
          {result && submitted ? <InvestigationResult result={result} submitted={submitted} onSelect={onSelect} /> : null}
        </>
      )}
    </section>
  )
}
