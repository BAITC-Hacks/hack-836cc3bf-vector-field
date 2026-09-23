# Pipeline v0

Один запуск читает три Parquet, проверяет схему и согласованность агрегатов, затем создаёт три CSV в официальной схеме и `snapshot.json` для API/Investigator. Ключ LLM не нужен.

Проверено на Python 3.12.6 в Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r pipeline\requirements.txt
.\.venv\Scripts\python.exe -m pipeline --data 'case/data (1)/data' --out pipeline/out
.\.venv\Scripts\python.exe -m unittest pipeline.test_pipeline -v
```

macOS/Linux (требует отдельной проверки на этой ОС):

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r pipeline/requirements.txt
.venv/bin/python -m pipeline --data 'case/data (1)/data' --out pipeline/out
```

Запускать из корня репозитория. `--data` принимает любую папку с `nodes.parquet`, `edges.parquet`, `transactions.parquet`; `--out` принимает папку для результатов. Пути с пробелами заключать в кавычки. По умолчанию используются папки кейса и `pipeline/out`. Результаты: `pipeline/out/nodes_roles.csv`, `pipeline/out/clusters.csv`, `pipeline/out/top_nodes.csv`, `pipeline/out/snapshot.json`. Каталог `pipeline/out` исключён из Git.

Последний проверенный Windows запуск со snapshot: 7.171 секунды после установки зависимостей; 2248 узлов, 3119 рёбер, 4840 транзакций, 35 слабосвязных компонент, 19 изолятов, 105 кластеров.

## Правила

`rules_version=v0`, NetworkX Louvain seed=42, resolution=1. Сначала добавляются все nodes, включая изоляты; затем направленные edges. Louvain использует неориентированную проекцию с суммой обоих направлений, внутри каждой слабосвязной компоненты. Betweenness направленная и невзвешенная. Кластерные номера стабильны для того же snapshot и версий библиотек: сортировка по размеру, затем минимальному gid.

Для каждого положительного признака `p(x)=(число меньших + 0.5 × число равных)/N` среди всех положительных конечных значений по всей сети; `p(0)=0`. Роли из `docs/BUILD_BRIEF.md`: consolidator при ≥3 плательщиках; distributor при ≥10 получателях; transit при наблюдаемом отношении выхода ко входу 0.8–1.2 и ≥2 tx с обеих сторон, исключая seed и depth=4; terminal при отношении ≤0.1, входе на ≥2 датах и последнем входе до 30 июля, исключая seed и depth=4; coordinator требует вместе достижимость от ≥2 seed, betweenness не ниже 90-го квантиля положительных значений и ≥20% межкластерного incident volume. `peripheral` означает недостаточность признаков. Сила сигнала и policy-множитель роли дают `role_score`; подробные веса и пороги в `config.py`. Это эвристические баллы, не вероятность и не измеренная точность.

`priority_score` — сумма шести вкладов: `0.175×p(direct_seed_senders) + 0.175×p(seed_reach_4) + 0.25×p(in_degree) + 0.20×p(max(in_kzt,out_kzt)) + 0.10×p(betweenness) + 0.10×p(out_degree)`. Все вклады остаются в структурированном evidence `snapshot.json` и live API; CSV содержит краткий текст роли и объяснение топа.

## Ограничения

Только внутрибанковские переводы от 5000 KZT за июль 2026, исходящий обход на 4 колена. Входящие за пределами графа и остатки неизвестны. Нулевой выход на depth=4 не доказывает terminal. `out/in` не бухгалтерский баланс, а структурный путь не доказывает происхождение или хронологию средств. Даты точны только до дня. Роли и приоритеты — гипотезы для аналитика без размеченной выборки. GID хранится как int64 внутри Python и полная десятичная строка в CSV; в будущем HTTP/React только строки.

Для ~1 млн узлов точные betweenness и NetworkX/Louvain в памяти потребуют замены на пакетную обработку и приближённые алгоритмы; этот прототип рассчитан на текущий кейс.
