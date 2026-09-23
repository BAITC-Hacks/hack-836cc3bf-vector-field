# Общая live-интеграция

Интеграционный checkout Stage 2 включает pipeline с тремя официальными CSV и `snapshot.json`; HTTP, четыре Investigator tools и React читают один live snapshot. Backend подключает единственный канонический адаптер `agent/openai_model.py` к `/api/investigate` при наличии `OPENAI_API_KEY`, создаёт клиент на время запроса и закрывает его после завершения. Модель по умолчанию — `gpt-5.6-luna`; SDK timeout — 15 секунд, общий deadline Investigator — 30 секунд. Контракт v1 не менялся. Fixtures остаются синтетическими.

Полный pipeline со snapshot занял 3.211 с после установки зависимостей: 2248 узлов, 3119 рёбер, 4840 транзакций, 35 компонент, 19 изолятов, 105 кластеров. Повторный запуск занял 2.998 с; SHA-256 всех трёх CSV и `snapshot.json` совпали. Прошли 3 теста pipeline, 31 тест agent, 2 теста SDK boundary и 14 интеграционных тестов. Frontend build прошёл на Node.js 24.21.0.

`integration.test_live_service` проверяет реальные Parquet, четыре tools, exact string gid, facts и limitations, isolate/boundary, ошибки и таймауты. После AI failure три CSV продолжают отдаваться без изменения байтов. Отдельный синтетический транспортный тест сохраняет leading-zero gid через HTTP, model context, tool и evidence; добавленный ведущий ноль не становится псевдонимом существующего live gid. Необработанная ошибка сервера возвращает `INTERNAL_ERROR` без внутренних деталей.

Текущий browser smoke использует настоящий OpenAI provider без mocks:

- Ranking: completed за 9464 мс, `rank_entities` и три `get_entity_profile`, три findings и девять facts.
- Профиль `100000003115284100`: completed, `get_entity_profile`, два findings и десять facts.

Facts сверены со snapshot, смысл выводов просмотрен отдельно. Число успешных сценариев не доказывает корректность любого свободного ответа. Полный отчёт и статус интеграции: [STAGE2_CLOSURE.md](STAGE2_CLOSURE.md). Не считать merge в `main` завершённым только на основании этой проверки checkout.

Для demo использовать live gid `100000003115284100`, изолят `100000000456947100` и boundary `100000000018102100`. Примеры `900…` в fixture относятся только к учебным данным.

```powershell
.\.venv\Scripts\python.exe -m pipeline --data 'case/data (1)/data' --out pipeline/out
.\.venv\Scripts\python.exe -m unittest pipeline.test_pipeline -v
.\.venv\Scripts\python.exe -m unittest discover -s agent -p 'test_*.py' -v
.\.venv\Scripts\python.exe -m unittest backend.test_openai_model -v
.\.venv\Scripts\python.exe -m unittest discover -s integration -p 'test_*.py' -v
cd frontend
npm.cmd run build
```

Автоматические тесты provider boundary используют mocks и не требуют ключа; описанный browser smoke выполнен отдельно с реальным provider. Без ключа `/api/investigate` возвращает `status=unavailable`. Запуск на втором ноутбуке/macOS не проверен.

Историческая интеграция до Stage 2 проверялась на Windows/Python 3.12.6/Node 22.11.0: pipeline 7.171 с и повтор 6.864 с, детерминированные четыре файла, 24 agent tests, 5 тестов прежнего backend adapter и 10 integration tests. В том checkpoint реального HTTP smoke ещё не было; эти числа не относятся к текущему объединённому adapter.

## Исторический checkpoint `fbfe5e0` (до frontend и snapshot/API)

Branch at that checkpoint: `codex/integration-backend-agent`, merged from the published `codex/backend` and `codex/agent` branches. That checkpoint did not include `codex/frontend`; the following records describe its historical scope, not the current integration state.

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

At that checkpoint, the published backend branch contained the CSV pipeline but no backend API or common JSON snapshot service. `integration/test_pipeline_agent.py` therefore used a **profile-only test adapter** over `AnalysisResult`; this legacy test adapter still does not implement subgraph, ranking, common recipients or HTTP. The current production service and its integration tests provide those operations separately.

The subsequent integration gate was to publish the contract v1 snapshot/API, verify all four tools and integrate the frontend. Those layers are present in the current Stage 2 checkout; final closure is recorded in the report linked above.
