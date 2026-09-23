# Общий контракт v1

- `contracts.ts` — transport types для frontend, backend и tools; декларации, не runtime implementation.
- `fixtures.json` — 17 синтетических сценариев для UI и интеграционного контракта, включая normal/isolate/boundary, truncated subgraph, AI failure и empty common recipients. Это не результаты исходного датасета, не scoring tests и не реальные AI calls.
- `../docs/API_CONTRACT.md` — endpoints, defaults, limits, errors, tool semantics и ownership.

Frontend использует fixture с явной отметкой «учебные данные». Backend строит соответствующие Pydantic-модели и реальные handlers. Один Investigator использует те же service-функции и snapshot. До готовности HTTP можно независимо работать над UI/tools boundary.

Нельзя объявлять API готовым только потому, что эти файлы существуют. Нужен реальный end-to-end run после реализации.
