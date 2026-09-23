# HackAlem 2026 — Full Team Execution Plan

**Дата:** 23 сентября 2026  
**Трек:** FinTech  
**Основное окно:** 13:00–18:00  
**Команда:** Нурасыл · Даулет · Аки  
**Цель:** построить наиболее убедительное решение официального кейса, которое реально работает end-to-end и выдерживает demo.

---

# 1. Executive summary

У команды фактически не 5 часов на «разработку продукта».

У вас:

- 30 минут на понимание правильного продукта;
- 3 часа на создание и усиление работающего решения;
- 1,5 часа на то, чтобы оно не развалилось при показе.

Поэтому весь день строится вокруг четырёх жёстких gates:

### 13:30 — Solution Lock

Команда точно знает:

- что требует challenge;
- что оценивает rubric;
- какой один user flow показываем;
- какая минимальная архитектура нужна;
- какие agents/tools действительно нужны;
- что real, а что simulated;
- какой контракт между frontend/backend/agent;
- что считается Core Done.

### 14:30 — True Vertical Slice

Обязан впервые работать путь:

```text
UI
→ backend
→ real AI/agent
→ tool/data
→ structured result
→ UI
```

Tool может обращаться к подготовленным/симулированным данным, если реальная внешняя интеграция не обязательна. Но AI-вызов должен быть настоящим.

### 16:30 — Hard Feature Freeze

С этого момента запрещены:

- новые agents;
- новые integrations;
- новый database stack;
- крупные архитектурные изменения;
- существенные новые screens;
- «давайте ещё вот это добавим».

Остаются:

- P0/P1 bugs;
- reliability;
- demo UX;
- fallback;
- README;
- presentation assets;
- rehearsal;
- submission.

### 17:30 — Code Lock

После 17:30 меняется код только при критическом дефекте, который делает demo невозможным.

Если такой дефект появляется — предпочтительнее revert на последний рабочий commit, чем двадцатиминутный рефакторинг.

---

# 2. Fixed decisions / defaults / open decisions

## 2.1. Уже решено

Зафиксировано до получения официального challenge:

| Область | Решение |
|---|---|
| Команда | 3 человека |
| Трек | FinTech |
| Team lead | Нурасыл |
| AI/agents | Нурасыл |
| Backend/integrations | Даулет |
| Frontend/UI | Аки |
| Final decision-maker | Нурасыл |
| Git | один официальный GitHub repository |
| Coding AI | Codex обязателен, Claude Code/ChatGPT дополнительно |
| Рабочий ритм | 25 минут work/review + 5 минут sync |
| Scope philosophy | working demo > архитектурная сложность |
| Multi-agent | только если функционально оправдан |
| FinTech high-impact action | HumanGate |
| Explainability | evidence/operational trace, не скрытый chain-of-thought |
| Старый Oqera code | не переносится |
| Oqera knowledge/patterns | можно использовать как опыт |
| Demo engineering | seed/mock/fallback допустимы при честном обозначении |

---

# 2.2. Предварительные defaults

Это хорошие стартовые варианты, но они должны пережить проверку официальным case.

### Frontend

```text
React
Vite
Tailwind
```

Оставляем, если официальный repository/template не диктует другое.

### Backend

```text
Python
FastAPI
Pydantic
```

Это сильный default и менять его без причины не стоит.

### Agent harness

```text
OpenAI Agents SDK
```

Хороший default для bounded tool-using agent flow.

Но не надо насильно использовать Agents SDK, если challenge фактически требует простой deterministic pipeline.

### State

Исходный default команды — SQLite.

Я бы изменил его на:

```text
No DB / JSON / in-memory
        ↓ если нужна persistence
SQLite
```

Для пятичасового hackathon **отсутствие БД лучше SQLite**, если данные нужны только для одного demo run.

SQLite нужен, когда состояние действительно является частью demo:

- approval;
- audit trail;
- несколько run;
- сохранённые cases;
- history.

---

# 2.3. Нельзя решить заранее

До официального challenge нельзя фиксировать:

- конкретный FinTech product;
- fraud/AML/KYC/payments/lending/etc.;
- точное число agents;
- нужен ли вообще multi-agent;
- agent roles;
- tools;
- external APIs;
- RAG;
- embeddings;
- vector DB;
- PostgreSQL;
- Redis;
- deployment;
- UI information architecture;
- exact HumanGate;
- exact data model;
- evaluation metrics;
- presentation structure.

---

# 3. Operating principles

## Principle 1 — Rubric beats taste

Если технология выглядит впечатляюще, но не улучшает выполнение challenge или demo, она не нужна.

## Principle 2 — Build one story

Продукт должен объясняться одной строкой:

```text
Пользователь делает X
→ система выполняет Y
→ показывает Z
→ при high-impact действии просит approval.
```

Если для объяснения нужно пять сценариев — scope слишком широкий.

## Principle 3 — Vertical before horizontal

Сначала одна полностью рабочая цепочка.

Только потом:

- второй specialist;
- verifier;
- второй tool;
- дополнительные screens;
- animations.

## Principle 4 — Contracts before parallel coding

Аки, Даулет и Нурасыл не должны самостоятельно придумывать названия одинаковых сущностей.

## Principle 5 — Mock the boundary, not the intelligence

Можно симулировать:

- банковский rail;
- corporate API;
- third-party data source.

Нельзя симулировать и выдавать за настоящее:

- AI reasoning;
- agent decision;
- tool invocation, если заявляется, что он реально выполняется.

## Principle 6 — Main must remain demoable

`main` — рабочая интеграционная ветка, а не свалка трёх незавершённых экспериментов.

## Principle 7 — Every 30 minutes produces something visible

После каждого цикла должен существовать:

- работающий capability;
- commit;
- validated contract;
- или устранённый blocker.

## Principle 8 — New feature must earn its time

После 15:00 новая feature должна отвечать на вопрос:

> Как именно она повышает шанс хорошо показать официальный rubric?

Если ответа нет — CUT.

---

# 4. Первые 30 минут: 13:00–13:30

Это важнейшие 30 минут всего хакатона.

Не начинать coding race до определения правильной задачи.

---

## 13:00–13:04 — Silent challenge intake

Все трое самостоятельно читают:

- case;
- rubric;
- mandatory requirements;
- submission instructions;
- ограничения;
- доступные resources.

Никто не начинает сразу продавать свою идею другим.

### Нурасыл

Ищет:

- target user;
- бизнес-проблему;
- expected outcome;
- где реально нужен AI;
- FinTech смысл.

### Даулет

Ищет:

