# Live snapshot API

Запускать из корня после `python -m pipeline --data 'case/data (1)/data' --out pipeline/out`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

`backend/service.py` один раз читает `pipeline/out/snapshot.json` при старте процесса. HTTP routes и четыре Investigator tools делегируют одному `SnapshotService`; роли, scores и evidence не пересчитываются на запросах. Если собран `frontend/dist`, FastAPI отдаёт его по `/`.

Реализованы contract v1 routes: `/api/summary`, `/api/entities`, `/api/entities/{gid}`, `/api/subgraph`, `/api/clusters`, `/api/export/{filename}`, `/api/investigate`. Export ограничен тремя официальными CSV. Все gid в JSON — точные десятичные строки. AI model adapter пока не подключён, поэтому `/api/investigate` при валидном запросе возвращает `status=unavailable`; core routes продолжают работать. При отсутствии snapshot API возвращает `SNAPSHOT_NOT_READY`.

Проверка: `.\.venv\Scripts\python.exe -m unittest integration.test_live_service -v`. Тест использует реальные Parquet, проверяет все четыре tools, live HTTP, неизвестный gid, пустое пересечение, изолят, depth=4, timeout и AI outage.
