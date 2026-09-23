import type { SummaryResponse } from '@shared/contracts'
import { formatCount, formatKzt } from '../data/format'
import { isKnownLimitation, limitationLabel } from '../data/limitations'
import type { Async } from '../data/useAsyncData'
import { ErrorBlock, LoadingBlock } from './States'

const COUNT_LABELS: { key: keyof SummaryResponse['counts']; label: string }[] = [
  { key: 'n_nodes', label: 'Узлов' },
  { key: 'n_edges', label: 'Рёбер' },
  { key: 'n_transactions', label: 'Транзакций' },
  { key: 'n_seed', label: 'Seed' },
  { key: 'n_components', label: 'Компонент' },
  { key: 'n_components_with_edges', label: 'Из них со связями' },
  { key: 'n_isolates', label: 'Изолятов' },
  { key: 'n_depth_truncated', label: 'Depth=4' },
  { key: 'n_clusters', label: 'Кластеров' },
]

interface Props {
  state: Async<SummaryResponse>
  providerMode: 'fixture' | 'live'
}

const API_BASE = (import.meta.env.VITE_API_BASE ?? '').replace(/\/+$/, '')

export function BriefHeader({ state, providerMode }: Props) {
  if (state.status === 'loading' || state.status === 'idle') {
    return (
      <header className="brief">
        <LoadingBlock label="Загрузка сводки…" />
      </header>
    )
  }
  if (state.status === 'error') {
    return (
      <header className="brief">
        <ErrorBlock title="Сводка недоступна" error={state.error} />
      </header>
    )
  }

  const { meta, period, counts, total_observed_kzt, limitations } = state.data
  const synthetic = meta.data_mode === 'fixture'

  return (
    <header className="brief">
      <div className="brief-lead">
        <h1>Очередь проверки финансовой сети</h1>
        {synthetic ? <span className="badge badge-training">Учебные данные</span> : null}
        <span className="badge badge-mode">{providerMode === 'fixture' ? 'provider: fixture' : 'provider: live'}</span>
        {providerMode === 'live' ? (
          <div className="brief-actions">
            <details className="export-menu">
              <summary className="btn">Экспорт CSV</summary>
              <div className="export-menu-items">
                <a href={`${API_BASE}/api/export/top_nodes.csv`}>Топ узлов</a>
                <a href={`${API_BASE}/api/export/nodes_roles.csv`}>Роли всех узлов</a>
                <a href={`${API_BASE}/api/export/clusters.csv`}>Кластеры</a>
              </div>
            </details>
            <a className="btn btn-investigator-link" href="#investigator-question">Спросить Investigator</a>
          </div>
        ) : null}
      </div>

      <p className="brief-caption">
        {synthetic
          ? 'Числа ниже приходят из синтетического fixture-набора (6 узлов). Это НЕ расчёт по Parquet-кейсу (2248 узлов) и НЕ результат анализа: свои scores, кластеры и топ-20 даёт pipeline, экран их только показывает.'
          : 'Числа рассчитаны локальным pipeline и читаются из одного snapshot.'}{' '}
        Период наблюдения: <strong>{period.from}</strong> — <strong>{period.to}</strong>.
      </p>

      <dl className="brief-counts">
        {COUNT_LABELS.map(({ key, label }) => (
          <div className="brief-count" key={key}>
            <dt>{label}</dt>
            <dd>{formatCount(counts[key])}</dd>
          </div>
        ))}
        <div className="brief-count">
          <dt>Наблюдаемый оборот</dt>
          <dd>{formatKzt(total_observed_kzt)}</dd>
        </div>
      </dl>

      <div className="brief-meta">
        <span>
          snapshot <code>{meta.snapshot_id}</code>
        </span>
        <span>
          rules <code>{meta.rules_version}</code>
        </span>
        <span>
          contract v{meta.contract_version}
        </span>
      </div>

      <ul className="chips">
        {limitations.map((code) => (
          <li
            className={`chip ${isKnownLimitation(code) ? '' : 'chip-unknown'}`}
            key={code}
            title={code}
          >
            {limitationLabel(code)}
          </li>
        ))}
      </ul>
    </header>
  )
}
