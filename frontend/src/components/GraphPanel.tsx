import { useEffect, useMemo, useRef, useState } from 'react'
import cytoscape from 'cytoscape'
import type { Edge, Gid, Role, SubgraphResponse } from '@shared/contracts'
import { formatKzt, formatScore, shortGid } from '../data/format'
import { ROLE_COLORS, ROLE_LABELS } from '../data/labels'
import type { Async } from '../data/useAsyncData'
import { EmptyBlock, LoadingBlock, StateBlock } from './States'
import './GraphPanel.css'

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
      'font-size': 12,
      'font-family': 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
      color: '#cbd5e1',
      'text-outline-width': 2,
      'text-outline-color': '#071524',
      'background-color': 'data(color)',
      width: 'data(size)',
      height: 'data(size)',
      shape: 'ellipse',
      'border-width': 2,
      'border-color': '#64748b',
    },
  },
  { selector: 'node[?isSeed]', style: { 'border-width': 4, 'border-color': '#fbbf24' } },
  {
    selector: 'node[?boundary]',
    style: { 'border-style': 'dashed', 'border-width': 4, 'border-color': '#fb923c' },
  },
  {
    selector: 'node[?isCenter]',
    style: {
      'border-width': 5,
      'border-color': '#7dd3fc',
      'underlay-color': '#38bdf8',
      'underlay-opacity': 0.2,
      'underlay-padding': 9,
      'font-weight': 'bold',
      color: '#f0f9ff',
      'z-index': 10,
    },
  },
  {
    selector: 'edge',
    style: {
      width: 2.4,
      'line-color': '#71869f',
      'target-arrow-color': '#a9bfd7',
      'target-arrow-shape': 'triangle',
      'arrow-scale': 1.6,
      'curve-style': 'bezier',
      label: 'data(label)',
      'font-size': 11,
      color: '#c0cfdf',
      'text-rotation': 'autorotate',
      'text-margin-y': -10,
      'text-background-color': '#0b1220',
      'text-background-opacity': 0.8,
      'text-background-padding': 2,
    },
  },
  { selector: 'edge[?touchesCenter]', style: { 'line-color': '#7ca9c5', 'target-arrow-color': '#bae6fd', width: 3 } },
]

