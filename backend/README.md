# Live snapshot API

Запускать из корня после `python -m pipeline --data 'case/data (1)/data' --out pipeline/out`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

`backend/service.py` один раз читает `pipeline/out/snapshot.json` при старте процесса. HTTP routes и четыре Investigator tools делегируют одному `SnapshotService`; роли, scores и evidence не пересчитываются на запросах. Если собран `frontend/dist`, FastAPI отдаёт его по `/`.

Реализованы contract v1 routes: `/api/summary`, `/api/entities`, `/api/entities/{gid}`, `/api/subgraph`, `/api/clusters`, `/api/export/{filename}`, `/api/investigate`. Export ограничен тремя официальными CSV. Все gid в JSON — точные десятичные строки. При `OPENAI_API_KEY` backend создаёт OpenAI Investigator adapter; модель настраивается через `OPENAI_MODEL` (по умолчанию `gpt-6-luna`). Без ключа `/api/investigate` возвращает `status=unavailable`; core routes продолжают работать. При отсутствии snapshot API возвращает `SNAPSHOT_NOT_READY`.

Проверка: `.\.venv\Scripts\python.exe -m unittest discover -s integration -p 'test_*.py' -v`. Тесты используют реальные Parquet, проверяют четыре tools, HTTP, точные gid, evidence, timeout, AI outage и model adapter с подменой только внешнего provider boundary. Для настоящего сетевого smoke с ключом: `.\.venv\Scripts\python.exe -m agent.live_smoke --scenario all`.
