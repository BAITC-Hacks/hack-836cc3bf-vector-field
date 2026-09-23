import { useEffect, useState } from 'react'
import type { Gid, InvestigationResponse } from '@shared/contracts'

interface Props {
  mode: 'fixture' | 'live'
  selectedGid: Gid | null
  snapshotId: string | null
}

const BASE = (import.meta.env.VITE_API_BASE ?? '').replace(/\/+$/, '')

export function InvestigatorPanel({ mode, selectedGid, snapshotId }: Props) {
  const [question, setQuestion] = useState('Какие наблюдаемые признаки стоит проверить дальше?')
  const [result, setResult] = useState<InvestigationResponse | null>(null)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setResult(null)
    setError(null)
  }, [selectedGid, snapshotId])

  async function investigate() {
    if (!selectedGid || !snapshotId || !question.trim()) return
    setPending(true)
    setResult(null)
    setError(null)
    try {
      const response = await fetch(`${BASE}/api/investigate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({ question: question.trim(), selected_gids: [selectedGid], snapshot_id: snapshotId }),
      })
      const body = await response.json()
      if (!response.ok) throw new Error(body?.error?.message ?? `HTTP ${response.status}`)
      const data = body as InvestigationResponse
      if (data.meta.snapshot_id !== snapshotId) throw new Error('Snapshot изменился; обновите страницу.')
      setResult(data)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause))
    } finally {
      setPending(false)
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
        {error ? <p className="banner banner-warning" role="alert">{error}</p> : null}
        {result ? <div role="status">
          <p><strong>AI: {result.status}</strong> — {result.message}</p>
          {result.status === 'unavailable' ? <p>AI недоступен. Очередь, карточка и граф остаются доступны.</p> : null}
          {result.findings.map((finding, index) => <p key={index}>{finding.text} <code>{finding.gids.join(', ')}</code></p>)}
          {result.tool_calls.length > 0 ? <ul>{result.tool_calls.map((call, index) =>
            <li key={index}>{call.name}: {call.status}, {call.duration_ms} мс</li>)}</ul> : null}
        </div> : null}
      </>}
    </section>
  )
}
