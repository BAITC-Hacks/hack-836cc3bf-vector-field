# Backend + agent integration checkpoint (without frontend)

Branch: `codex/integration-backend-agent`, merged from the published `codex/backend` and `codex/agent` branches. This checkpoint does not merge into `main` and does not include `codex/frontend`.

Verified on Windows, Python 3.12.10, with `pipeline/requirements.txt` installed in `.venv`:

```powershell
.\.venv\Scripts\python.exe -m pipeline --data 'case/data (1)/data' --out pipeline/out
.\.venv\Scripts\python.exe -m unittest pipeline.test_pipeline -v
.\.venv\Scripts\python.exe -m unittest discover -s agent -p 'test_*.py' -v
.\.venv\Scripts\python.exe -m unittest integration.test_pipeline_agent -v
```

Observed result: 2248 nodes, 3119 edges, 4840 transactions, 35 weak components, 19 isolates, 105 clusters; complete CSV run 2.947 seconds after dependency installation. The pipeline's 3 tests, agent's 24 tests, and integration's 2 tests passed.

The integration test uses the **real in-memory `AnalysisResult.profiles`** from the three Parquet files. It checks one mixed profile, an isolated seed, and a depth=4 node through `agent.investigate` with a scripted model, exact string gids, trusted evidence references and limitations. It also checks all 2248 profiles have six priority facts whose sum matches `priority_score`. The scripted model is test-only; no live LLM or API key is used.

## Still needed for full integration

The published backend branch currently contains the CSV pipeline, but no backend API or persistent/common JSON snapshot service. `integration/test_pipeline_agent.py` therefore has an explicitly **profile-only test adapter** over `AnalysisResult`; it does not implement subgraph, ranking, common recipients or HTTP. These operations must be provided by the same backend snapshot service used by the UI. Do not present this checkpoint as a complete Investigator or product.

Next merge gate: backend publishes the contract v1 snapshot/API and its own tests; replace this smoke adapter with a live service provider and verify the four tools. Then integrate frontend on a separate reviewed merge step, test exact gid lookup and graph UI, and only then merge into `main`.