- mandatory technical requirements;
- required data;
- integrations;
- API constraints;
- submission requirements;
- запрещённые подходы.

### Аки

Ищет:

- evaluation criteria;
- что жюри должно увидеть;
- какие результаты необходимо визуально доказать;
- какой user journey implied case'ом.

### AI

Каждый может дать case своему assistant, но с разными задачами.

Не спрашивать:

> «Придумай нам лучший проект».

Спрашивать:

> «Извлеки только требования, rubric, constraints и ambiguities. Ничего не додумывай».

---

# 13:04–13:08 — Independent extraction

Создаётся общий черновик.

### Нурасыл

Заполняет:

```text
Problem
Target user
Expected outcome
AI necessity
```

### Даулет

Заполняет:

```text
Mandatory requirements
Technical constraints
Submission requirements
Available resources
```

### Аки

Заполняет:

```text
Evaluation criteria
Expected visible result
Demo requirements
```

---

# 13:08–13:12 — Interpretation merge

Команда сверяет три прочтения.

Создаются четыре категории:

```text
MUST
SHOULD
UNKNOWN
NON-GOAL
```

Любой спор > 60 секунд закрывает Нурасыл.

Если формулировка организаторов реально неоднозначна и рядом есть mentor/organizer — спрашиваете.

Не стройте архитектуру вокруг догадки, которую можно проверить за две минуты.

---

# 13:12–13:17 — Product concept lock

Допускается максимум 2–3 варианта решения.

Они проверяются не по «вау», а по четырём вопросам:

1. Закрывает ли mandatory requirements?
2. Позволяет ли показать ценность за короткое demo?
3. Есть ли оправданная agentic работа?
4. Реально ли построить core примерно за час?

Нурасыл выбирает один вариант.

### К 13:17 должно существовать:

```text
DEMO STORY:

Пользователь делает X
→ система делает Y
→ использует Z
→ возвращает R.
```

И одна фраза:

```text
WHY AI / WHY AGENT
```

---

# 13:17–13:21 — Minimal architecture lock

Определяются:

### Frontend

Только screens/states, необходимые для demo.

### Backend

Минимальные endpoint(s).

### Agent architecture

Начинать максимум с:

```text
1 orchestrator / primary agent
```

Второго specialist пока только записать как `OPTIONAL`.

### Tools

Для каждого tool:

```text
purpose
input
output
real / simulated
```

### External integration decision

Real integration берём только если:

- обязательна case;
- заметно улучшает rubric;
- или подключается примерно за 10–15 минут.

Иначе создаётся реалистичный adapter/mock.

---

# 13:21–13:25 — Contract + HumanGate + DoD

Нурасыл принимает **семантику canonical contract**.

Даулет отвечает за его техническую реализацию.

Минимально фиксируются:

```text
request
status
summary/result
evidence
tool activity
recommended action
requires_approval
error
```

Конкретные поля зависят от case.

### HumanGate

Именно здесь определяется risk policy.

Для каждого действия спрашивается:

```text
Что произойдёт, если агент ошибётся?
```

Если последствия существенные/финансовые/регуляторные/трудно обратимые:

```text
agent prepares/recommends
→ HumanGate
→ execution
```

Если действие безопасное и обратимое:

```text
agent may execute
```

Если challenge вообще не имеет high-impact action — HumanGate не добавляем декоративно.

---

# 13:25–13:28 — Parallelization lock

Каждому назначается первый 25-минутный deliverable.

### Нурасыл

Primary agent + structured output.

### Даулет

Backend skeleton + endpoint + schemas.

### Аки

UI skeleton против canonical mock fixture.

Создаются branches.

---

# 13:28–13:30 — Readback + first commit

Нурасыл вслух читает:

- challenge;
- demo story;
- core architecture;
- contract;
- Core Done;
- кто что делает следующие 25 минут.

Каждый подтверждает не идею, а **понимание своего deliverable**.

Далее первый commit:

```text
docs: lock challenge scope and build contract
```

---

# 4.1. Source of truth к 13:30

В repository должен появиться:

```text
docs/BUILD_BRIEF.md
```

Он содержит:

```md
# Challenge
...

# Mandatory Requirements
...

# Evaluation Criteria
...

# Submission Requirements
...

# Target User
...

# Problem
...

# Demo Story
...

# Why AI / Agent
...

# Architecture
...

# Agents
...

# Tools
...

# Real vs Simulated Integrations
...

# HumanGate Policy
...

# API Contract
...

# Demo Fixture
...

# Core Definition of Done
...

# Stretch
...

# Cut First
...

# Current Owners
...
```

Дополнительно:

```text
shared/
    example-request.json
    example-response.json
```

или аналогичные fixtures.

Это позволяет Аки не ждать backend.

---

# 5. Stage architecture

## STAGE-00 — Challenge Intake

**Время:** 13:00–13:08  
**Purpose:** понять буквальное содержание case.  
**Owner:** Нурасыл.  
**Inputs:** официальный case/rubric.  
**Outputs:** extracted requirements.  
**Review:** сравнение трёх независимых интерпретаций.  
**Exit:** нет неизвестных mandatory требований.

---

## STAGE-01 — Solution Lock

**Время:** 13:08–13:30  
**Purpose:** заморозить продуктовый scope и contract.  
**Owner:** Нурасыл.  
**Output:** `BUILD_BRIEF.md`.  
**Exit:** каждый способен одной фразой объяснить demo и назвать свой первый deliverable.

---

## STAGE-02 — Skeleton & Wire Slice

**Время:** 13:30–14:00  
**Purpose:** три слоя уже существуют и могут соединяться.  
**Exit:** UI вызывает backend; backend способен вызвать real AI или AI отдельно доказан; UI умеет показать agreed response.

---

## STAGE-03 — True Vertical Slice

**Время:** 14:00–14:30  
**Purpose:** первый настоящий end-to-end flow.  
**Exit:**

```text
UI
→ backend
→ AI
→ meaningful tool/data
→ structured response
→ UI
```

---

## STAGE-04 — Core Stabilization

**Время:** 14:30–15:00  
**Purpose:** сделать flow повторяемым, а не случайно работающим.  
**Exit:** основной demo flow проходит минимум 3 последовательных раза.

---

## STAGE-05 — Agent Depth

**Время:** 15:00–15:30  
**Purpose:** добавить только agentic depth, которая помогает challenge.  
**Exit:** specialist/verifier/tool depth добавлены или сознательно отклонены.

---

## STAGE-06 — Evidence / HumanGate / UX