function fitGraph(cy: cytoscape.Core) {
  cy.resize()
  cy.fit(cy.elements(), 48)
  // Keep a singleton legible without blowing it up to fill the canvas.
  if (cy.zoom() > 1.15) cy.zoom(1.15)
  cy.center()
}

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
      minZoom: 0.04,
      maxZoom: 3,
      wheelSensitivity: 0.25,
      boxSelectionEnabled: false,
      autounselectify: true,
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
    const resizeObserver = new ResizeObserver(handleResize)
    resizeObserver.observe(container)

    cyRef.current = cy
    return () => {
      window.removeEventListener('resize', handleResize)
      resizeObserver.disconnect()
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
        label: `${node.gid === data.center_gid ? 'ВЫБРАН · ' : ''}${shortGid(node.gid)}`,
      },
    }))

    const edges = data.edges.map((edge, index) => ({
      data: {
        id: `${edge.src}>${edge.dst}#${index}`,
        source: edge.src,
        target: edge.dst,
        touchesCenter: edge.src === data.center_gid || edge.dst === data.center_gid,
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
      minNodeSpacing: 65,
      avoidOverlap: true,
      padding: 28,
      animate: false,
    }).run()

    fitGraph(cy)
    // A large neighbourhood should open around the selected entity at a
    // readable scale. The overview control still fits every displayed node.
    if (cy.zoom() < 0.55) {
      cy.zoom(0.55)
      cy.center(cy.getElementById(data.center_gid))
    }
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

  const centerNode = data?.nodes.find((node) => node.gid === data.center_gid)
  const focusSelected = () => {
    const cy = cyRef.current
    if (!cy || !data) return
    cy.zoom(1)
    cy.center(cy.getElementById(data.center_gid))
  }

  return (
    <section className="panel panel-graph" aria-label="Связи выбранного узла">
      <div className="panel-head">
        <h2 className="panel-title">Связи выбранного узла</h2>
        <div className="limit-toggle" role="group" aria-label="Размер окружения">
          <button
            type="button"
            className={`chip ${subgraphLimit === 80 ? 'is-on' : ''}`}
            aria-pressed={subgraphLimit === 80}
            onClick={() => onSubgraphLimit(80)}
          >
            До 80 узлов
          </button>
          <button
            type="button"
            className={`chip ${subgraphLimit === 2 ? 'is-on' : ''}`}
            aria-pressed={subgraphLimit === 2}
            onClick={() => onSubgraphLimit(2)}
          >
            2 узла
          </button>
          <button type="button" className={`chip ${subgraphLimit === 200 ? 'is-on' : ''}`}
            aria-pressed={subgraphLimit === 200}
            onClick={() => onSubgraphLimit(200)}>До 200 узлов</button>
        </div>
      </div>

      {state.status === 'loading' ? (
        <LoadingBlock label="Загрузка окружения…" />
      ) : state.status === 'error' ? (
        <StateBlock title="Окружение недоступно" error={state.error} />
      ) : data === null ? (
        <EmptyBlock title="Узел не выбран">Выберите узел в очереди слева или найдите его по точному gid.</EmptyBlock>
      ) : (
        <>
          <div className="graph-context">
            <span className="graph-selected-label">Выбран GID <code>{data.center_gid}</code></span>
            <span>Окружение: {data.hops} {data.hops === 1 ? 'шаг' : 'шага'} по входящим и исходящим связям</span>
          </div>
          {data.truncated ? (
            <div className="banner banner-warning" role="status">
              <strong>Показана часть окружения.</strong> Узлов показано {data.nodes.length} из {data.total_nodes},
              скрыто соседей: <strong>{data.omitted_count}</strong>. Рёбер показано {data.edges.length} из{' '}
              {data.total_edges}, скрыто: <strong>{data.omitted_edges}</strong>. Метрики карточки относятся ко всей
              наблюдаемой сети.
              <div className="banner-actions">
                <button type="button" className="btn" onClick={() => onSubgraphLimit(200)} disabled={subgraphLimit === 200}>
                  {subgraphLimit === 200 ? 'Показан максимум: 200 узлов' : 'Расширить окружение до 200 узлов'}
                </button>
              </div>
            </div>
          ) : null}

          <div className="graph-status">
            <strong>{data.nodes.length} узлов · {data.edges.length} направленных связей</strong>
            <div className="graph-tools" role="group" aria-label="Управление графом">
              <button type="button" className="btn btn-tiny" onClick={focusSelected}>К выбранному</button>
              <button type="button" className="btn btn-tiny" onClick={() => { if (cyRef.current) fitGraph(cyRef.current) }}>Всё окружение</button>
              <a className="btn btn-tiny" href="#selected-dossier">Карточка узла</a>
            </div>
          </div>
          <div className="graph-node-info">
            {hovered ? (
              <span>
                <code>{hovered.gid}</code>
                {hovered.isSeed ? <span className="badge badge-seed">исходный узел</span> : null} · {ROLE_LABELS[hovered.role]}{' '}
                · приоритет проверки {formatScore(hovered.priority)}
              </span>
            ) : data.total_edges === 0 ? (
              <span className="graph-empty-note">
                В предоставленной сети нет наблюдаемых связей этого узла. Карточка и её ограничения доступны.
              </span>
            ) : (
              <span>Стрелка: отправитель → получатель. Нажмите на узел, чтобы открыть его карточку.</span>
            )}
          </div>

          <div className="graph-canvas" ref={containerRef} aria-label={`Направленные связи GID ${data.center_gid}`} />
          {centerNode?.depth === 4 ? (
            <p className="graph-boundary-note">Граница наблюдения: глубина 4. Отсутствие исходящих связей может быть следствием ограничения сбора.</p>
          ) : null}
          <p className="graph-navigation-note">Колесо — масштаб · перетаскивание — перемещение. Путь на графе не доказывает движение тех же средств.</p>

          <ul className="legend">
            <li className="legend-title">Структурные роли · подпись при наведении на узел</li>
            {legend}
            <li className="legend-sep">
              <span className="legend-ring legend-ring-seed" aria-hidden="true" /> жёлтая обводка — исходный узел
            </li>
            <li>
              <span className="legend-ring legend-ring-center" aria-hidden="true" /> голубая обводка — выбранный узел
            </li>
            <li>
              <span className="legend-ring legend-ring-boundary" aria-hidden="true" /> пунктир — граница наблюдения (глубина 4)
            </li>
            <li>
              <span className="legend-arrow" aria-hidden="true" />→ направление перевода · размер узла — приоритет проверки
            </li>
          </ul>
        </>
      )}
    </section>
  )
}
