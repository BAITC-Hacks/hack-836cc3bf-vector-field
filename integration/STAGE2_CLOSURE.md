# Stage 2: integration verification — 23 September 2026

Integration gate: **PASS**. Final main smoke and publication: pending the final integration step below. This report distinguishes real browser/model checks from SDK mocks.

## Integrated sources and decisions

- Base: `origin/main` at `e5dc17d` (local main was still at `d0bd17e`).
- Frontend: `origin/codex/frontend` at `91cb23a`.
- Agent: `origin/codex/agent` at `96cfcba`, including `878d5b8` and its live-provider closure.
- Backend: `origin/codex/daulet-ai-runtime` at `8c246b2`. The older backend/integration refs were already ancestors of main and were not applied twice.
- Remote refs were fetched again during integration. No newer published frontend hotfix was present at that check.
- Work ran in a separate `codex/stage2-final` worktree. Existing agent worktree and uncommitted work were not changed. No reviewer-only branches were merged.

One adapter remains: `agent/openai_model.py`, default `gpt-5.6-luna`, configurable with `OPENAI_MODEL`. Backend preserves lazy creation per request, client cleanup, bounded execution, request validation and safe error mapping. The competing backend adapter was removed; useful real SDK serialization tests were retained against the canonical adapter. Backend includes the agent requirements; OpenAI has one version pin.

Transport v1, shared types/fixtures, CSV schemas and analytical rules are unchanged. The same pipeline snapshot/service supplies API and tools; no alternate ranking or score implementation was added. GID-to-integer conversion in Python sorting is only a comparison key; identifiers and lookups remain exact strings, including leading zeros.

Two P1 fixes: unexpected HTTP errors now return v1 `INTERNAL_ERROR` JSON without internal details; clicking a finding's gid focuses and scrolls to its graph, with a direct link to the existing dossier. Priority meaning is explicit beside the findings. No new tool, endpoint, analytics or redesign was introduced.

## Reproducible core and tests

Windows, Python 3.14.7, Node 24.21.0. Pinned pandas 3.0.6 / NumPy 2.5.3 / PyArrow 25.0.1 / NetworkX 3.7 / OpenAI 3.19.0.

| Check | Actual result |
|---|---|
| `python -m pipeline --data "case/data (1)/data" --out pipeline/out` without a key | 3.211 seconds; repeat 2.998 seconds |
| Determinism | All three CSV and snapshot SHA-256 hashes identical across both runs |
| `python -m unittest pipeline.test_pipeline -v` | 3 PASS |
| `python -m unittest discover -s agent -p "test_*.py" -v` | 31 PASS |
| `python -m unittest backend.test_openai_model -v` | 2 PASS; actual SDK transport, mocked network |
| `python -m unittest discover -s integration -p "test_*.py" -v` | 14 PASS; real Parquet, mocked model/provider where applicable |
| `npm.cmd ci` and `npm.cmd run build` in frontend | PASS; no package/lockfile changes |

2248 nodes, 3119 edges, 4840 transactions, 35 weak components (16 with edges), 19 isolates, 105 clusters, 444 boundary nodes. All 97 repeated transaction rows retained. CSV rows: 2248 / 105 / 100; longest short evidence: 91 characters. Coverage, finite scores, six priority contributions, tie sorting, amount/count aggregates, cluster membership and depth=4 exclusion from terminal were checked.

Snapshot: `ffc9f16fa9385251100f6cf1`.

| File | SHA-256 |
|---|---|
| nodes_roles.csv | `a91acc22a64067ed0bf38ade1b95931becae5b24ff453bc359bb1871e4d0ccf1` |
| clusters.csv | `d15c7c481688cf33783391d7c965992171c9e6ec206aa06512ecadf4bf897c17` |
| top_nodes.csv | `15514a67b2c4102221cf1a8ad1c6d584c7750be714765764f90037a090e315cf` |
| snapshot.json | `c2e7d1611cc58df1447ddf9dc74063ad273e2fcaf895412a135a0e3214aaaafd` |

## Real browser and provider gate

The built React app was served by actual Uvicorn/FastAPI on localhost:8012, with live mode and the real snapshot. No temporary endpoint, fixture response or scripted model was used for these browser scenarios. The credential was loaded only into the server environment from an ignored local file; no credential is committed.

- A: a natural-language global ranking question with no selected gid displayed loading, then completed. Real model selected `rank_entities`, followed by three profile tools through the service. First run: 3 findings / 9 facts / 4 real tool calls, 9464 ms in backend logs. Repeat after the UX fix: 3 findings / 12 facts, 9212 ms. Model wording varies; citations are validated against snapshot facts.
- B: a question about `100000003115284100` displayed loading then completed, with `get_entity_profile`, 2 findings and 10 facts. Role and priority were explained separately. Exact gid and fact values matched the profile.
- Completed findings, numeric evidence, limitations and actual tool trace were displayed. Priority was described as investigation priority, not a crime probability. Text was reviewed separately from schema validation.
- A finding link to `100000007908818100` visibly scrolled/focused its directed graph (11 nodes / 11 edges); the dossier link displayed that exact node. The original question context remained attached to the AI answer.
- Search/card/graph: `100000003115284100` has 10 nodes / 11 edges, no truncation. Isolate `100000000456947100` has a full card and explicit no-links message. Boundary `100000000018102100` is depth=4/peripheral with truncation limitations. Unknown `999999999999999999` shows ENTITY_NOT_FOUND.
- All three CSV links triggered successful browser downloads. HTTP response bytes separately matched the original pipeline SHA-256 hashes and attachment filenames.
- Missing credentials was exercised in the actual browser before credentials were loaded: honest unavailable, no invented findings. Unit/integration tests additionally exercise provider failure, timeout and bad tool arguments, followed by working search/profile/graph and byte-identical exports. Leading-zero gid roundtrip and a non-aliasing 404 are covered.

Environment issue resolved: CSV generated by the sandbox account initially could not be read by the ordinary server account. Re-running the unchanged pipeline under the same account as the API took 2.714 seconds and restored downloads with identical bytes. No ACL/security change or analytical code workaround was added.

## Remaining limits

- macOS and a second laptop were unavailable; no claim of execution there.
- P2: Vite reports a >500 kB bundle; no scope-expanding optimization was made.
- Optional live common-recipient/subgraph model scenarios were not required for A+B closure. All four service tools are covered by integration tests.
- Citation validation and the two smoke scenarios do not prove every possible free-form model statement. Existing data/observability limitations remain.

## Final main gate

Pending: safely merge the verified integration branch, repeat smoke on main, verify clean status and push main without rewriting history.