**Время:** 15:30–16:00  
**Purpose:** сделать reasoning продукта понятным пользователю и жюри.  
**Exit:** evidence, activity trace и approval states работают там, где это необходимо.

---

## STAGE-07 — Rubric Closure

**Время:** 16:00–16:30  
**Purpose:** закрыть оставшиеся scoring gaps и подготовить demo surface.  
**Exit:** нет незакрытых критичных rubric требований.

---

## STAGE-08 — Feature Freeze & Reliability

**Время:** 16:30–17:00  
**Purpose:** перестать строить и начать защищать результат.  
**Exit:** demo-ready build + fallback + второй компьютер способен запустить core.

---

## STAGE-09 — Demo Ready

**Время:** 17:00–17:30  
**Purpose:** rehearsal, UX fixes, presentation assets.  
**Exit:** минимум две успешные репетиции.

---

## STAGE-10 — Submission Lock

**Время:** 17:30–18:00  
**Purpose:** гарантированно сдать рабочий продукт.  
**Exit:** repository/submission проверены и отправлены.

---

# 6. Полный execution plan: 13:30–18:00

# CYCLE 1 — 13:30–14:00

## Цель

Получить **wire slice**, а не три независимых проекта.

## Нурасыл

- создаёт simplest viable primary agent;
- определяет prompt/instructions;
- получает structured output;
- если нужен tool — создаёт минимальный tool interface;
- не строит specialist/verifier.

## Даулет

- FastAPI skeleton;
- один основной endpoint;
- Pydantic request/response;
- CORS если нужен;
- `.env` loading;
- подключает agent entrypoint или временный adapter.

## Аки

- React/Vite shell;
- один основной screen;
- input;
- submit;
- loading;
- render canonical fixture;
- error container.

Никаких сложных routing/navigation/design systems.

## Coding agents

Могут:

- bootstrap project;
- генерировать boilerplate;
- создавать Pydantic models;
- создавать React components;
- писать basic tests;
- проверить imports/startup.

## Люди проверяют

- совпадение полей;
- отсутствие лишних abstractions;
- реально ли запускается;
- не заменил ли AI выбранный stack самостоятельно.

## Integration checkpoint

К 13:53:

```text
Frontend → backend request
Backend → response
Frontend → rendered response
```

Agent также должен быть отдельно callable.

Идеально — уже через backend.

## Deliverable

Первый runnable skeleton.

## Commit

```text
feat: add runnable frontend backend and agent skeleton
```

## Go

Можно идти дальше, если:

- frontend запускается;
- backend запускается;
- endpoint вызывается;
- primary agent делает реальный model call.

## No-Go

Если нет:

- никаких specialists;
- никаких databases;
- никакого polish.

Все трое доводят wire slice.

---

# CYCLE 2 — 14:00–14:30

## Цель

Получить **настоящий vertical slice**.

Это первый критический deadline.

## Нурасыл

- primary agent вызывает meaningful tool;
- structured output соответствует contract;
- tool result превращается в evidence/result;
- prompt минимально стабилизирован.

## Даулет

Соединяет:

```text
endpoint
→ agent
→ tool/data
→ response
```

Добавляет минимальную обработку timeout/error.

## Аки

Переключается:

```text
mock response
→ real backend
```

Рендерит:

- result;
- evidence;
- status;
- error.

## Coding agents

Проверяют:

- schema mismatch;
- request/response mismatch;
- missing optional fields;
- serialization;
- imports;
- runtime exceptions.

## Люди проверяют

Один настоящий сценарий руками.

Не unit test.

Полный клик от UI до результата.

## Integration checkpoint

Необходимо увидеть:

```text
USER ACTION
↓
API
↓
REAL MODEL
↓
TOOL/DATA
↓
STRUCTURED RESULT
↓
SCREEN
```

## Deliverable

Первый end-to-end demo.

Внешний FinTech API может пока быть simulated tool adapter.

## Commit

```text
feat: complete first end to end agent flow
```

## Go

Только если vertical slice прошёл.

## No-Go

Если не прошёл:

- database остаётся out;
- second agent out;
- external API out;
- animations out.

Следующий cycle остаётся integration cycle.

---

# CYCLE 3 — 14:30–15:00

## Цель

Превратить случайно работающий flow в **Core Done candidate**.

## Нурасыл

- проверяет output quality;
- убирает prompt ambiguity;
- проверяет challenge/rubric;
- решает, действительно ли нужен второй specialist.

## Даулет

- стабилизирует endpoint;
- нормализует errors;
- tool adapters;
- state только если реально требуется;
- добавляет простой health/startup check.

## Аки

Добавляет:

- empty state;
- retry;
- correct evidence rendering;
- result hierarchy;
- базовую понятную FinTech UX.

## AI review

Особенно ищет:

- schema drift;
- null/undefined;
- wrong endpoint;
- hidden hardcoding;
- fake status;
- backend duplication.

## Human check

Основной flow запускается три раза подряд.

## Deliverable

Core, который можно показывать без извинений.

## Commit

```text
fix: stabilize core demo flow and contracts
```

## Go

Три последовательных успешных demo runs.

## No-Go

Если нестабилен — остаёмся на одном agent и одном tool.

---

# CYCLE 4 — 15:00–15:30

## Цель

Добавить **agent depth**, только если Core Green.

## Нурасыл

Теперь впервые может добавить:

- specialist #2;
- verifier;
- дополнительный tool;

но максимум **одну архитектурную единицу за цикл**.

Не всё сразу.

Приоритет:

1. второй meaningful tool;
2. specialist, если роли реально различаются;
3. verifier, если verification существенно для case.

## Даулет

- подключает новый component без изменения existing contract;
- сохраняет backward compatibility;
- если specialist создаёт новый state — нормализует его.

## Аки

Не обязана отображать внутреннюю архитектуру целиком.

Добавляет только полезные states:

- activity;
- evidence;
- status progression.

## Integration checkpoint

Новая depth feature не должна ломать существующий vertical slice.

## Deliverable

Усиленный, но всё ещё стабильный core.

## Commit

```text
feat: add challenge relevant agent depth
```

## Go

Новая feature работает и улучшает case.

## No-Go

Если она создаёт instability:

```text
git revert
```

Не «починим потом».

---

# CYCLE 5 — 15:30–16:00

## Цель

Сделать систему понятной и доверяемой.

## Нурасыл

- определяет финальные evidence fields;
- risk policy;
- HumanGate semantics;
- operational trace;
- проверяет, что система не показывает fake chain-of-thought.

## Даулет

Если нужен approval:

```text
status = approval_required
```

