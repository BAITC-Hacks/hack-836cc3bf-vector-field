import { useMemo, useState } from 'react'
import type { EntityResponse, Gid, Role, SubgraphResponse, SummaryResponse } from '@shared/contracts'
import { BriefHeader } from './components/BriefHeader'
import { Dossier } from './components/Dossier'
import { FixtureScenarios, type Scenario } from './components/FixtureScenarios'
import { GraphPanel } from './components/GraphPanel'
import { InvestigatorPanel } from './components/InvestigatorPanel'
import { PriorityQueue, type SeedFilter } from './components/PriorityQueue'
import { SearchBox } from './components/SearchBox'
import { createDataProvider, useAsyncData } from './data'

const UNKNOWN_GID: Gid = '999999999999999999'

export default function App() {
  const provider = useMemo(() => createDataProvider(), [])
  const [roleFilter, setRoleFilter] = useState<Role | 'all'>('all')
  const [seedFilter, setSeedFilter] = useState<SeedFilter>('all')
  const [query, setQuery] = useState('')
  const [queryError, setQueryError] = useState<string | null>(null)
  const [searchFeedback, setSearchFeedback] = useState<string | null>(null)
  const [selectedGid, setSelectedGid] = useState<Gid | null>(null)
  const [subgraphLimit, setSubgraphLimit] = useState(80)

  const summary = useAsyncData<SummaryResponse>(() => provider.getSummary(), [provider])
  const queue = useAsyncData(
    () =>
      provider.listEntities({
        role: roleFilter === 'all' ? undefined : roleFilter,
        is_seed: seedFilter === 'all' ? undefined : seedFilter === 'seed',
        offset: 0,
        limit: 200,
      }),
    [provider, roleFilter, seedFilter],
  )
  const entity = useAsyncData<EntityResponse | null>(
    async () => (selectedGid === null ? null : provider.getEntity(selectedGid)),
    [provider, selectedGid],
  )
  const subgraph = useAsyncData<SubgraphResponse | null>(
    async () =>
      selectedGid === null
        ? null
        : provider.getSubgraph({ gid: selectedGid, hops: 1, limit: subgraphLimit }),
    [provider, selectedGid, subgraphLimit],
  )

  function selectGid(gid: Gid) {
    setSelectedGid(gid)
    setQuery(gid)
    setQueryError(null)
    setSearchFeedback(null)
  }

  function searchGid(gid: Gid) {
    setQueryError(null)
    setSearchFeedback(null)
    if (gid === '') {
      setQueryError('Введите полный gid.')
      return
    }
    if (!/^\d+$/.test(gid)) {
      setQueryError('gid должен состоять только из десятичных цифр.')
      return
    }
    selectGid(gid)
  }

  const scenarioGids = useMemo(() => {
    if (summary.status !== 'ready') return null
    const nodes = summary.data.top_nodes
    return {
      ordinary: nodes.find((node) => node.role === 'consolidator')?.gid ?? null,
      isolate: nodes.find((node) => node.limitations.includes('isolated_seed'))?.gid ?? null,
      boundary: nodes.find((node) => node.depth === 4)?.gid ?? null,
    }
  }, [summary])

  const scenarios: Scenario[] = [
    { key: 'ordinary', label: 'Обычная карточка', gid: scenarioGids?.ordinary ?? null },
    { key: 'isolate', label: 'Изолят', gid: scenarioGids?.isolate ?? null },
    { key: 'boundary', label: 'Depth=4 boundary', gid: scenarioGids?.boundary ?? null },
    { key: 'truncated', label: 'Урезанное окружение', gid: scenarioGids?.ordinary ?? null },
    { key: 'not-found', label: 'ENTITY_NOT_FOUND', gid: UNKNOWN_GID },
  ]

  return (
    <div className="app-shell">
      <BriefHeader state={summary} providerMode={provider.mode} />

      <main className="workspace">
        <aside className="left-column">
          <SearchBox
            mode={provider.mode}
            value={query}
            onValueChange={(value) => {
              setQuery(value)
              setQueryError(null)
              setSearchFeedback(null)
            }}
            onSearch={searchGid}
            validationError={queryError}
            feedback={
              searchFeedback ? <p className="field-feedback">{searchFeedback}</p> : null
            }
          />
          {provider.mode === 'fixture' ? <FixtureScenarios
            scenarios={scenarios}
            activeGid={selectedGid}
            onSelect={selectGid}
          /> : null}
          <PriorityQueue
            state={queue}
            selectedGid={selectedGid}
            onSelect={selectGid}
            roleFilter={roleFilter}
            onRoleFilter={setRoleFilter}
            seedFilter={seedFilter}
            onSeedFilter={setSeedFilter}
            totalNodes={summary.status === 'ready' ? summary.data.counts.n_nodes : 0}
            mode={provider.mode}
          />
        </aside>

        <section className="center-column">
          <GraphPanel
            state={subgraph}
            onSelect={selectGid}
            subgraphLimit={subgraphLimit}
            onSubgraphLimit={setSubgraphLimit}
          />
        </section>

        <aside className="right-column">
          <section className="panel dossier-panel">
            <div className="panel-head">
              <h2 className="panel-title">Dossier</h2>
              <span className="panel-sub">профиль выбранного gid</span>
            </div>
            <Dossier state={entity} />
          </section>
          <InvestigatorPanel mode={provider.mode} selectedGid={selectedGid}
            snapshotId={summary.status === 'ready' ? summary.data.meta.snapshot_id : null} />
        </aside>
      </main>

      <footer className="footer">
        <span>HackAlem · {provider.mode === 'fixture' ? 'synthetic fixture UI' : 'live local snapshot'}</span>
        <span>Наблюдаемые связи и эвристические баллы требуют проверки аналитиком.</span>
      </footer>
    </div>
  )
}
