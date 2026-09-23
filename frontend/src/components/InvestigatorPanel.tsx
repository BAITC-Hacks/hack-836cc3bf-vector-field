import { useEffect, useRef, useState, type FormEvent } from 'react'
import type { ErrorResponse, Gid, InvestigationResponse } from '@shared/contracts'
import { InvestigationResult, type SubmittedQuestion } from './InvestigationResult'
import { LoadingBlock } from './States'

interface Props {
  mode: 'fixture' | 'live'
  selectedGid: Gid | null
  snapshotId: string | null
  onSelect(gid: Gid): void
}

const BASE = (import.meta.env.VITE_API_BASE ?? '').replace(/\/+$/, '')
const CLIENT_TIMEOUT_MS = 40_000

function httpError(status: number, body: ErrorResponse | null): string {
  if (status === 409) return 'Snapshot изменился. Обновите страницу и повторите вопрос.'
  if ([404, 422, 503].includes(status) && body?.error?.message) return body.error.message
  return 'Investigator не ответил. Попробуйте ещё раз; очередь, граф и карточки доступны.'
}

export function InvestigatorPanel({ mode, selectedGid, snapshotId, onSelect }: Props) {
  const [question, setQuestion] = useState('')
  const [submitted, setSubmitted] = useState<SubmittedQuestion | null>(null)
  const [result, setResult] = useState<InvestigationResponse | null>(null)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const requestId = useRef(0)
  const activeRequest = useRef<AbortController | null>(null)

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
    if (mode !== 'live' || pending || !snapshotId || !text) return

    const currentId = ++requestId.current
    const controller = new AbortController()
    activeRequest.current = controller
    const submittedQuestion = { text, gid: selectedGid }
    const timer = window.setTimeout(() => controller.abort(), CLIENT_TIMEOUT_MS)
    setSubmitted(submittedQuestion)
    setPending(true)
    setResult(null)
    setError(null)

    try {
      const response = await fetch(`${BASE}/api/investigate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({
          question: text,
          selected_gids: selectedGid === null ? [] : [selectedGid],
          snapshot_id: snapshotId,
        }),
        signal: controller.signal,
      })
      const body = await response.json().catch(() => null) as InvestigationResponse | ErrorResponse | null
      if (!response.ok) throw new Error(httpError(response.status, body as ErrorResponse | null))
      const data = body as InvestigationResponse | null
      if (!data?.meta || !['completed', 'unavailable', 'timeout', 'failed'].includes(data.status) ||
          typeof data.message !== 'string' || !Array.isArray(data.findings) || !Array.isArray(data.evidence) ||
          !Array.isArray(data.limitations) || !Array.isArray(data.next_checks) || !Array.isArray(data.tool_calls)) {
        throw new Error('Investigator вернул неполный ответ. Попробуйте ещё раз.')
      }
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
          <p className="investigator-intro">Задайте вопрос о сети. Выбранный узел добавится как контекст; выводы опираются на факты текущего snapshot.</p>
          <form className="investigator-form" onSubmit={investigate}>
            <label className="investigator-label" htmlFor="investigator-question">Ваш вопрос</label>
            <textarea id="investigator-question" className="search-input investigator-question" value={question}
              onChange={(event) => setQuestion(event.target.value)} rows={3} maxLength={2000}
              placeholder="Например: какие узлы проверить первыми и почему?" />
            <div className="investigator-form-bottom">
              <span className="investigator-scope">{selectedGid ? <>Контекст: <code>{selectedGid}</code></> : 'Контекст: вся наблюдаемая сеть'}</span>
              <button type="submit" className="btn investigator-submit" disabled={pending || !snapshotId || !question.trim()}>
                {pending ? 'Проверка…' : 'Отправить вопрос'}
              </button>
            </div>
          </form>
          {!snapshotId ? <p className="hint">Ожидание snapshot для вопроса.</p> : null}
          {pending ? <LoadingBlock label="Investigator проверяет данные текущего snapshot…" /> : null}
          {error ? <div className="state state-error" role="alert"><span className="state-title">Не удалось получить ответ</span><p className="state-message">{error}</p></div> : null}
          {result && submitted ? <InvestigationResult result={result} submitted={submitted} onSelect={onSelect} /> : null}
        </>
      )}
    </section>
  )
}
