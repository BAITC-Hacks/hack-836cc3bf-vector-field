/** Fixture-backed data provider.
 *
 * Reads shared/transport v1 fixtures (shared/fixtures.json) — the single
 * synthetic source shared by frontend, backend and agent owners.
 *
 * Two things are implemented here rather than hard-coded as canned blobs:
 *  1. entity lookup — only the three full cards that actually exist in the
 *     fixture set; every other gid fails honestly with ENTITY_NOT_FOUND and
 *     never falls back to another node's dossier;
 *  2. subgraph — the contract rule (API_CONTRACT «Семантика subgraph»)
 *     evaluated over the fixture node/edge sets. For the shipped fixtures this
 *     reproduces `subgraph`, `subgraph_truncated` and `subgraph_isolate`
 *     exactly, including omitted_count / omitted_edges.
 */
import type {
  ClustersResponse,
  EntityListResponse,
  EntityResponse,
  EntitySummary,
  Edge,
  ErrorResponse,
  Gid,
  SubgraphResponse,
  SummaryResponse,
} from '@shared/contracts'
import rawFixtures from '@shared/fixtures.json'
import { compareGidAsc } from './format'
import { ROLES, ProviderError, type DataProvider, type ListParams, type SubgraphParams } from './provider'

interface FixtureBundle {
  summary: SummaryResponse
  entity: EntityResponse
  entity_isolate: EntityResponse
  entity_boundary: EntityResponse
  entities: EntityListResponse
  subgraph: SubgraphResponse
  clusters: ClustersResponse
  error_not_found: ErrorResponse
}

/** fixtures.json is the transport example; shared/contracts.ts is its type. */
const fx = rawFixtures as unknown as FixtureBundle

/** Small artificial latency so loading states are actually observable in the UI.
 *  Removed automatically by the HTTP provider. */
const FIXTURE_LATENCY_MS = 160

const sleep = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms))

const NOT_FOUND_MESSAGE = fx.error_not_found.error.message
const CARD_LESS_MESSAGE =
  'Узел есть в fixture-списке, но полная карточка (GET /api/entities/{gid}) для него в наборе отсутствует. Другой dossier не подставляется.'

const ALL_GIDS: ReadonlySet<Gid> = new Set(fx.entities.items.map((item) => item.gid))

const FULL_CARDS = new Map<Gid, EntityResponse>([
  [fx.entity.entity.gid, fx.entity],
  [fx.entity_boundary.entity.gid, fx.entity_boundary],
  [fx.entity_isolate.entity.gid, fx.entity_isolate],
])

/** Contract sort: priority DESC, then gid ASC as a whole integer. */
function byPriorityThenGid(a: EntitySummary, b: EntitySummary): number {
  if (b.priority_score !== a.priority_score) return b.priority_score - a.priority_score
  return compareGidAsc(a.gid, b.gid)
}

function assertPage(offset: number, limit: number): void {
  if (!Number.isInteger(limit) || limit < 1 || limit > 200) {
    throw new ProviderError('INVALID_REQUEST', `limit должен быть целым в диапазоне 1..200, получено ${limit}`)
  }
  if (!Number.isInteger(offset) || offset < 0) {
    throw new ProviderError('INVALID_REQUEST', `offset должен быть целым неотрицательным, получено ${offset}`)
  }
}

function assertGid(gid: Gid): void {
  if (typeof gid !== 'string' || gid.length === 0) {
    throw new ProviderError('INVALID_REQUEST', 'gid обязателен и должен быть строкой', gid ?? null)
  }
  if (!/^\d+$/.test(gid)) {
    throw new ProviderError('INVALID_REQUEST', 'gid должен состоять только из десятичных цифр', gid)
  }
}

export class FixtureDataProvider implements DataProvider {
  readonly mode = 'fixture' as const

  async getSummary(): Promise<SummaryResponse> {
    await sleep(FIXTURE_LATENCY_MS)
    return fx.summary
  }

