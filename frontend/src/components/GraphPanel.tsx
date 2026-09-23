import { useEffect, useMemo, useRef, useState } from 'react'
import cytoscape from 'cytoscape'
import type { Edge, Gid, Role, SubgraphResponse } from '@shared/contracts'
import { formatKzt, formatScore, shortGid } from '../data/format'
import { limitationLabel } from '../data/limitations'
import { ROLE_COLORS, ROLE_LABELS } from '../data/labels'
import type { Async } from '../data/useAsyncData'
import { EmptyBlock, LoadingBlock, StateBlock } from './States'

interface Props {
  state: Async<SubgraphResponse | null>
  onSelect(gid: Gid): void
  subgraphLimit: number
  onSubgraphLimit(limit: number): void
}

interface HoverInfo {
  gid: Gid
  role: Role
  priority: number
  isSeed: boolean
}

/** Layout ranking only — a BFS over the shown edge list so the selected node
 *  sits in the middle. This is positioning, not an analytic metric: nothing
 *  computed here is ever displayed as data. */
function ringDistances(center: Gid, edges: Edge[]): Map<Gid, number> {
  const adjacency = new Map<Gid, Gid[]>()
  const link = (a: Gid, b: Gid) => {
    const list = adjacency.get(a)
    if (list) list.push(b)
    else adjacency.set(a, [b])
  }
  for (const edge of edges) {
    link(edge.src, edge.dst)
    link(edge.dst, edge.src)
  }

  const distance = new Map<Gid, number>([[center, 0]])
  let frontier: Gid[] = [center]
  while (frontier.length > 0) {
    const next: Gid[] = []
    for (const current of frontier) {
      for (const neighbour of adjacency.get(current) ?? []) {
        if (!distance.has(neighbour)) {
          distance.set(neighbour, (distance.get(current) ?? 0) + 1)
          next.push(neighbour)
        }
      }
    }
    frontier = next
  }
  return distance
}

const GRAPH_STYLE = [
  {
    selector: 'node',
    style: {
      label: 'data(label)',
      'text-valign': 'bottom',
      'text-halign': 'center',
      'text-margin-y': 8,
      'font-size': 10,
      'font-family': 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
      color: '#cbd5e1',
      'text-outline-width': 0,
      'background-color': 'data(color)',
      width: 'data(size)',
      height: 'data(size)',
      shape: 'ellipse',
      'border-width': 2,
      'border-color': '#64748b',
    },
  },
  { selector: 'node[?isSeed]', style: { 'border-width': 4, 'border-color': '#fbbf24' } },
  { selector: 'node[?isCenter]', style: { 'border-width': 4, 'border-color': '#38bdf8' } },
  {
    selector: 'node[?boundary]',
    style: { 'border-style': 'dashed', 'border-width': 4, 'border-color': '#fb923c' },
  },
  { selector: 'node:selected', style: { 'border-width': 5, 'border-color': '#f472b6' } },
  {
    selector: 'edge',
    style: {
      width: 2,
      'line-color': '#475569',
      'target-arrow-color': '#475569',
      'target-arrow-shape': 'triangle',
      'arrow-scale': 1.3,
      'curve-style': 'bezier',
      label: 'data(label)',
      'font-size': 9,
      color: '#94a3b8',
      'text-rotation': 'autorotate',
      'text-margin-y': -10,
      'text-background-color': '#0b1220',
      'text-background-opacity': 0.8,
      'text-background-padding': 2,
    },
  },
]

