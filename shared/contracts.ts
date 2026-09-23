/** Transport contract v1. HTTP handlers live in backend/app.py.
 * All GIDs MUST remain strings. Fixtures are synthetic and explicitly marked.
 */
export type Gid = string;
export type Role = 'consolidator' | 'transit' | 'distributor' | 'terminal' | 'coordinator' | 'peripheral';
export interface Meta {
  contract_version: '1';
  snapshot_id: string;
  rules_version: string;
  data_mode: 'fixture' | 'live';
}
export interface Evidence {
  evidence_id: string;
  gid: Gid;
  metric: string;
  value: number | string | null;
  unit: 'count' | 'KZT' | 'ratio' | 'text';
  rule_id: string;
  source: 'nodes.parquet' | 'edges.parquet' | 'transactions.parquet' | 'derived';
  scope: string;
  text: string;
  limitations: string[];
}
export interface Metrics {
  in_degree: number;
  out_degree: number;
  in_kzt: number;
  out_kzt: number;
  in_tx: number;
  out_tx: number;
  pass_through: number | null;
  direct_seed_senders: number;
  seed_reach_4: number;
  betweenness: number;
}
export interface EntitySummary {
  gid: Gid;
  depth: number;
  is_seed: boolean;
  role: Role;
  role_score: number;
  priority_score: number;
  cluster_id: number;
  evidence: string; // short role explanation, <=200 characters
  why: string; // priority explanation
  limitations: string[];
}
export interface Entity extends Omit<EntitySummary, 'evidence'> {
  evidence_text: string;
  metrics: Metrics;
  evidence: Evidence[];
  secondary_roles: Role[];
  next_checks: string[];
}
export interface EntityResponse { meta: Meta; entity: Entity }
export interface EntityListResponse {
  meta: Meta; items: EntitySummary[]; total: number; offset: number; limit: number;
}
export interface SummaryResponse {
  meta: Meta;
  period: { from: string; to: string };
  counts: {
    n_nodes: number; n_edges: number; n_transactions: number; n_seed: number;
    n_components: number; n_components_with_edges: number; n_isolates: number;
    n_depth_truncated: number; n_clusters: number;
  };
  total_observed_kzt: number;
  limitations: string[];
  top_nodes: EntitySummary[];
}
export interface Edge { src: Gid; dst: Gid; sum_kzt: number; n_tx: number }
export interface SubgraphResponse {
  meta: Meta;
  center_gid: Gid;
  hops: number;
  nodes: EntitySummary[];
  edges: Edge[];
  total_nodes: number;
  total_edges: number;
  truncated: boolean;
  omitted_count: number; // hidden nodes, not edges
  omitted_edges: number;
}
export interface Cluster {
  cluster_id: number; n_nodes: number; n_seed: number; sum_kzt_internal: number;
  top_gids: Gid[]; hypothesis: string;
}
export interface ClustersResponse { meta: Meta; items: Cluster[] }
export interface InvestigationRequest { question: string; selected_gids: Gid[]; snapshot_id: string }
export interface Finding {
  text: string; gids: Gid[]; evidence_ids: string[]; limitations: string[];
}
export interface ToolCall {
  name: string;
  status: 'completed' | 'failed';
  duration_ms: number;
  evidence_ids: string[];
}
export interface InvestigationResponse {
  meta: Meta;
  status: 'completed' | 'unavailable' | 'timeout' | 'failed';
  message: string;
  findings: Finding[];
  evidence: Evidence[]; // resolves every finding evidence_id within this response
  limitations: string[];
  next_checks: string[];
  tool_calls: ToolCall[];
}
export interface ErrorResponse {
  error: {
    code: 'INVALID_REQUEST' | 'ENTITY_NOT_FOUND' | 'SNAPSHOT_NOT_READY' | 'SNAPSHOT_MISMATCH' | 'INTERNAL_ERROR';
    message: string;
  };
}
export interface CommonRecipientsRequest { gids: Gid[]; max_hops: number; limit: number }
export interface CommonRecipient {
  gid: Gid;
  paths: { source_gid: Gid; gids: Gid[] }[];
}
export interface CommonRecipientsResponse {
  meta: Meta;
  selected_gids: Gid[];
  mode: 'direct' | 'reachable';
  max_hops: number;
  items: CommonRecipient[];
  total: number;
  truncated: boolean;
  limitations: string[];
}
