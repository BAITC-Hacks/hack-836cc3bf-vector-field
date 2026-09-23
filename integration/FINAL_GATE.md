# Submission closure — 2026-09-23

Core gate: **PASS**. Final technical/demo gate: **PASS**. After the user's explicit approval, both real OpenAI browser questions completed on the final snapshot, and finding → graph/card was verified. The earlier approval block is resolved; no mock result is presented as live. The credential was held only in the server process environment and was not written to repository files or application logs.

Worktree branch: `codex/submission-gate`, based on `e531df0`. Other local team worktrees were not changed. Final publication/integration state is recorded in GitHub PR #2. Feature freeze retained; no new analytics, routes, tools or transport fields.

## Closed issues

- Role predicates used in terminal/coordinator explanations now survive as structured evidence, along with role-specific counts/amounts. The UI and tools consume those exact snapshot facts. Scores, role selection, cluster assignment and all CSV bytes remain unchanged.
- English and Russian priority claims both require priority evidence; the demonstrated English claim citing only degree is rejected. Global smoke now sends an empty selected_gids list.
- A selected boundary node keeps its centre highlight and dashed boundary; out/in no longer has a misleading share label.
- Python LF/CRLF differences no longer alter snapshot identity. Actual source changes and binary Parquet changes still do.
- Added a dependency lock, one-command demo launcher, exact demo/recovery script and checked-in CSV/backup deliverables.

## Evidence matrix

The category numbers below identify the official rubric; they are not awarded marks or predictions.

| Rubric category | Available evidence |
|---|---|
| 25/25 Correspondence/working | 2248 nodes, 105 clusters, 100 ranked nodes; directed graph, full-dataset search, all CSV exports |
| 25/25 Technical | one deterministic snapshot, exact string gid, six priority facts, role predicate evidence, bounded read-only agent, regression suite |
| 25/25 README/reproducibility | clean venv install, pinned lock, repeated/isolated-source CLI, newline invariance, tested backup restoration |
| 15/15 Value | priority → role/evidence → graph → next checks; isolate and boundary explained without overclaiming |
| 10/10 Potential/originality | observable-data limitations and documented ~1M-node scaling path; no unsupported accuracy/ROI claim |

## Commands and results

Windows, Python 3.14.7, Node 24.21.0. Dependencies installed into a new `.venv` with `pip install -r backend/requirements.txt`; resolved versions recorded in `requirements-lock.txt`, reinstallation/check passed. `npm.cmd ci` passed, 0 reported vulnerabilities; `npm.cmd run build` passed after final frontend changes.

| Command (using .venv Python from repository root) | Result |
|---|---|
| `python -m pipeline --data "case/data (1)/data" --out pipeline/out` without key | 3.339s and 3.073s; all four files byte-identical |
| `python -m unittest pipeline.test_pipeline -v` | 4 PASS |
| `python -m unittest discover -s agent -p "test_*.py" -v` | 32 PASS |
| `python -m unittest backend.test_openai_model -v` | 2 PASS; real SDK, mocked network |
| `python -m unittest discover -s integration -p "test_*.py" -v` | 14 PASS; real Parquet, mocked model where applicable |
| `npm.cmd run build` (frontend) | PASS, TypeScript and production Vite |
| Restore backup to empty temporary directory | checksums, built UI, summary, all export bytes, AI unavailable PASS |

Isolated-source reproduction copied tracked current sources/data into a fresh directory, stripped API key and Python path overrides, asserted imports came from that directory and CLI imported no agent/OpenAI modules. With all Python sources deliberately converted to CRLF: 2.882s and byte-identical CSV/snapshot. This is a same-machine cold-source test; another physical laptop/macOS was unavailable.

Actual staged Git checkout with `core.autocrlf=true` into a fresh directory also passed: 3.250s; Python became CRLF, submitted CSVs stayed LF, all generated artifacts and backup matched the manifest.

Negative data check: corrupting one edge sum by 0.01 KZT exits 2 with a clear aggregate mismatch; no success output, existing verified artifacts preserved.

Combined final run of all modules: **52 tests PASS in 13.283s**. Final port 8000 summary and all three HTTP export hashes match the manifest.

## Dataset/contract gates