и минимальный mechanism:

```text
approve / reject
```

или эквивалентный flow.

Не строить полноценную workflow engine.

## Аки

Добавляет:

- evidence cards;
- activity timeline;
- HumanGate card;
- approve/reject;
- polished result hierarchy.

## Presentation

Аки уже может **пассивно сохранять screenshots** работающего продукта.

Но она ещё не должна уходить на 25 минут в deck.

## Deliverable

Demo становится объяснимым.

## Commit

```text
feat: add evidence trace and approval experience
```

## Go

Core стабилен.

## No-Go

HumanGate/visualization режется до минимальной версии.

---

# CYCLE 6 — 16:00–16:30

## Цель

Последний feature cycle.

Не «ещё что-нибудь красивое», а **закрытие rubric gaps**.

## Нурасыл

Создаёт checklist:

```text
Rubric item → доказательство в продукте/demo
```

Ищет незакрытые обязательные пункты.

Пишет первую версию demo narrative.

## Даулет

Закрывает:

- critical integration gaps;
- timeout;
- fallback adapter;
- replay mechanism;
- persistence только если необходима.

## Аки

- UX polish основной цепочки;
- agent/activity visualization;
- screenshots;
- начинает presentation assets;
- не строит дополнительные страницы.

## Deliverable

Наиболее полный scoring build.

## Commit

```text
feat: close rubric gaps and prepare demo build
```

## Gate

В **16:30 HARD FEATURE FREEZE**.

---

# CYCLE 7 — 16:30–17:00

# FEATURE FREEZE

## Цель

Reliability.

## Запрещено

- новый agent;
- новый external API;
- новая database;
- новая architecture;
- новый framework;
- новый крупный screen.

## Нурасыл

- тестирует edge cases;
- проверяет output quality;
- фиксирует только P0/P1 agent failures;
- завершает demo script.

## Даулет

Главный owner цикла.

Проверяет:

- startup;
- env;
- timeout;
- failed external calls;
- malformed response;
- fallback;
- secondary laptop startup;
- logs.

## Аки

- loading/error/fallback states;
- visual bugs;
- final screenshots;
- architecture diagram из **замороженной** архитектуры.

## Integration checkpoint

Полный запуск с нуля.

Не из уже работающего dev server.

## Deliverable

Demo-ready build.

## Commit

```text
fix: harden demo runtime and fallback paths
```

## Go

Полный demo проходит.

## No-Go

Stretch выключается полностью.

---

# CYCLE 8 — 17:00–17:30

## Цель

Rehearsal.

## Нурасыл

- говорит demo narrative вслух;
- сокращает лишнее;
- проверяет связь demo с rubric.

## Даулет

- остаётся demo ops;
- следит за runtime/logs;
- устраняет только reproducible bugs;
- проверяет clean setup.

## Аки

- presentation assets;
- problem/solution visuals;
- screenshots;
- architecture diagram;
- резервная screenshot sequence.

## Первый rehearsal

Около 17:05–17:10.

После него максимум:

- 3 fixes.

## Второй rehearsal

Около 17:20.

Уже на intended demo machine.

## Deliverable

Команда знает точный порядок показа.

## Commit

```text
fix: finalize demo experience
```

## Gate

17:30 — CODE LOCK.

---

# CYCLE 9 — 17:30–18:00

## Цель

Не улучшить продукт.

# Сдать продукт.

## Нурасыл

Проверяет:

- challenge coverage;
- submission form;
- название;
- short description;
- demo narrative;
- никакой обязательный пункт не забыт.

## Даулет

Проверяет:

- repo clean;
- main latest;
- requirements/install;
- `.env.example`;
- README;
- no secrets;
- startup commands;
- dependencies locked.

## Аки

Проверяет:

- screenshots/assets;
- presentation files, если требуются;
- product visual integrity;
- fallback screenshots/video, если предусмотрены.

## Последний demo

Около 17:35–17:40.

После него код не трогаем без P0.

## Final commit

```text
docs: finalize setup demo and submission instructions
```

или при bug fix:

```text
fix: resolve final demo blocker
```

## Последние 10–15 минут

Идеально уже ничего не разрабатывать.

Только:

- submission;
- upload;
- verify;
- check GitHub;
- check links.

---

# 7. Responsibility model

# Нурасыл

## Обязан лично

- понять challenge;
- определить WHAT;
- определить WHY;
- выбрать scope;
- определить demo story;
- определить canonical semantics;
- выбрать agent architecture;
- определить HumanGate policy;
- следить за rubric;
- принимать CUT decisions;
- принимать architectural decisions;
- управлять временем;
- готовить demo narrative.

## Не должен

- чинить CSS;
- настраивать Vite;
- дебажить Windows paths;
- писать каждый backend endpoint;
- вручную разрешать каждый merge conflict;
- перестраивать чужой код «как красивее»;
- уходить на 40 минут в prompt tuning.

### Правило

Нурасыл вмешивается в чужой поток только при:

```text
RED integration gate
contract decision
scope decision
rubric gap
systemic architecture problem
time risk
```

---

# Даулет

Отвечает за **HOW между слоями**.

Его зона:

```text
HTTP
schemas implementation
adapters
agent/backend connection
storage
external APIs
errors
runtime
startup
cross-platform
integration fixes
```

Даулет не должен самостоятельно менять meaning contract.

Если считает contract плохим:

```text
показывает проблему Нурасылу
→ Нурасыл принимает решение
→ Даулет реализует.
```

---

# Аки

Отвечает за **что реально видит judge/user**.

Она не должна ждать backend.

Если backend не готов:

```text
shared example response
→ UI development continues
```

Аки не должна:

- самостоятельно менять response schema;
- придумывать backend behavior;
- строить complex state management;
- создавать 7-screen dashboard.

Её главная задача:

> один user flow должен выглядеть настолько ясно, что смысл продукта можно понять почти без объяснений.

---

# 8. Git / integration workflow

## Branch strategy

Три основные рабочие branches:

```text
feat/agents
feat/backend
feat/frontend
```

`main` — интеграционная и demo branch.

После freeze возможны только короткие:

```text
fix/<problem>
```

---

# Directory ownership

Пример:

```text
frontend/        → Аки
backend/         → Даулет
agents/          → Нурасыл
shared/          → contract-controlled
docs/            → shared, Нурасыл owner
```

Не редактировать чужую область без необходимости.

---

# PR policy

Полноценный enterprise PR process не нужен.

### Обычная feature внутри своей директории

Можно merge без formal PR после локального check.

### Change касается:

