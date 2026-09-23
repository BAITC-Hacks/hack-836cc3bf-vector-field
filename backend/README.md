# Live snapshot API

Запускать из корня после `python -m pipeline --data 'case/data (1)/data' --out pipeline/out`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

`backend/service.py` один раз читает `pipeline/out/snapshot.json` при старте процесса. HTTP routes и четыре Investigator tools делегируют одному `SnapshotService`; роли, scores и evidence не пересчитываются на запросах. Если собран `frontend/dist`, FastAPI отдаёт его по `/`.

Реализованы contract v1 routes: `/api/summary`, `/api/entities`, `/api/entities/{gid}`, `/api/subgraph`, `/api/clusters`, `/api/export/{filename}`, `/api/investigate`. Export ограничен тремя официальными CSV. Все gid в JSON — точные десятичные строки. При наличии `OPENAI_API_KEY` `/api/investigate` создаёт адаптер OpenAI Responses только на время запроса и использует модель `gpt-5.6-luna` по умолчанию (`OPENAI_MODEL` задаёт другую). Общий deadline Investigator — 30 секунд. Без ключа endpoint возвращает `status=unavailable`; core routes продолжают работать. При отсутствии snapshot API возвращает `SNAPSHOT_NOT_READY`.

Для AI установите переменные в том же окружении, где запускается FastAPI, **до запуска сервера**:

```powershell
# Windows PowerShell, из корня репозитория
$env:OPENAI_API_KEY="<ваш API key>"
$env:OPENAI_MODEL="gpt-5.6-luna"
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

```bash
# macOS/Linux, из корня репозитория
export OPENAI_API_KEY='<ваш API key>'
export OPENAI_MODEL='gpt-5.6-luna'
.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

После изменения переменных окружения перезапустите сервер. `.env.example` показывает имена переменных, но файл `.env` сам по себе не загружается. Адаптер посылает `store=False` и передаёт контекст инструментов между model calls внутри запроса; это отключает хранение состояния Responses, но не меняет правила хранения данных для мониторинга злоупотреблений на стороне API. Исторический provider smoke описан в agent/README.md; текущий browser gate фиксируется отдельно в integration/STAGE2_CLOSURE.md.

Проверка: `.\.venv\Scripts\python.exe -m unittest integration.test_live_service -v`. Тест использует реальные Parquet, проверяет все четыре tools, live HTTP, неизвестный gid, пустое пересечение, изолят, depth=4, timeout и AI outage. Адаптер Responses проверяется отдельными тестами без сетевого вызова.

Настоящий сетевой API smoke: `python -m agent.live_smoke --scenario all`. Канонический адаптер — `agent/openai_model.py`; backend создаёт его на запрос и закрывает клиент в `finally`.
