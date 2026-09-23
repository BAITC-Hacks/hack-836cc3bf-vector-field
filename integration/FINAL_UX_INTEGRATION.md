# Final frontend integration — 23 September 2026

PASS: `codex/frontend` commit `ea0693d` integrated over verified main `067cc70` as `77c8e18`. Only frontend changed; backend, agent, pipeline, transport contracts and dependency locks are identical to the verified base. Merge conflicts preserve the observed out/in disclaimer and selected boundary highlight.

## Production UI on the real snapshot

Tested at `http://127.0.0.1:8000/`, snapshot `e4b834b7ab30665ff544d2e4`, Python 3.14.7 / Node 24.21.0. TypeScript and Vite production build PASS. No JavaScript errors during the successful exact-node / AI path.

| Scenario | Result |
|---|---|
| Initial page | First ranked GID selected from summary; network question context remains explicit |
| Real global question | Completed; 3 findings / 9 exact facts / 4 real tool calls; whole-network context despite selected top node |
| Finding → graph | Real global finding opens `100000003115284100`, exact dossier and 10 nodes / 11 directed edges |
| Real selected-node question | Completed; exact selected GID, 3 findings / 10 exact facts / 1 tool call |
| Isolate `100000000456947100` | 1 node / 0 edges, full dossier, observation-gap explanation |
| Boundary `100000000018102100` | Depth 4 and explicit warning: absent observed outflow does not establish terminal |
| Unknown `999999999999999999` | ENTITY_NOT_FOUND, no stale dossier; selected-context submit disabled |
| Truncation | Limit 2 shows 8 omitted nodes / 10 omitted edges; expansion restores 10 / 11 |
| Other component `100000002578405100` | Expand to 117 nodes / 118 edges; overview control works |
| Exports | All 3 browser downloads triggered; HTTP bodies byte-match submission CSVs and manifest |
| Backup | Updated production frontend; all 7 artifact hashes verified; CSV and snapshot unchanged |

Global question: «Какие узлы проверить первыми и почему?» (radio «Вся сеть»).
Selected question: «Что известно об узле 100000003115284100 и какие признаки поддерживают его приоритет?» (radio «Выбранный узел»).

The existing 52 Python tests and fresh-checkout deterministic pipeline evidence remain applicable to unchanged core files; see [FINAL_GATE.md](FINAL_GATE.md). This UI update was checked with production build and the browser scenarios above, not represented as a new core-test run.

Local installation note: a new `npm ci` stopped at ENOSPC. Its incomplete directory was removed and the previously installed dependencies from the identical lockfile were reused for this build. A fresh dependency installation had passed in the base gate. Disk cleanup beyond this task's temporary files was not performed.

## Product fit and limits

The core use case is complete: queue → numerical reasons → observed directed links → next checks. Role and priority remain separate. Roles/priority are heuristics without labeled accuracy validation; AI prose is only partially mechanically checked. Cluster computation/export is complete, while interactive cluster exploration remains basic. One-million-node scaling is documented, not implemented; second-device/macOS verification remains unavailable. At narrow widths the card is below the central column and reachable by «Карточка узла»; large graphs can require «Всё окружение».

No API key or model response was added to the repository or backup.