- shared contract;
- двух областей;
- архитектуры;
- позднего hotfix;

используется короткий PR или совместный review.

Цель не Git ceremony.

Цель — не сломать `main`.

---

# Merge cadence

В конце каждого цикла:

1. commit;
2. push branch;
3. pull latest main;
4. run targeted check;
5. merge;
6. integration smoke test.

### Merge order при contract-dependent изменении

```text
canonical contract
→ producer/backend/agent
→ frontend consumer
```

---

# Кто merge'ит

Каждый owner может merge changes внутри своей области.

Даулет выступает **integration captain**, когда:

- есть conflict между слоями;
- меняется backend-agent interface;
- frontend/backend расходятся;
- порядок merges имеет значение.

Нурасыл не должен становиться штатным merge engineer.

---

# Canonical contract

Human-readable:

```text
docs/BUILD_BRIEF.md
```

Runtime implementation:

```text
Pydantic schemas / backend contract
```

Fixtures:

```text
shared/example-request.json
shared/example-response.json
```

Никакого:

```text
frontend самостоятельно переименовал score
```

или:

```text
agent решил возвращать risk_score_v2
```

---

# Breaking change protocol

Breaking change допустим только так:

```text
1. Обнаружена необходимость.
2. Нурасыл принимает semantic decision.
3. BUILD_BRIEF меняется.
4. Даулет меняет backend/runtime contract.
5. Аки обновляет frontend.
6. Один integration test.
```

На sync это должно занимать минуты.

---

# 9. AI review process каждые 25 минут

Вместо отдельного длинного аудита:

```text
00:00–00:23 build
00:23–00:25 AI compatibility review
00:25–00:30 human sync
```

AI review входит в 25-минутный блок.

---

## Agent reviewer

Проверяет:

```text
input schema
output schema
tool signatures
tool return shape
structured output
timeouts/errors
approval state
evidence
backend compatibility
```

---

## Backend reviewer

Проверяет:

```text
routes
request validation
response shape
serialization
agent integration
frontend contract
timeouts
env
startup
```

---

## Frontend reviewer

Проверяет:

```text
endpoint
request body
response assumptions
missing fields
loading
empty
error
approval
fallback
```

---

## Global compatibility review

Не просить AI «проанализировать весь код и дать 80 рекомендаций».

Prompt objective:

```text
Проверь только текущий diff + canonical contract +
end-to-end demo path.
```

Формат:

```text
GATE: GREEN | YELLOW | RED

BROKEN CONTRACTS
- ...

RUNTIME BLOCKERS
- ...

DEMO RISKS
- ...

FIX NOW — MAX 3
1.
2.
3.

DEFER / CUT
- ...
```

Максимум около 8–10 коротких пунктов.

Если AI начинает советовать рефакторить naming convention — игнорировать.

---

# 10. Строгий 5-minute sync

Каждый sync — ровно пять минут.

## 00:00–00:45 — Health

Каждый отвечает одной фразой:

```text
GREEN / YELLOW / RED
Что реально работает.
```

---

## 00:45–01:45 — Broken

Только:

- blockers;
- contract mismatch;
- runtime failures.

---

## 01:45–02:45 — Integration gate

Что показал end-to-end smoke test?

```text
PASS / FAIL
```

---

## 02:45–03:30 — CUT / Decision

Нурасыл принимает максимум необходимые decisions.

Если спор не закрыт за минуту — Нурасыл выбирает.

---

## 03:30–04:30 — Next 25

Каждый называет **один primary deliverable** следующего цикла.

Не пять задач.

---

## 04:30–05:00 — Git

Кто:

- commit;
- merge;
- fixes blocker.

Старт нового таймера.

---

# 11. Feature-cut strategy

# 14:00

## MUST

- stack запускается;
- backend endpoint существует;
- UI существует;
- primary agent делает реальный model call;
- canonical contract не распался.

## SHOULD

- wire slice работает.

## CUT

- DB;
- specialist #2;
- verifier;
- external integrations;
- animations.

---

# 15:00

## MUST

- настоящий vertical slice;
- один meaningful tool/data path;
- structured result;
- UI показывает результат;
- demo fixture;
- basic errors.

## SHOULD

- три успешных run подряд;
- evidence.

## CUT

Если core красный:

- multi-agent;
- real external API;
- complex storage;
- dashboard extras.

---

# 16:00

## MUST

- стабильный core;
- evidence;
- user flow;
- risk/HumanGate если нужен case;
- fallback concept.

## SHOULD

- second specialist или verifier, если оправданы;
- agent activity UI.

## CUT

- третий agent;
- второй external API;
- fancy animations;
- advanced persistence.

---

# 16:30

## MUST

- rubric-critical functionality;
- stable demo path.

## CUT EVERYTHING NEW.

# HARD FEATURE FREEZE.

---

# 17:00

## MUST

- cold startup;
- fallback;
- README;
- second-machine test;
- demo script;
- screenshots.

## CUT

Любые stretch features.

---

# 17:30

## MUST

- две успешные rehearsals;
- clean main;
- submission materials;
- no secrets;
- fallback works.

# CODE LOCK.

---

# 12. Feature freeze

## Hard freeze: 16:30

Почему не 17:00?

Потому что после 16:30 остаётся ровно три цикла:

```text
16:30–17:00 reliability
17:00–17:30 rehearsal
17:30–18:00 submission
```

Это здоровая структура.

Если freeze поставить на 17:00, любой крупный bug съест либо rehearsal, либо submission.

### Early freeze

Если в 16:00 core всё ещё нестабилен:

```text
FEATURE FREEZE = 16:00
```

Автоматически.

---

# 13. Presentation / demo process

Презентация никогда не блокирует core.

## 15:30+

Аки может сохранять:

- screenshots;
- visual states;
- interesting evidence;
- working agent timeline.

Это занимает секунды, а не отдельный cycle.

---

## 16:00+

Если core Green:

Аки начинает собирать:

- problem screenshot/visual;
- solution screenshot;
- product screen;
- evidence/HumanGate screen.

---

## 16:30+

Архитектура заморожена.

Теперь можно сделать architecture diagram.

Не раньше.

Иначе она будет перерисовываться.

---

# Problem / solution narrative

Нурасыл формулирует текст.

Аки оформляет.

---

# Demo script

Первый draft: около 16:30–16:45.

Структура:

```text
1. Проблема.
2. Что делает пользователь.
3. Agent начинает работу.
4. Tool/evidence.
5. Decision/result.
6. HumanGate при необходимости.
7. Business value.
```

---

# Rehearsals

