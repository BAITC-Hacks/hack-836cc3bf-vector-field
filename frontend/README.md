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

По умолчанию приложение использует `HttpDataProvider` и реальный локальный snapshot API. Для учебного режима установить `VITE_DATA_PROVIDER=fixture` перед сборкой или запуском Vite. В этом режиме шесть синтетических fixture-узлов явно помечены «Учебные данные» и не выдаются за исходную сеть.

Проверяемые сценарии:

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

## Ограничения

- Без предварительного запуска pipeline live API вернёт `SNAPSHOT_NOT_READY`.
- Адаптер OpenAI Responses подключён к backend при наличии `OPENAI_API_KEY`; реальный HTTP smoke с credential ещё не проведён. Статус ответа Investigator отображается без подмены.
- На Windows в этой сессии сборка прошла на Node 22.11 с предупреждением Vite о требовании 22.12+; `npm ci` пропустил optional Windows binding Rolldown, поэтому его пришлось доустановить в локальный `node_modules` командой `npm.cmd install --no-save --no-package-lock @rolldown/binding-win32-x64-msvc@1.2.9`. Эта команда не меняет lockfile.
