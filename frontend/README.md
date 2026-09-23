# HackAlem frontend

Один React/Vite/TypeScript экран для сценария `очередь → выбранный узел → направленный ego-граф → dossier`.

## Фактически проверенные команды

Из этой директории:

```powershell
npm.cmd install
npm.cmd run dev
npm.cmd run build
npm.cmd run preview
```

`npm.cmd` используется в Windows, если PowerShell execution policy блокирует `npm.ps1`.

## Текущий режим

По умолчанию приложение использует `FixtureDataProvider` и `shared/fixtures.json` — общий синтетический transport fixture v1. В интерфейсе явно отображается **«Учебные данные»**. Шесть fixture-узлов не расширяются выдуманным top-20 и не выдаются за исходную сеть из Parquet.

Проверяемые сценарии:

- обычная карточка `900000000000000001`;
- изолят `900000000000000006`;
- boundary `depth=4`, `900000000000000005`;
- урезанное окружение кнопкой `limit 2 — урезанное` с `omitted_count`;
- unknown gid `999999999999999999` с честным `ENTITY_NOT_FOUND`;
- точный поиск по gid без numeric conversion.

Граф использует Cytoscape. Исходные `gid`, `src`, `dst` остаются строками; Cytoscape получает их без `Number`, `parseInt` или unary `+`. React не пересчитывает роли, scores, потоки или priority evidence. Если fixture не содержит `priority_v0` facts, UI сообщает об отсутствии данных.

## Архитектура provider

Компоненты зависят от `DataProvider` в `src/data/provider.ts`. Сейчас подключён `FixtureDataProvider`; готов `HttpDataProvider` с теми же методами и именами полей.

Для запуска через будущий backend:

```powershell
$env:VITE_DATA_PROVIDER="http"
$env:VITE_API_BASE=""
npm.cmd run dev
```

Vite проксирует `/api` на `http://127.0.0.1:8000`. Нужны routes из contract v1:

- `GET /api/summary`
- `GET /api/entities?role=&cluster_id=&is_seed=&offset=&limit=`
- `GET /api/entities/{gid}`
- `GET /api/subgraph?gid=&hops=&limit=`
- `GET /api/clusters`

Следующий этап — заменить fixture snapshot на live snapshot/API. Компоненты и transport-типы менять не требуется.

## Ограничения

- Пока это fixture-stage, не production analysis и не результат расчёта по исходным Parquet.
- Фактический backend, pipeline, CSV и Investigator находятся вне frontend scope.
- Визуальная проверка браузером должна выполняться после `npm.cmd run dev`; build/typecheck — автоматическая проверка проекта.
