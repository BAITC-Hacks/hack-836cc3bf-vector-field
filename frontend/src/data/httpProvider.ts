/** Default live HTTP data provider — contract v1 routes from docs/API_CONTRACT.md. */
import type {
  ClustersResponse,
  EntityListResponse,
  EntityResponse,
  ErrorResponse,
  Gid,
  SubgraphResponse,
  SummaryResponse,
} from '@shared/contracts'
import { ProviderError, type DataProvider, type ErrorCode, type ListParams, type SubgraphParams } from './provider'

const BASE = (import.meta.env.VITE_API_BASE ?? '').replace(/\/+$/, '')

function codeFromStatus(status: number): ErrorCode {
  if (status === 404) return 'ENTITY_NOT_FOUND'
  if (status === 409) return 'SNAPSHOT_MISMATCH'
  if (status === 422) return 'INVALID_REQUEST'
  if (status === 503) return 'SNAPSHOT_NOT_READY'
  return 'INTERNAL_ERROR'
}

function query(params: Record<string, string | number | undefined>): string {
  const sp = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) sp.set(key, String(value))
  }
  const encoded = sp.toString()
  return encoded ? `?${encoded}` : ''
}

async function request<T>(path: string): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${BASE}${path}`, { headers: { Accept: 'application/json' } })
  } catch (cause) {
    const detail = cause instanceof Error ? cause.message : String(cause)
    throw new ProviderError('INTERNAL_ERROR', `API недоступен: ${detail}`)
  }

  const text = await response.text()

  if (!response.ok) {
    let code = codeFromStatus(response.status)
    let message = `HTTP ${response.status}`
    try {
      const parsed = JSON.parse(text) as Partial<ErrorResponse>
      if (parsed && typeof parsed === 'object' && parsed.error && typeof parsed.error.code === 'string') {
        code = parsed.error.code
        message = parsed.error.message
      }
    } catch {
      // Not a JSON error body — keep the status-derived code.
    }
    throw new ProviderError(code, message)
  }

  try {
    return JSON.parse(text) as T
  } catch {
    throw new ProviderError('INTERNAL_ERROR', 'Ответ API не является корректным JSON')
  }
}

export class HttpDataProvider implements DataProvider {
  readonly mode = 'live' as const

  getSummary(): Promise<SummaryResponse> {
    return request<SummaryResponse>('/api/summary')
  }

  listEntities(params: ListParams): Promise<EntityListResponse> {
    return request<EntityListResponse>(
      `/api/entities${query({
        role: params.role,
        cluster_id: params.cluster_id,
        is_seed: params.is_seed === undefined ? undefined : String(params.is_seed),
        offset: params.offset,
        limit: params.limit,
      })}`,
    )
  }

  getEntity(gid: Gid): Promise<EntityResponse> {
    return request<EntityResponse>(`/api/entities/${encodeURIComponent(gid)}`)
  }

  getSubgraph(params: SubgraphParams): Promise<SubgraphResponse> {
    return request<SubgraphResponse>(
      `/api/subgraph${query({ gid: params.gid, hops: params.hops, limit: params.limit })}`,
    )
  }

  getClusters(): Promise<ClustersResponse> {
    return request<ClustersResponse>('/api/clusters')
  }
}