  async listEntities(params: ListParams): Promise<EntityListResponse> {
    await sleep(FIXTURE_LATENCY_MS)
    assertPage(params.offset, params.limit)
    if (params.role !== undefined && !ROLES.includes(params.role)) {
      throw new ProviderError('INVALID_REQUEST', `Неизвестное значение role: ${String(params.role)}`)
    }
    if (params.cluster_id !== undefined && !Number.isInteger(params.cluster_id)) {
      throw new ProviderError('INVALID_REQUEST', 'cluster_id должен быть целым')
    }

    let items = fx.entities.items
    if (params.role !== undefined) items = items.filter((i) => i.role === params.role)
    if (params.cluster_id !== undefined) items = items.filter((i) => i.cluster_id === params.cluster_id)
    if (params.is_seed !== undefined) items = items.filter((i) => i.is_seed === params.is_seed)

    const total = items.length
    const sorted = [...items].sort(byPriorityThenGid)
    const page = sorted.slice(params.offset, params.offset + params.limit)

    return { meta: fx.entities.meta, items: page, total, offset: params.offset, limit: params.limit }
  }

  async getEntity(gid: Gid): Promise<EntityResponse> {
    await sleep(FIXTURE_LATENCY_MS)
    assertGid(gid)

    const card = FULL_CARDS.get(gid)
    if (card) return card

    // Honest unavailable state: known node, missing full card in this fixture set.
    if (ALL_GIDS.has(gid)) throw new ProviderError('ENTITY_NOT_FOUND', CARD_LESS_MESSAGE, gid)
    throw new ProviderError('ENTITY_NOT_FOUND', NOT_FOUND_MESSAGE, gid)
  }

  async getSubgraph(params: SubgraphParams): Promise<SubgraphResponse> {
    const { gid, hops, limit } = params
    await sleep(FIXTURE_LATENCY_MS)
    assertGid(gid)

    if (!Number.isInteger(hops) || hops < 1 || hops > 2) {
      throw new ProviderError('INVALID_REQUEST', `hops должен быть целым в диапазоне 1..2, получено ${hops}`, gid)
    }
    if (!Number.isInteger(limit) || limit < 1 || limit > 200) {
      throw new ProviderError('INVALID_REQUEST', `limit должен быть целым в диапазоне 1..200, получено ${limit}`, gid)
    }
    if (!ALL_GIDS.has(gid)) throw new ProviderError('ENTITY_NOT_FOUND', NOT_FOUND_MESSAGE, gid)

    const universe = fx.entities.items

    // Undirected adjacency is traversal only; every returned edge keeps its
    // original src → dst direction from the fixture.
    const adjacency = new Map<Gid, Gid[]>()
    for (const node of universe) adjacency.set(node.gid, [])
    for (const edge of fx.subgraph.edges) {
      adjacency.get(edge.src)?.push(edge.dst)
      adjacency.get(edge.dst)?.push(edge.src)
    }

    const distance = new Map<Gid, number>([[gid, 0]])
    let frontier: Gid[] = [gid]
    for (let step = 1; step <= hops && frontier.length > 0; step += 1) {
      const next: Gid[] = []
      for (const current of frontier) {
        for (const neighbour of adjacency.get(current) ?? []) {
          if (!distance.has(neighbour)) {
            distance.set(neighbour, step)
            next.push(neighbour)
          }
        }
      }
      frontier = next
    }

    // Contract order: centre first, then nearest by hops; inside a level
    // priority DESC, gid ASC.
    const candidates = universe
      .filter((node) => distance.has(node.gid))
      .sort((a, b) => {
        const da = distance.get(a.gid) ?? 0
        const db = distance.get(b.gid) ?? 0
        if (da !== db) return da - db
        return byPriorityThenGid(a, b)
      })

    const kept = candidates.slice(0, limit)
    const keptSet = new Set(kept.map((node) => node.gid))
    const candidateSet = new Set(candidates.map((node) => node.gid))

    const inSet = (edge: Edge, set: ReadonlySet<Gid>): boolean => set.has(edge.src) && set.has(edge.dst)
    const totalEdges = fx.subgraph.edges.filter((edge) => inSet(edge, candidateSet))
    const shownEdges = fx.subgraph.edges.filter((edge) => inSet(edge, keptSet))

    const omittedCount = candidates.length - kept.length
    const omittedEdges = totalEdges.length - shownEdges.length

    return {
      meta: fx.subgraph.meta,
      center_gid: gid,
      hops,
      nodes: kept,
      edges: shownEdges,
      total_nodes: candidates.length,
      total_edges: totalEdges.length,
      truncated: omittedCount > 0 || omittedEdges > 0,
      omitted_count: omittedCount,
      omitted_edges: omittedEdges,
    }
  }

  async getClusters(): Promise<ClustersResponse> {
    await sleep(FIXTURE_LATENCY_MS)
    return fx.clusters
  }
}