### Rehearsal #1

Около 17:05.

Цель:

- обнаружить технические и narrative проблемы.

### Rehearsal #2

Около 17:20.

Цель:

- точный final flow.

### Rehearsal #3

После 17:35 только если submission уже под контролем.

---

# Demo roles

### Нурасыл

- главный narrator;
- управляет product flow;
- объясняет AI/FinTech logic.

### Аки

- presentation/slides;
- visual fallback;
- помогает с screen transitions.

### Даулет

# Demo Ops

Во время показа:

- backend already running;
- logs открыты;
- знает fallback;
- может быстро перезапустить сервис;
- не меняет код.

---

# 14. Demo reliability / fallback

# MUST

## 1. Seed data

Один основной deterministic demo case.

Не выбирать случайные данные прямо перед жюри.

---

## 2. Known-good path

Команда знает заранее:

```text
какой input
→ какой тип поведения
→ какой ожидаемый output class
```

Не обязательно hardcode exact LLM wording.

---

## 3. Mock external boundary

Если реальный external API ненадёжен:

```text
adapter interface остаётся
implementation переключается на simulated data
```

И это честно обозначается.

---

## 4. Real AI

Core inference остаётся настоящим.

Fallback не должен превращать проект в полностью static demo.

---

## 5. Timeouts

External APIs должны быстро fail.

AI flow не должен бесконечно висеть.

Demo-oriented target:

```text
bounded call
→ timeout
→ friendly recovery
```

Конкретные секунды выбираются после измерения фактической latency.

---

## 6. Friendly error state

UI не должен показывать:

```text
Internal Server Error
```

без объяснения.

Нужны:

```text
Retry
Use demo data
Show last successful run
```

где это уместно.

---

## 7. Previous successful result

После настоящего successful run можно сохранить structured result.

Если network/API умер во время demo:

```text
Last successful verified run
```

может быть показан как fallback.

Важно назвать его именно fallback/replay, а не выдавать за live execution.

---

## 8. Backup path

Primary:

```text
live AI + live/local tools
```

Fallback A:

```text
live AI + simulated external tool
```

Fallback B:

```text
replay last successful structured run
```

---

# NICE TO HAVE

- short screen recording;
- hosted deployment;
- second demo scenario;
- multiple personas;
- monitoring dashboard.

Только после MUST.

---

# 15. Cross-platform strategy

Команда:

- 2 Mac;
- 1 Windows.

Нельзя надеяться, что «разберёмся потом».

## До 13:00

Без написания hackathon code проверить:

```text
git
GitHub auth
python
node
npm
Codex
OpenAI access
browser
network
```

---

# Runtime discipline

После выбора stack:

- фиксируется одна поддерживаемая Python version;
- фиксируется одна Node version;
- commit lockfiles;
- создаётся `.env.example`;
- не используются абсолютные paths;
- не используются `/Users/...`;
- README не зависит только от Bash.

Предпочитать команды вида:

```text
python -m ...
npm install
npm run dev
```

вместо сложных shell scripts.

---

# Demo machine

К 16:30 назначается primary demo laptop.

К 17:00 core должен запускаться ещё минимум на одном laptop команды.

Не обязательно поднимать всё одновременно на трёх.

---

# 16. Database / state decision framework

# In-memory / JSON

Использовать, когда:

- один demo session;
- seed data;
- read-only fixture;
- состояние после restart не важно.

Это **самый предпочтительный вариант**, если его достаточно.

---

# SQLite

Использовать, если demo требует:

- case history;
- approval persistence;
- audit trail;
- multiple runs;
- state between steps.

---

# PostgreSQL

Использовать только если:

- официальный case требует;
- предоставлена готовая инфраструктура;
- нужна реальная multi-user/concurrency семантика;
- PostgreSQL capability непосредственно важна для demo.

Не ради «production readiness».

---

# Vector DB

Только если retrieval является центральной частью challenge и:

- corpus реально значимый;
- semantic retrieval улучшает результат;
- обычного filtering/full-text/in-memory embeddings недостаточно.

Если у вас 10 документов, Qdrant вам почти наверняка не нужен.

---

# 17. Agent harness decision

# Оставляем OpenAI Agents SDK, если

Есть:

- 1–3 tool-using agents;
- structured outputs;
- handoff/delegation;
- bounded execution;
- tracing;
- небольшое число tools.

Это ваш наиболее вероятный режим.

---

# Рассматриваем более простой approach, если

Challenge — это:

```text
extract → validate → calculate → return
```

Тогда обычные Python functions + один LLM call могут быть лучше agent framework.

---

# Deterministic workflow

Если процесс заранее известен:

```text
Step A
→ Step B
→ Step C
```

не нужно заставлять agent «решать», какой следующий шаг, если выбора реально нет.

---

# Strict policy / rules engine

High-impact financial policy:

```text
детерминированные правила в коде
```

AI может:

- extract;
- classify;
- summarize;
- collect evidence.

Но formal policy лучше не отдавать исключительно вероятностной модели.

---

# Complex state machine / long-running

Другой orchestration framework имеет смысл только если:

- это реально требуется challenge;
- команда уже умеет им пользоваться.

Осваивать новый graph framework на HackAlem — плохой trade-off.

---

# Heavy RAG

Тогда основной engineering problem:

```text
ingestion
retrieval
grounding
citations
```

а не количество agents.

---

# 18. HumanGate / risk policy

Policy принимается в **13:21–13:25**.

Для каждого action:

```text
Impact?
Reversible?
Financial consequence?
Regulatory consequence?
Can human review meaningfully help?
```

### Low risk

Agent выполняет.

### High impact

```text
Agent investigates
→ prepares action
→ presents evidence
→ requires approval
→ executes/simulates after approval
```

---

# Backend impact

Нужны states вроде:

```text
completed
approval_required
approved
rejected
failed
```

Только необходимые case.

---

# Agent impact

Agent не должен обходить HumanGate через другой tool.

---

# Frontend impact

Пользователь должен ясно видеть:

- почему требуется approval;
- что произойдёт после approval;
- evidence;
- approve/reject.

---

# Demo impact

HumanGate может быть очень сильным moment:

```text
AI сделал 80% работы,
но критичное решение человек контролирует.
```

Если такой момент соответствует case.

---

# 19. Commit strategy

Не commit каждую минуту.

Но желательно видимое продвижение каждые 30–60 минут.

Пример:

### ~13:30

```text
docs: lock challenge scope and build contract
```

### ~14:00

```text
feat: add runnable system skeleton
```

### ~14:30