2248/3119/4840 nodes/edges/transactions; 35 weak components (16 with edges), 19 isolates, 444 depth=4 nodes, 105 clusters. All 97 repeated transaction rows preserved; exact total 36589001201 tiyn. CSV rows 2248/105/100, finite scores, exact coverage/sorting, short numeric evidence, cluster membership/internal sums, boundary exclusion from terminal and six priority contributions verified. Strict JSON, exact string IDs in all nested fields and null ratio for zero inflow passed. Contract version 1 and analytical rules v0 unchanged; additional Evidence metric names fit the existing schema.

Snapshot `e4b834b7ab30665ff544d2e4`. Full artifact SHA-256 values are in `submission/manifest.json`.

## Browser evidence

Actual built React + Uvicorn + real pipeline snapshot, no fixture success response. No-key behavior was first checked with `scripts/demo.py --no-ai`. After explicit user approval, the final server on port 8000 used the real `gpt-5.6-luna` adapter with the credential only in its environment. Both browser requests used snapshot `e4b834b7ab30665ff544d2e4`. No runtime changes were needed to pass these live checks.

| Scenario | Observed |
|---|---|
| Global question | PASS: no selection, loading → completed; rank_entities + 3 get_entity_profile calls; 3 findings, 12 displayed exact facts; 10860 ms |
| Exact node | PASS: `100000003115284100`, loading → completed; one get_entity_profile call, 3 findings/10 facts, 7736 ms. Exact dossier: 8 senders/15 input tx/2160500 KZT; 10 graph nodes/11 directed edges |
| Finding → graph | PASS: clicked exact gid 100000003115284100 in real global finding; focus moved to its graph; exact dossier loaded; 10 nodes/11 directed edges and arrows inspected in screenshot |
| Isolate | `100000000456947100`: full card, 0 links, null ratio, data-gap explanation |
| Boundary | `100000000018102100`: depth=4/peripheral, limitation visible, 2 nodes/1 edge |
| Other component | `100000002578405100`: distributor, 116 recipients, 117 ego nodes/118 edges; component size 270 verified independently |
| Unknown | `999999999999999999`: ENTITY_NOT_FOUND in card/graph, no stale substitute |
| Truncation | limit=2: 8 hidden nodes/10 hidden edges; expand returns 10 nodes/11 edges |
| Exports | all three browser downloads; HTTP bytes equal pipeline SHA-256 |
| Visual | arrows, node labels, selected centre and role legend inspected in screenshot |

## Secrets and limits

Pattern audit: 93 tracked files (90 text/3 Parquet) and 32 locally reachable commits/176 distinct blobs (173 text) before closure commit. No confirmed tokens, private keys, JWT/Bearer literals, credential URLs or tracked `.env`/cache/dependencies. Historical broad assignment candidates were documentation placeholders. The backup is built from an explicit artifact/UI allowlist and contains no environment files or model responses. All 20 staged closure files, including each backup archive member, were additionally checked for token/private-key patterns and prohibited environment/dependency paths; no findings. This is a scoped pattern audit, not a guarantee about ignored files, dangling history or arbitrary binary contents.

Known limitations: July 2026, intrabank ≥5000 KZT, incomplete inflow, depth/day/period censoring; heuristic scores; no ground truth; free-text semantic validation remains partial. Model/provider latency and availability are external. A second physical device and macOS were not available. Output replacement is per-file; avoid recalculation while serving a snapshot and use the checked backup after a disk/lock failure.

Deferred P2: ~718 kB frontend bundle; queue/graph result caps and no dedicated clear-selection control; explicit Pydantic response models; stronger free-text semantics. No scope-expanding fixes were made.

## Demo and publication

Commands, first question, exact nodes, solution diagram and 5-minute sequence: `docs/DEMO.md`. Backup: `submission/backup.zip`. Main is left as the team integration base. The closure code/artifact commit `2faa74c` is published to `origin/codex/submission-gate`. The first combined commit/push was rejected and did not execute. A subsequent read-only provenance check after fresh fetch proved that `origin/main` already holds exactly the three Parquet inputs (edges blob `a2f957eac43af647391523a5da77c625f5e12b66`, nodes `a312bab63f4e5c4ed4471298789ffbdea612c1d7`, transactions `ab7f49293607c32f28f3daa9403fc7b0ea903ec1`). With this new evidence, automatic approval review allowed the same-repository feature-branch push; no access or visibility change occurred. The user subsequently explicitly approved the two OpenAI demo scenarios; the live results above close that separate gate. The final task response records HEAD and final PR state. PR: https://github.com/BAITC-Hacks/hack-836cc3bf-vector-field/pull/2. No judge portal/destination was supplied, so no external contest submission is claimed.
