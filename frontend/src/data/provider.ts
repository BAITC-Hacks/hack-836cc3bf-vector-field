/** Data-provider boundary.
 *
 * Components depend only on this interface. Today the app runs on
 * `FixtureDataProvider` (shared/fixtures.json); switching to `HttpDataProvider`
 * is a one-line change in `createDataProvider()` and does not touch components.
 *
 * All gid values are decimal STRINGS end to end. Nothing in this layer may
 * apply Number(), parseInt() or unary + to a gid.
 */
import type {
  ClustersResponse,
  EntityListResponse,
  EntityResponse,
  Gid,
  Role,
  SubgraphResponse,
  SummaryResponse,
} from '@shared/contracts'

export type ErrorCode =
  | 'INVALID_REQUEST'
  | 'ENTITY_NOT_FOUND'
  | 'SNAPSHOT_NOT_READY'
  | 'SNAPSHOT_MISMATCH'
  | 'INTERNAL_ERROR'

export class ProviderError extends Error {
  readonly code: ErrorCode
  readonly gid: Gid | null

  constructor(code: ErrorCode, message: string, gid: Gid | null = null) {
    super(message)
    this.name = 'ProviderError'
    this.code = code
    this.gid = gid
  }
}

export function toProviderError(err: unknown): ProviderError {
  if (err instanceof ProviderError) return err
  if (err instanceof Error) return new ProviderError('INTERNAL_ERROR', err.message)
  return new ProviderError('INTERNAL_ERROR', String(err))
}

export const ROLES: readonly Role[] = [
  'consolidator',
  'transit',
  'distributor',
  'terminal',
  'coordinator',
  'peripheral',
]

export interface ListParams {
  role?: Role
  cluster_id?: number
  is_seed?: boolean
  offset: number
  limit: number
}

export interface SubgraphParams {
  gid: Gid
  hops: number
  limit: number
}

export interface DataProvider {
  /** `fixture` = synthetic shared/fixtures.json. `live` = local calculated snapshot. */
  readonly mode: 'fixture' | 'live'
  getSummary(): Promise<SummaryResponse>
  listEntities(params: ListParams): Promise<EntityListResponse>
  /** Rejects with ProviderError ENTITY_NOT_FOUND for unknown or card-less gid. */
  getEntity(gid: Gid): Promise<EntityResponse>
  getSubgraph(params: SubgraphParams): Promise<SubgraphResponse>
  getClusters(): Promise<ClustersResponse>
}