export function GraphPanel({ state, onSelect, subgraphLimit, onSubgraphLimit }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const cyRef = useRef<cytoscape.Core | null>(null)
  const onSelectRef = useRef(onSelect)
  const [hovered, setHovered] = useState<HoverInfo | null>(null)
  const data = state.status === 'ready' ? state.data : null

  useEffect(() => {
    onSelectRef.current = onSelect
  }, [onSelect])

  // One cytoscape instance for the lifetime of the panel — a library, not a
  // hand-rolled engine. Node ids are the gid strings themselves.
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const cy = cytoscape({
      container,
      elements: [],
      // Cytoscape's declaration cannot infer data-driven style values such as
      // `data(color)` from the object literal; runtime shape is the documented
      // stylesheet format.
      style: GRAPH_STYLE as never,
      minZoom: 0.3,
      maxZoom: 3,
      wheelSensitivity: 0.25,
      boxSelectionEnabled: false,
    })

    cy.on('tap', 'node', (event) => {
      onSelectRef.current(event.target.id())
    })
    cy.on('mouseover', 'node', (event) => {
      const node = event.target as cytoscape.NodeSingular
      setHovered({
        gid: node.id(),
        role: node.data('role') as Role,
        priority: node.data('priority') as number,
        isSeed: Boolean(node.data('isSeed')),
      })
    })
    cy.on('mouseout', 'node', () => setHovered(null))

    const handleResize = () => cy.resize()
    window.addEventListener('resize', handleResize)

    cyRef.current = cy
    return () => {
      window.removeEventListener('resize', handleResize)
      cy.destroy()
      cyRef.current = null
    }
  }, [data !== null])

  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return
    setHovered(null)
    if (!data) {
      cy.elements().remove()
      return
    }

    const distances = ringDistances(data.center_gid, data.edges)
    const showEdgeLabels = data.edges.length <= 12

    const nodes = data.nodes.map((node) => ({
      data: {
        id: node.gid,
        role: node.role,
        priority: node.priority_score,
        isSeed: node.is_seed,
        isCenter: node.gid === data.center_gid,
        boundary: node.depth === 4,
        color: ROLE_COLORS[node.role],
        // Bounded size range so one hub cannot swallow the screen.
        size: Math.round(28 + 20 * node.priority_score),
        label: shortGid(node.gid),
      },
    }))

    const edges = data.edges.map((edge, index) => ({
      data: {
        id: `${edge.src}>${edge.dst}#${index}`,
        source: edge.src,
        target: edge.dst,
        label: showEdgeLabels ? `${formatKzt(edge.sum_kzt)} · ${edge.n_tx} оп.` : '',
      },
    }))

    cy.batch(() => {
      cy.elements().remove()
      cy.add([...nodes, ...edges])
    })

    cy.layout({
      name: 'concentric',
      // Larger value = inner ring. Centre of the ego-graph wins.
      concentric: (node) => {
        const distance = distances.get(node.id())
        return distance === undefined ? -1 : 2 - distance
      },
      levelWidth: () => 1,
      minNodeSpacing: 52,
      avoidOverlap: true,
      padding: 28,
      animate: false,
    }).run()

    cy.fit()
    cy.resize()
  }, [data])

  const legend = useMemo(
    () =>
      (Object.keys(ROLE_LABELS) as Role[]).map((role) => (
        <li key={role}>
          <span className="dot" style={{ backgroundColor: ROLE_COLORS[role] }} aria-hidden="true" />
          {ROLE_LABELS[role]}
        </li>
      )),
    [],
  )

  return (
    <section className="panel panel-graph">
      <div className="panel-head">
        <h2 className="panel-title">Направленный ego-граф</h2>
        {data ? (
          <span className="panel-sub">
            центр <code>{data.center_gid}</code> · hops {data.hops}
          </span>
        ) : null}
        <div className="limit-toggle" role="group" aria-label="limit подграфа">
          <button
            type="button"
            className={`chip ${subgraphLimit === 80 ? 'is-on' : ''}`}
            onClick={() => onSubgraphLimit(80)}
          >
            limit 80
          </button>
          <button
            type="button"
            className={`chip ${subgraphLimit === 2 ? 'is-on' : ''}`}
            onClick={() => onSubgraphLimit(2)}
          >
            limit 2 — урезанное
          </button>
          <button type="button" className={`chip ${subgraphLimit === 200 ? 'is-on' : ''}`}
            onClick={() => onSubgraphLimit(200)}>limit 200</button>
        </div>
      </div>

      {state.status === 'idle' || state.status === 'loading' ? (
        <LoadingBlock label="Загрузка окружения…" />
      ) : state.status === 'error' ? (
        <StateBlock title="Окружение недоступно" error={state.error} />
      ) : data === null ? (
        <EmptyBlock title="Узел не выбран">Выберите узел в очереди слева или найдите его по точному gid.</EmptyBlock>
      ) : (
        <>
          {data.truncated ? (
            <div className="banner banner-warning" role="status">
              <strong>Показана часть окружения.</strong> Узлов показано {data.nodes.length} из {data.total_nodes},
              скрыто соседей: <strong>{data.omitted_count}</strong>. Рёбер показано {data.edges.length} из{' '}
              {data.total_edges}, скрыто: {data.omitted_edges}. <code>limit={subgraphLimit}</code> — это ограничение
              ответа API, а не фильтр сети.
              <div className="banner-actions">
                <button type="button" className="btn" onClick={() => onSubgraphLimit(200)} disabled={subgraphLimit === 200}>
                  {subgraphLimit === 200 ? 'Достигнут лимит 200' : 'Показать остальных соседей'}
                </button>
                <span className="chip">{limitationLabel('subgraph_truncated')}</span>
              </div>
            </div>
          ) : null}

          <div className="graph-status">
            {hovered ? (
              <span>
                <code>{hovered.gid}</code>
                {hovered.isSeed ? <span className="badge badge-seed">seed</span> : null} · {ROLE_LABELS[hovered.role]}{' '}
                · priority {formatScore(hovered.priority)} (баллы)
              </span>
            ) : data.edges.length === 0 ? (
              <span className="graph-empty-note">
                Нет наблюдаемых связей: у узла 0 входящих и 0 исходящих рёбер в этой выборке.
              </span>
            ) : (
              <span>
                {data.nodes.length} узлов · {data.edges.length} направленных рёбер · наведите курсор на узел, клик —
                открыть карточку
              </span>
            )}
            {' '}<a className="btn btn-tiny" href="#selected-dossier">Карточка узла</a>
          </div>

          <div className="graph-canvas" ref={containerRef} />

          <ul className="legend">
            <li className="legend-title">Роль (цвет + подпись)</li>
            {legend}
            <li className="legend-sep">
              <span className="legend-ring legend-ring-seed" aria-hidden="true" /> жёлтая обводка — seed
            </li>
            <li>
              <span className="legend-ring legend-ring-center" aria-hidden="true" /> голубая обводка — выбранный узел
            </li>
            <li>
              <span className="legend-ring legend-ring-boundary" aria-hidden="true" /> пунктир — depth 4 (граница
              обхода)
            </li>
            <li>
              <span className="legend-arrow" aria-hidden="true" />→ стрелка = исходящий перевод src → dst; размер
              узла — priority в ограниченном диапазоне
            </li>
          </ul>
        </>
      )}
    </section>
  )
}
