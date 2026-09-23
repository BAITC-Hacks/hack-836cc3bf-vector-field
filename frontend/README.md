# HackAlem frontend

Один React/Vite/TypeScript экран для сценария `вопрос Investigator → проверяемые факты → узел/граф`, сохраняя очередь, поиск и dossier.

## Фактически проверенные команды

Из этой директории:

```powershell
npm.cmd ci
npm.cmd run dev
npm.cmd run build
npm.cmd run preview
```

`npm.cmd` используется в Windows, если PowerShell execution policy блокирует `npm.ps1`.

## Текущий режим

По умолчанию приложение использует `HttpDataProvider` и реальный локальный snapshot API. Для учебного режима установить `VITE_DATA_PROVIDER=fixture` перед сборкой или запуском Vite. В этом режиме шесть синтетических fixture-узлов явно помечены «Учебные данные» и не выдаются за исходную сеть.

В live-режиме вопрос Investigator можно отправить по всей наблюдаемой сети или с выбранным gid как контекстом. Форма вызывает `POST /api/investigate` по transport v1 и показывает loading, completed, empty, unavailable, timeout и failed отдельно. В завершённом ответе отображаются findings, числовые evidence facts, ограничения, следующие проверки и фактически выполненные tool calls; gid открывает существующую карточку и граф. В шапке доступны три CSV через `/api/export/{filename}`. UI не создаёт AI-ответов в fixture mode.

Узлы для demo на исходном live snapshot:

- карточка и Investigator: `100000003115284100`;
- изолят: `100000000456947100`;
- boundary `depth=4`: `100000000018102100`;
- unknown gid: `999999999999999999`, ожидается `ENTITY_NOT_FOUND`.

Следующие примеры относятся **только к синтетическому fixture mode**, а не к исходному dataset:

- обычная карточка `900000000000000001`;
- изолят `900000000000000006`;
- boundary `depth=4`, `900000000000000005`;
- урезанное окружение кнопкой `limit 2 — урезанное` с `omitted_count`;
- unknown gid `999999999999999999` с честным `ENTITY_NOT_FOUND`;
- точный поиск по gid без numeric conversion.

Граф использует Cytoscape. Исходные `gid`, `src`, `dst` остаются строками; Cytoscape получает их без `Number`, `parseInt` или unary `+`. React не пересчитывает роли, scores, потоки или priority evidence. Если fixture не содержит `priority_v0` facts, UI сообщает об отсутствии данных.

## Архитектура provider

Компоненты зависят от `DataProvider` в `src/data/provider.ts`; live и fixture реализации используют одни имена полей.

Для разработки с live backend:

```powershell
$env:VITE_API_BASE=""
npm.cmd run dev
```

Vite проксирует `/api` на `http://127.0.0.1:8000`. Нужны routes из contract v1:

- `GET /api/summary`
- `GET /api/entities?role=&cluster_id=&is_seed=&offset=&limit=`
- `GET /api/entities/{gid}`
- `GET /api/subgraph?gid=&hops=&limit=`
- `GET /api/clusters`

В собранном режиме FastAPI раздаёт `frontend/dist` вместе с `/api`; `GET /api/summary` и остальные routes используют `pipeline/out/snapshot.json`. Панель Investigator получает ответ `/api/investigate`; без `OPENAI_API_KEY` она отображает `unavailable`, не скрывая core.

## Проверка Stage 2

В интеграционном checkout сборка прошла на Node.js 24.21.0. В браузере с реальным OpenAI provider проверены два сценария: ranking за 9464 мс (`rank_entities` и три `get_entity_profile`, три findings и девять facts) и профиль `100000003115284100` (`get_entity_profile`, два findings и десять facts). Точные facts сверены со snapshot, смысл findings просмотрен отдельно. Канонический adapter — `agent/openai_model.py`, модель по умолчанию `gpt-5.6-luna`.

Полные результаты, ограничения и статус интеграции: [Stage 2 closure](../integration/STAGE2_CLOSURE.md). Эти проверки относятся к интеграционному checkout и сами по себе не означают завершение merge в `main`.

## Ограничения

- Без предварительного запуска pipeline live API вернёт `SNAPSHOT_NOT_READY`.
- Адаптер OpenAI Responses работает при наличии `OPENAI_API_KEY`; отсутствие ключа и ошибки отображаются честным статусом. Live browser smoke покрывает ranking и профиль, а не любой возможный вопрос.
- Исторический запуск до Stage 2 на Node 22.11 сопровождался предупреждением Vite и ручной установкой optional Windows binding Rolldown. Это не результат текущей успешной сборки на Node 24.21.0 и не обязательный шаг обычной установки.
