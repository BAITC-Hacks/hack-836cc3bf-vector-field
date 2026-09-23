# Контракт v1: frontend ↔ backend ↔ Investigator

Статус: зафиксированная спецификация для реализации. Реальных HTTP handlers, Pydantic-моделей и интеграционного теста пока нет. Согласованные формы: `shared/contracts.ts`; синтетические примеры: `shared/fixtures.json`. Frontend может начать сразу. Backend реализует именно эти формы; agent использует те же profile/subgraph/list функции.

Этот документ уточняет прежнее текстовое описание в BUILD_BRIEF/README. При различиях transport-полей контракт v1 имеет приоритет; требования CSV из официального кейса остаются неизменными. Семантика правил ролей остаётся в BUILD_BRIEF.

## Общие правила

- Все gid/src/dst — строки из десятичных цифр. В URL также точная строка. Cluster ID — integer. Деньги в transport — number KZT, округление до 0.01; расчёты с контролируемой точностью внутри pipeline.
- Каждый успешный ответ содержит `meta`: `contract_version="1"`, `snapshot_id`, `rules_version`, `data_mode=fixture|live`.
- Fixture — синтетический пример интерфейса. Его scores не являются рассчитанными результатами исходного кейса. Live означает рассчитанные локальные данные, не подключение к банковскому API.
- Backend выдаёт один согласованный snapshot. Его ID связан с hashes данных/config; при новом расчёте ID меняется. Не смешивать карточку из одного snapshot с AI-ответом другого.
- Все поля типов обязательны. Коллекции могут быть пустыми; `pass_through` может быть null. NaN/Infinity запрещены. Nullable поле не заменять отсутствующим ключом.
- Ограничения — коды string[], next_checks — готовые человекочитаемые предложения. UI отображает известные коды по словарю ниже, неизвестные — нейтральным текстом без падения.
- `EntitySummary.evidence` — короткий текст; `Entity.evidence` — массив фактов. Для полной карточки краткий текст называется `evidence_text`. Это намеренное различие, закреплённое типами.
- Полные факты имеют уникальные evidence_id внутри snapshot. Их значения и тексты генерирует deterministic layer, не модель.

## HTTP

| Method / route | Параметры | Ответ |
|---|---|---|
| GET `/api/summary` | Нет | SummaryResponse; top_nodes — top 20 из полного snapshot |
| GET `/api/entities` | role?, cluster_id?, is_seed?, offset=0, limit=20 | EntityListResponse; нужен для фильтров всей сети, а не фильтрации только top-20 |
| GET `/api/entities/{gid}` | Точный gid | EntityResponse; поиск работает по всем узлам |
| GET `/api/subgraph` | gid, hops=1, limit=80 | SubgraphResponse |
| GET `/api/clusters` | Нет | ClustersResponse, включая singleton clusters |
| GET `/api/export/{filename}` | Одно из трёх имён из ТЗ | UTF-8 CSV, Content-Disposition attachment |
| POST `/api/investigate` | InvestigationRequest | InvestigationResponse |

Ограничения: list limit 1..200, offset≥0; subgraph hops 1..2, limit 1..200; selected_gids 0..20 уникальных gid; question 1..2000 символов после trim. Для common recipients max_hops 1..4, limit 1..50, gids 1..20 уникальных известных gid. Tool и HTTP validators применяют одинаковые пределы. Bool query — `true`/`false`. Неподдержанный enum или неверный диапазон — 422.

Entity list сортируется по priority DESC, gid ASC как исходному целому (в Python); total — количество после фильтров до pagination. Rank CSV глобальный, UI не выдаёт номер строки отфильтрованной страницы за глобальный rank.

## Семантика subgraph

Для UI окружение обходится по входящим И исходящим соседям на hops шагов; показанные рёбра всегда сохраняют исходное направление. Это отличается от directed downstream reach инструмента common recipients.

1. Найти всех кандидатов окружения; center входит всегда.
2. При превышении limit оставить center, затем ближайшие по hops узлы; внутри уровня — priority DESC, gid ASC.
3. Показать все исходные направленные рёбра между оставленными узлами.
4. total_nodes/total_edges относятся к полному окружению до ограничения. omitted_count=total_nodes−len(nodes), omitted_edges=total_edges−len(edges).
5. truncated=true, если скрыты узлы или рёбра. Все концы показанных edges присутствуют в nodes. Изолят возвращает один узел, пустые edges и truncated=false.

Граф не является набором всех путей передачи тех же денег. Метрики карточки относятся ко всей наблюдаемой сети, не только выбранному ego-графу.

## Ошибки и отсутствие AI