```text
feat: complete end to end agent flow
```

### ~15:00

```text
fix: stabilize core flow
```

### ~15:30

```text
feat: add challenge relevant agent depth
```

### ~16:00

```text
feat: add evidence and approval flow
```

### ~16:30

```text
feat: close rubric gaps and freeze features
```

### ~17:00

```text
fix: harden demo runtime
```

### ~17:30

```text
fix: finalize demo experience
```

### ~17:50

```text
docs: finalize setup and submission
```

Это не жёсткие обязательные commit messages, а milestones.

---

# 20. Contingency branches

# Scenario A — 14:30, frontend/backend ещё не соединены

## Действия

Немедленно:

- freeze agent complexity;
- Даулет + Аки работают вместе над одним endpoint;
- canonical fixture становится единственным contract;
- Нурасыл прекращает agent feature work.

Нурасыл занимается только:

- contract diagnosis;
- минимизацией output.

## CUT

- second agent;
- DB;
- external API;
- advanced UI.

## Нельзя

Продолжать каждому строить свою половину ещё 30 минут.

---

# Scenario B — Agent работает плохо

## Действия

- collapse до одного agent;
- уменьшить свободу prompt;
- structured output;
- дать agent более конкретные tools;
- deterministic business rules вынести в код;
- использовать clean demo fixture.

## CUT

- handoffs;
- extra specialists;
- verifier, если он только добавляет latency.

## Нельзя

Добавлять ещё agents в надежде, что они исправят первого.

---

# Scenario C — External API не работает

## Действия

Через 10–15 минут максимум:

```text
live adapter → simulated adapter
```

Interface сохраняется.

UI/README честно показывают simulation.

## Нельзя

Потратить час на reverse engineering чужого API.

---

# Scenario D — Multi-agent orchestration нестабильна

## Действия

```text
orchestrator + tools
```

или:

```text
single agent + deterministic workflow
```

Specialists collapse.

## Сохраняем

- tool use;
- evidence;
- HumanGate;
- structured output.

Жюри важнее работа, чем количество кружков на architecture diagram.

---

# Scenario E — UI сильно отстаёт

Аки делает один screen.

```text
Input
↓
Activity
↓
Evidence
↓
Decision
↓
Approval
```

Если flow позволяет.

## CUT

- routing;
- dashboard;
- animations;
- charts без необходимости;
- design system.

Даулет/Нурасыл не перепрыгивают полностью во frontend.

Они дают Аки стабильный contract.

---

# Scenario F — 16:30, core нестабилен

Немедленно:

# EMERGENCY FREEZE

Все трое работают только над одним demo path.

Никакой презентации кроме backup screenshots.

Никаких новых features.

Приоритет:

```text
runtime
→ fallback
→ one rehearsal
→ submission
```

---

# Scenario G — критический bug за 30 минут до конца

Не рефакторить.

Порядок:

```text
1. Can we revert?
2. Can we disable broken stretch feature?
3. Can we switch adapter?
4. Can we use last successful run?
5. Only then patch.
```

Предпочтение:

```text
known-good commit
```

перед экспериментальным fix.

---

# 21. Если идём впереди плана

Если True Vertical Slice работает раньше 14:30, не начинать случайные stretch features.

Приоритет улучшений:

## 1. Rubric gaps

Что ещё даёт реальные points?

## 2. Reliability

Может ли система выдержать 10 runs?

## 3. Evidence / trust

Понятно ли, почему система пришла к результату?

## 4. HumanGate / policy

Если релевантно case.

## 5. Agent depth

Второй specialist/verifier только здесь.

## 6. Demo visualization

Activity/evidence.

## 7. One meaningful real integration

Если она усиливает credibility.

## 8. Visual polish

Самый последний слой.

---

# 22. Definition of Done

# Core Done

Проект уже можно показать, когда:

- frontend запускается;
- backend запускается;
- user выполняет основной action;
- real AI реально участвует;
- есть meaningful tool/data interaction;
- возвращается structured result;
- UI показывает result;
- errors не роняют всё приложение;
- mandatory core challenge requirement выполнен.

---

# Demo Ready

Дополнительно:

- deterministic seed scenario;
- три последовательных successful runs;
- evidence понятно;
- HumanGate работает, если нужен;
- timeout есть;
- fallback есть;
- UI loading/error states есть;
- demo script готов;
- cold startup проверен;
- primary demo laptop готов.

---

# Submission Ready

Дополнительно:

- `main` содержит final build;
- README;
- setup;
- `.env.example`;
- no secrets;
- dependency files committed;
- required submission fields заполнены;
- links проверены;
- GitHub history показывает progress;
- последний commit pushed;
- второй человек подтвердил, что repository открывается/запускается.

---

# Stretch

Только после первых трёх:

- дополнительный specialist;
- verifier;
- extra tool;
- real secondary integration;
- richer animations;
- additional scenarios;
- deployment;
- advanced analytics.

---

# 23. Decision log template

Не писать длинные ADR.

Использовать одну строку на решение:

```md
# Decision Log

- [13:17] D-01 — Выбран <concept>. Why: лучше закрывает <rubric/must>. Owner: N. Contract impact: none.
- [13:22] D-02 — <integration> simulated. Why: live API unavailable / not required. Owner: N+D. Contract impact: tool interface unchanged.
- [15:04] D-03 — Specialist B CUT. Why: core instability. Owner: N. Contract impact: none.
```

Этого достаточно.

---

# 24. Status board template

```text
CORE: GREEN / YELLOW / RED
TIME: 15:42
STAGE: STAGE-06

N | NOW: verifier | BLOCKED: no | NEXT: output tuning
D | NOW: approval endpoint | BLOCKED: no | NEXT: fallback
A | NOW: evidence UI | BLOCKED: approval schema | NEXT: HumanGate

BROKEN
- approval response missing reason

FIX NOW
- D adds reason field after N confirms contract

CUT
- second external API
- animated graph

NEXT GATE
16:00 — evidence + HumanGate end-to-end
```

Нурасыл должен понимать состояние примерно за 15 секунд.

---

# 25. Master timeline

