import { useLayoutEffect, useRef, useState } from 'react'
import type { Gid, InvestigationResponse } from '@shared/contracts'

interface Props {
  mode: 'fixture' | 'live'
  selectedGid: Gid | null
  snapshotId: string | null
}

const BASE = (import.meta.env.VITE_API_BASE ?? '').replace(/\/+$/, '')

export function InvestigatorPanel({ mode, selectedGid, snapshotId }: Props) {
  const [question, setQuestion] = useState('Какие наблюдаемые признаки стоит проверить дальше?')
  const [result, setResult] = useState<{
    gid: Gid; snapshotId: string; response: InvestigationResponse
  } | null>(null)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<{
    gid: Gid; snapshotId: string; message: string
  } | null>(null)
  const requestSequence = useRef(0)

  const visibleResult = result?.gid === selectedGid && result.snapshotId === snapshotId
    ? result.response : null
  const visibleError = error?.gid === selectedGid && error.snapshotId === snapshotId
    ? error.message : null

  useLayoutEffect(() => {
    requestSequence.current += 1
    setResult(null)
    setError(null)
    setPending(false)
  }, [selectedGid, snapshotId])

  async function investigate() {
    const gid = selectedGid
    const requestedSnapshotId = snapshotId
    if (!gid || !requestedSnapshotId || !question.trim()) return
    const sequence = ++requestSequence.current
    setPending(true)
    setResult(null)
    setError(null)
    try {
      const response = await fetch(`${BASE}/api/investigate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({ question: question.trim(), selected_gids: [gid], snapshot_id: requestedSnapshotId }),
      })
      const body = await response.json()
      if (sequence !== requestSequence.current) return
      if (!response.ok) throw new Error(body?.error?.message ?? `HTTP ${response.status}`)
      const data = body as InvestigationResponse
      if (data.meta.snapshot_id !== requestedSnapshotId) throw new Error('Snapshot изменился; обновите страницу.')
      setResult({ gid, snapshotId: requestedSnapshotId, response: data })
    } catch (cause) {
      if (sequence === requestSequence.current) {
        setError({ gid, snapshotId: requestedSnapshotId, message: cause instanceof Error ? cause.message : String(cause) })
      }
    } finally {
      if (sequence === requestSequence.current) setPending(false)
    }
  }

  return (
    <section className="panel" aria-label="Investigator">
      <div className="panel-head"><h2 className="panel-title">Investigator</h2><span className="panel-sub">необязательная проверка</span></div>
      {mode === 'fixture' ? <p className="hint">На учебных данных Investigator недоступен.</p> : <>
        <p className="hint">Использует только read-only операции над текущим snapshot. Основной экран работает независимо от AI.</p>
        <textarea className="search-input investigator-question" aria-label="Вопрос Investigator" value={question} onChange={(event) => setQuestion(event.target.value)} rows={3} />
        <button type="button" className="btn" disabled={pending || !selectedGid || !snapshotId || !question.trim()}
          onClick={investigate}>{pending ? 'Проверка…' : 'Спросить по выбранному узлу'}</button>
        {!selectedGid ? <p className="hint">Сначала выберите узел.</p> : null}
        {visibleError ? <p className="banner banner-warning" role="alert">{visibleError}</p> : null}
        {visibleResult ? <div role="status">
          <p><strong>AI: {visibleResult.status}</strong> — {visibleResult.message}</p>
          {visibleResult.status === 'unavailable' ? <p>AI недоступен. Очередь, карточка и граф остаются доступны.</p> : null}
          {visibleResult.findings.map((finding, index) => <p key={index}>{finding.text} <code>{finding.gids.join(', ')}</code></p>)}
          {visibleResult.tool_calls.length > 0 ? <ul>{visibleResult.tool_calls.map((call, index) =>
            <li key={index}>{call.name}: {call.status}, {call.duration_ms} мс</li>)}</ul> : null}
        </div> : null}
      </>}
    </section>
  )
}