| Ситуация | HTTP | Body |
|---|---|---|
| Невалидный запрос | 422 | ErrorResponse / INVALID_REQUEST |
| Неизвестный gid (включая selected_gids) | 404 | ErrorResponse / ENTITY_NOT_FOUND |
| Нет рассчитанного snapshot | 503 | ErrorResponse / SNAPSHOT_NOT_READY |
| В investigate передан старый snapshot_id | 409 | ErrorResponse / SNAPSHOT_MISMATCH |
| Необработанная ошибка сервера | 500 | ErrorResponse / INTERNAL_ERROR без traceback/секретов |
| AI выключен/нет ключа | 200 | InvestigationResponse, status=unavailable, findings/evidence/tool_calls=[] |
| AI timeout | 200 | InvestigationResponse, status=timeout; findings/evidence=[]; завершённые реальные calls можно сохранить |
| AI error / ответ не прошёл проверку | 200 | InvestigationResponse, status=failed; findings/evidence=[] |

HTTP 200 для unavailable/timeout/failed — осознанная договорённость об обработанном результате AI-операции. Frontend обязан проверять status. Это не означает успешное расследование. Приложение продолжает обслуживать core routes.

## Python boundary для одного Investigator

HTTP orchestration принадлежит backend. `agent/` предоставляет callable `investigate(request, tools) -> InvestigationResponse`; sync/async реализацию один раз согласовывают Нурасыл и Даулет. Предпочтение — async, без блокировки FastAPI event loop. Не запускать HTTP-вызовы собственного backend из tool, если доступна та же Python service-функция.

| Tool | Inputs | Result |
|---|---|---|
| get_entity_profile | gid:string | EntityResponse |
| get_subgraph | gid:string, hops:int=1, limit:int=80 | SubgraphResponse |
| rank_entities | role?:Role, cluster_id?:int, limit:int=20 | EntityListResponse, offset=0; is_seed не фильтровать без явного запроса |
| find_common_recipients | CommonRecipientsRequest | CommonRecipientsResponse |

Common recipients: пересечение узлов, достижимых **из каждого** выбранного gid по направленным путям длиной 1..max_hops. Исключить сами выбранные gid из кандидатов. max_hops=1 означает direct, больше — reachable. По каждому кандидату вернуть по одному кратчайшему пути-свидетельству от каждого selected_gid; при равных путях детерминированно выбирать порядок соседей по gid. Сортировка кандидатов — priority DESC, gid ASC; total до limit. Пустое пересечение — успешный ответ с items=[], не ошибка. Наличие пути не доказывает происхождение или хронологию средств; limitations обязательно включает `path_not_money_provenance`.

Ограничение 6 tool calls на вопрос. Общий стартовый timeout AI — 30 секунд, затем уточнить после измерения; бесконечные retries запрещены. Конфигурация лимитов единая.

## AI findings и evidence

Каждый finding имеет gids и evidence_ids. Все gids известны snapshot; все evidence_ids разрешаются в массив evidence ТОГО ЖЕ ответа. Ответ API переносит факты из snapshot/tools, модель только ссылается на них. Ссылки валидируются до показа. Ограничения фактов объединяются с limitations finding/result и не могут исчезнуть при генерации.

Tool calls — реальные name/status/duration_ms/evidence_ids, без скрытых рассуждений. Если модель вернула неподтверждённые числа/обвинение, не выдавать structured parsing за семантическую проверку: убрать непроверенный finding либо вернуть failed с понятным сообщением. Для MVP предпочтительны короткие findings и отображение чисел непосредственно из facts.

## Коды limitations v1

| Код | Подпись |
|---|---|
| inflow_incomplete | Входящие за пределами наблюдаемой сети неизвестны |
| depth_truncated | Исходящие ограничены глубиной обхода |
| seed_inflow_incomplete | Выборка собрана от seed; вход особенно неполон |
| outflow_exceeds_observed_inflow | Выход превышает наблюдаемый вход; полный баланс неизвестен |
| isolated_seed | У исходного участника нет наблюдаемых связей |
| insufficient_evidence | Недостаточно признаков для уверенной роли |
| date_only | Внутридневной порядок операций неизвестен |
| period_censored | Операции за пределами июля неизвестны |
| threshold_5000 | Переводы менее 5000 KZT не наблюдаются |
| intrabank_only | Наблюдаются только внутрибанковские переводы |
| path_not_money_provenance | Структурный путь не доказывает движение тех же средств |
| subgraph_truncated | Показана часть окружения |

## Проверка совместимости

Frontend импортирует типы и использует fixtures. Backend создаёт эквивалентные Pydantic-схемы, сериализует фактические ответы и проверяет соответствие contract. Fixtures не заменяют runtime-тест: после реализации обязательно проверить live entity, isolate, boundary, truncated subgraph, list pagination, CSV и AI outage.

Изменения обязательных полей требуют одновременного обновления типов, fixtures, backend, frontend и tools. Никаких отдельных «почти совместимых» форматов по веткам. Additive необязательное поле допустимо только после явного документирования его default.
