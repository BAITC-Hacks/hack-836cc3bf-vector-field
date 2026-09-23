# Общая live-интеграция

Ветка `codex/integration-live` основана на checkpoint `fbfe5e0` и включает опубликованный frontend `0fd57ad`. В этой ветке pipeline создаёт три официальных CSV и `snapshot.json`; HTTP, четыре Investigator tools и React читают один live snapshot. Контракт v1 не менялся. Fixtures остаются синтетическими.

Проверено на Windows с Python 3.12.6 и Node 22.11.0 (Vite рекомендует 22.12+). Полный pipeline со snapshot занял 7.171 с после установки зависимостей: 2248 узлов, 3119 рёбер, 4840 транзакций, 35 компонент, 19 изолятов, 105 кластеров. `integration.test_live_service` проверяет на реальных Parquet профиль, подграф, ранжирование, общих получателей, exact string gid, evidence, ограничения, пустой результат, неизвестный gid, timeout и AI unavailable. В браузере проверены топ-лист, поиск произвольного gid, изолят, depth=4, стрелки, скрытые соседи 80→200 и AI unavailable.

```powershell
.\.venv\Scripts\python.exe -m pipeline --data 'case/data (1)/data' --out pipeline/out
.\.venv\Scripts\python.exe -m unittest pipeline.test_pipeline -v
.\.venv\Scripts\python.exe -m unittest discover -s agent -p 'test_*.py' -v
.\.venv\Scripts\python.exe -m unittest discover -s integration -p 'test_*.py' -v
cd frontend
npm.cmd run build
```

Повторный полный запуск занял 6.864 с; SHA-256 всех трёх CSV и `snapshot.json` совпали с предыдущим запуском. Прошли 3 теста pipeline, 24 теста agent, 5 интеграционных тестов и frontend build. Реальный model adapter пока отсутствует; `/api/investigate` возвращает `status=unavailable` при валидном запросе. Второй ноутбук/macOS не проверены.

## Исторический checkpoint `fbfe5e0` (до frontend и snapshot/API)

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

## Что отсутствовало на момент checkpoint

The published backend branch currently contains the CSV pipeline, but no backend API or persistent/common JSON snapshot service. `integration/test_pipeline_agent.py` therefore has an explicitly **profile-only test adapter** over `AnalysisResult`; it does not implement subgraph, ranking, common recipients or HTTP. These operations must be provided by the same backend snapshot service used by the UI. Do not present this checkpoint as a complete Investigator or product.

Next merge gate: backend publishes the contract v1 snapshot/API and its own tests; replace this smoke adapter with a live service provider and verify the four tools. Then integrate frontend on a separate reviewed merge step, test exact gid lookup and graph UI, and only then merge into `main`.