| Время | Stage | Нурасыл | Даулет | Аки | Общий deliverable | Gate |
|---|---|---|---|---|---|---|
| 13:00–13:08 | STAGE-00 Challenge Intake | Problem/AI need | Requirements/constraints | Rubric/demo expectations | Parsed challenge | Все понимают literal requirements |
| 13:08–13:30 | STAGE-01 Solution Lock | Demo story, scope, contract | Architecture feasibility | UI states | BUILD_BRIEF | Solution Lock |
| 13:30–14:00 | STAGE-02 Skeleton | Primary agent | API/schemas | UI + mock | Runnable skeleton | Wire slice |
| 14:00–14:30 | STAGE-03 Vertical Slice | Agent + tool | Full connection | Real API rendering | True E2E | **Mandatory vertical slice** |
| 14:30–15:00 | STAGE-04 Core Stabilization | Prompt/output quality | Errors/runtime | Core UX | Stable core | 3 successful runs |
| 15:00–15:30 | STAGE-05 Agent Depth | Specialist/verifier if justified | Integrate depth | Activity states | Stronger agentic system | Core must remain Green |
| 15:30–16:00 | STAGE-06 Evidence/Gate | Evidence/risk | Approval/trace | Evidence/HumanGate UI | Explainable flow | End-to-end trust layer |
| 16:00–16:30 | STAGE-07 Rubric Closure | Rubric audit/script | Fallback/runtime | Polish/assets | Scoring build | **Feature freeze** |
| 16:30–17:00 | STAGE-08 Reliability | Agent P0 fixes | Runtime/cross-platform | Error/fallback UI | Demo-ready build | Cold startup PASS |
| 17:00–17:30 | STAGE-09 Demo Ready | Narration/rehearsal | Demo ops | Presentation/assets | 2 rehearsals | **Code lock** |
| 17:30–18:00 | STAGE-10 Submission | Coverage/submission | Repo/setup | Assets/final visual | Submitted project | Final verification |

---

# 26. Red-team review

Перед финализацией я атаковал этот план как технический lead, который ожидает, что всё пойдёт хуже, чем кажется.

## Проблема 1 — слишком много ответственности на Нурасыле

Первоначально Нурасыл одновременно:

- lead;
- product;
- architecture;
- agents;
- integration review;
- demo.

Это создаёт single point of failure.

### Correction

Нурасыл больше **не integration mechanic**.

Даулет получает роль integration captain.

Аки самостоятельно развивается по canonical fixture.

Нурасыл вмешивается только в semantics/scope/rubric.

---

# Проблема 2 — Даулет может стать bottleneck

Если через Даулета проходят:

- backend;
- agent connection;
- frontend connection;
- Git merges;
- external APIs;
- DB;

он физически становится choke point.

### Correction

Frontend никогда не ждёт backend.

Agent layer имеет самостоятельный callable boundary.

Owners сами merge изменения своей директории.

Даулет вмешивается только в cross-layer integration.

---

# Проблема 3 — Аки легко заблокировать

Frontend может два часа ждать:

> «backend почти готов».

### Correction

К 13:30 должен существовать canonical fixture.

Frontend строится на нём сразу.

---

# Проблема 4 — 25/5 может съедать слишком много времени

9 sync × 5 минут = 45 минут.

Но без coordination вы рискуете потерять больше часа на позднюю интеграцию.

### Correction

Оставляем rhythm.

Но AI review идёт параллельно в последние две минуты рабочего блока.

Sync жёстко ограничен пятью минутами.

---

# Проблема 5 — multi-agent temptation

Ваш технический профиль делает особенно вероятной мысль:

> «Core работает, давайте сразу orchestrator + 3 specialists + verifier».

### Correction

Second specialist **запрещён до 15:00**, если только challenge буквально не требует нескольких независимых roles.

Добавлять максимум одну архитектурную единицу за cycle.

---

# Проблема 6 — SQLite был слишком сильным default

Даже SQLite создаёт:

- schema;
- storage layer;
- migrations/initialization;
- debugging.

Для одного demo run это может быть wasted complexity.

### Correction

Новый default:

```text
in-memory / JSON first
SQLite only when state proves useful
```

---

# Проблема 7 — presentation могла начаться поздно

Ждать 17:00 и только потом собирать assets рискованно.

### Correction

Аки начинает **пассивный asset capture около 15:30**, но dedicated presentation work только после core stability.

---

# Проблема 8 — architecture diagram может стать stale

Если нарисовать её в 14:00, к 16:00 архитектура изменится.

### Correction

Final architecture diagram делается после feature freeze в 16:30.

---

# Проблема 9 — Git workflow мог быть слишком тяжёлым

Три inexperienced Git users + mandatory PRs = overhead.

### Correction

Нет обязательных PR.

Directory ownership + frequent merge + `main` runnable.

PR только для shared/breaking/late changes.

---

# Проблема 10 — freeze в 17:00 слишком поздний

60 минут недостаточно одновременно для:

- reliability;
- cross-platform;
- rehearsals;
- submission.

### Correction

Hard freeze = **16:30**.

Code lock = **17:30**.

---

# Проблема 11 — real API obsession

FinTech case может соблазнить подключить несколько live integrations.

### Correction

External API получает максимум примерно 10–15 минут на proof-of-life.

Если не работает и не mandatory:

```text
simulated adapter
```

---

# Проблема 12 — AI coding agents могут «улучшить» архитектуру

Codex/Claude любят:

- abstractions;
- refactors;
- extra dependencies;
- schema changes.

### Correction

Каждый coding prompt должен включать:

```text
Do not change stack.
Do not rename contract fields.
Do not add dependencies unless necessary.
Do not modify other owners' directories.
Prefer smallest implementation.
```

Stage-specific prompts должны наследовать эти guardrails.

---

# 27. Final recommended operating model

Весь HackAlem можно свести к одной operational loop:

```text
OFFICIAL CASE
↓
LOCK WHAT / WHY
↓
LOCK CONTRACT
↓
BUILD ONE VERTICAL FLOW
↓
PROVE IT WORKS
↓
ADD ONLY RUBRIC-RELEVANT DEPTH
↓
FREEZE AT 16:30
↓
HARDEN
↓
REHEARSE
↓
SUBMIT
```

Роли должны оставаться очень чёткими:

```text
Нурасыл
WHAT / WHY / scope / AI / canonical semantics

Даулет
HOW backend / integration / runtime

Аки
HOW user sees and operates the product
```

А центральный технический invariant всего дня:

```text
main branch
+
one canonical contract
+
one working demo story
```

Если они сохраняются — команда контролирует проект.

Если они распадаются — никакое количество agents или красивых screens уже не спасёт последние полчаса.

---

# FINAL HACKATHON RULE

В любой момент задайте один вопрос:

> Если прямо сейчас организаторы скажут «время вышло, покажите, что есть», можем ли мы открыть продукт и провести понятный рабочий flow?

Если ответ **да** — можно усиливать решение.

Если ответ **нет** — никакие новые features не начинаются.