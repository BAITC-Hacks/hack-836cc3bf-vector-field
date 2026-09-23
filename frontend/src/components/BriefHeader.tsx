import { useState } from 'react'
import type { SummaryResponse } from '@shared/contracts'
import { formatCount, formatKzt } from '../data/format'
import { limitationLabel } from '../data/limitations'
import type { Async } from '../data/useAsyncData'
import { ErrorBlock, LoadingBlock } from './States'

const COUNT_LABELS: { key: keyof SummaryResponse['counts']; label: string }[] = [
  { key: 'n_nodes', label: 'Узлов для проверки' },
  { key: 'n_edges', label: 'Направленных связей' },
  { key: 'n_transactions', label: 'Переводов' },
  { key: 'n_clusters', label: 'Кластеров' },
]
const EXPORTS = [
  { filename: 'top_nodes.csv', label: 'Очередь проверки' },
  { filename: 'nodes_roles.csv', label: 'Все узлы и роли' },
  { filename: 'clusters.csv', label: 'Кластеры' },
] as const
const API_BASE = (import.meta.env.VITE_API_BASE ?? '').replace(/\/+$/, '')

interface Props {
  state: Async<SummaryResponse>
  providerMode: 'fixture' | 'live'
}

export function BriefHeader({ state, providerMode }: Props) {
  const [exporting, setExporting] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)

  async function download(filename: typeof EXPORTS[number]['filename']) {
    setExportError(null)
    setExporting(true)
    try {
      const response = await fetch(`${API_BASE}/api/export/${filename}`)
      if (!response.ok) throw new Error('export unavailable')
      // Check availability first so a server error stays inside the workspace.
      // Keep the actual download as a native URL for embedded browser support.
      await response.arrayBuffer()
      const link = document.createElement('a')
      link.href = `${API_BASE}/api/export/${filename}`
      link.download = filename
      document.body.append(link)
      link.click()
      link.remove()
    } catch {
      setExportError('Не удалось скачать CSV. Повторите попытку; очередь и карточки доступны.')
    } finally {
      setExporting(false)
    }
  }

  if (state.status === 'loading' || state.status === 'idle') {
    return <header className="brief"><h1>Проверка финансовой сети</h1><LoadingBlock label="Загрузка аналитики…" /></header>
  }
  if (state.status === 'error') {
    return <header className="brief"><h1>Проверка финансовой сети</h1><ErrorBlock title="Данные пока недоступны" error={state.error} /></header>
  }

  const { meta, period, counts, total_observed_kzt, limitations } = state.data
  const synthetic = meta.data_mode === 'fixture'
  return (
    <header className="brief">
      <div className="brief-lead">
        <span className="brand">HackAlem</span>
        <h1>Кого проверить первым?</h1>
        {synthetic ? <span className="badge badge-training">Учебные данные</span> : <span className="badge badge-mode">Финансовая сеть</span>}
        {providerMode === 'live' ? <div className="brief-actions">
          <details className="export-menu">
            <summary className="btn">Экспорт CSV</summary>
            <div className="export-menu-items">
              {EXPORTS.map(({ filename, label }) => <button key={filename} type="button" disabled={exporting} onClick={() => void download(filename)}>
                {label}<small>{filename}</small>
              </button>)}
            </div>
          </details>
          <a className="btn btn-investigator-link" href="#investigator-question">Задать вопрос AI ↓</a>
        </div> : null}
      </div>
      <p className="brief-caption">Выберите узел в очереди → изучите основания → проверьте связи на графе.
        <strong> Приоритет — порядок проверки, не вероятность преступления.</strong></p>
      {synthetic ? <p className="hint hint-warning">Учебный пример: синтетические данные и оценки. Это не результат анализа исходного кейса.</p> : null}
      <div className="brief-overview">
        <dl className="brief-counts">
          {COUNT_LABELS.map(({ key, label }) => <div className="brief-count" key={key}>
            <dt>{label}</dt><dd>{formatCount(counts[key])}</dd>
          </div>)}
        </dl>
        <div className="brief-scope">
          <span>Период: <strong>{period.from} — {period.to}</strong></span>
          <span>Наблюдаемый оборот: <strong>{formatKzt(total_observed_kzt)}</strong></span>
          <span>Внутри банка · переводы от 5 000 KZT · обход до 4 колен</span>
        </div>
      </div>
      <details className="dataset-details">
        <summary>Границы данных и методика <span>Входящие неполны · путь не доказывает движение тех же денег</span></summary>
        <p className="hint">{counts.n_seed} исходных узлов (seed) · {counts.n_components} компонент, из них {counts.n_components_with_edges} со связями · {counts.n_isolates} изолятов · {counts.n_depth_truncated} узлов на границе обхода.</p>
        <ul className="chips">{limitations.map((code) => <li className="chip" key={code}>{limitationLabel(code)}</li>)}</ul>
        <p className="brief-meta">Версия расчёта: <code>{meta.rules_version}</code> · Набор данных: <code>{meta.snapshot_id}</code> · Контракт v{meta.contract_version}</p>
      </details>
      {exportError ? <p className="field-error" role="alert">{exportError}</p> : null}
    </header>
  )
}
