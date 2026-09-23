# HackAlem AI 2026 — контекст хакатона для Codex

> **Назначение файла:** дать Codex единый контекст о HackAlem AI, его правилах, формате и ограничениях нашей команды.
>
> **Актуальность:** 22 сентября 2026, накануне основного хакатона.
>
> **Приоритет источников:** официальный регламент/платформа HackAlem → официальный Telegram HackAlem → официальный сайт → заявления организаторов/партнёров → рабочий контекст команды.
>
> Если информация в кейсе, на платформе или в сообщении организаторов 23 сентября противоречит этому файлу, **актуальный регламент организаторов имеет приоритет**.

---

## 1. Что такое HackAlem AI

HackAlem AI — крупный офлайн **agentic-AI hackathon** в Астане, проводимый при участии OpenAI и казахстанской AI/tech-экосистемы.

Основная задача участников — за очень ограниченное время создать **работающее AI-решение / AI-агента** под конкретную задачу одного из отраслевых треков.

Ключевая особенность формата:

- AI должен использоваться не только как помощник при разработке;
- в решении ожидается применение AI как существенной части продукта;
- **Codex должен использоваться командой в процессе разработки**;
- задачи основаны на прикладных/реальных кейсах;
- у конкретного кейса могут быть собственные критерии оценки.

Организаторы и партнёры, фигурирующие в официальных материалах:

- Министерство искусственного интеллекта и цифрового развития Республики Казахстан;
- Astana Hub;
- Silkroad Innovation Hub;
- AI & Digital Bridge;
- Blockchain & AI Technology Center / BAITC;
- OpenAI;
- среди партнёров также упоминались NVIDIA и другие технологические организации.

---

## 2. Дата, место и расписание

### Основной день

**23 сентября 2026, Астана.**

Формат: **полностью офлайн**.

Площадка:

**Международный выставочный центр (EXPO), проспект Мангилик Ел, 53/1, Астана.**

### Расписание 23 сентября

- **09:00–12:00 — offline check-in**
- **12:00–13:00 — открытие хакатона**
- **13:00–18:00 — основной coding/building window**
- фактическое время на разработку: **5 часов**

Важно:

- после check-in организаторы сообщали, что **выходить с площадки нельзя**;
- количество мест ограничено;
- в материалах используется принцип **first come, first served**.

---

## 3. Таймлайн после основного хакатона

По официальному сайту:

- **23.09 — Opening Ceremony + Hackathon**
- **24–28.09 — проверка и экспертная оценка решений**
- **29.09 — Demo Day для финалистов**
- **01.10 — награждение в рамках AI & Digital Bridge**

То есть 23 сентября команда строит и сдаёт решение, но финальная защита лучших проектов проходит позже.

---

## 4. Команды

Максимальный размер команды:

**до 3 человек.**

Даже solo-участник на платформе должен создать команду соответствующей категории.

Команду необходимо было сформировать заранее. Организаторы отдельно предупреждали, что **собирать или менять состав команды во время самого хакатона нельзя**.

### Наша команда

Нас **3 человека**.

Рабочее распределение ролей:

1. **Frontend / UI**
2. **Backend / integrations**
3. **AI agents / orchestration / AI integration**

Роли не являются жёсткими: при 5-часовом лимите участники могут помогать друг другу там, где возникает bottleneck.

---

## 5. Наш трек

Наша команда выбрала:

# **FinTech**

На HackAlem предусмотрено **10 отраслевых направлений**.

В публичных материалах среди направлений назывались:

- FinTech;
- строительство;
- государственные услуги;
- образование;
- здравоохранение;
- сельское хозяйство;
- и другие приоритетные отрасли экономики.

Полный конкретный набор кейсов и точный rubric для FinTech нужно считать неизвестным до публикации кейса на платформе.

### Главное правило для Codex

**Не пытаться заранее подгонять неизвестный FinTech-кейс под нашу старую идею.**

После публикации задания:

1. прочитать формулировку кейса полностью;
2. найти explicit deliverables;
3. найти критерии оценки;
4. определить обязательные ограничения;
5. только после этого проектировать решение.

---

## 6. Где ведётся разработка

Это один из наиболее важных пунктов регламента.

**Вся разработка должна идти строго в командном GitHub-репозитории, созданном/выданном платформой HackAlem.**

Организаторы отдельно предупреждали:

- работать нужно именно в командном GitHub;
- прогресс фиксируется;
- **прогресс отслеживается каждый час**;
- нарушение правил может привести к **дисквалификации**.

### Следствие для Codex

Во время хакатона:

- считать официальный командный repository единственным рабочим project source of truth;
- создавать и изменять код внутри него;
- регулярно сохранять рабочий прогресс;
- делать понятные commits;
- не прятать разработку в сторонних/private repositories;
- не переносить готовый заранее написанный продукт в официальный repo;
- не использовать существующую production-codebase другого проекта как основу, если это не разрешено организаторами.

---

## 7. Что известно о подготовке заранее

Организаторы прямо рекомендуют заранее:

- зарегистрироваться на платформе;
- сформировать команду;
- получить доступ к командному GitHub;
- проверить GitHub;
- установить и проверить необходимые инструменты;
- заранее познакомиться с **Codex**;
- заранее познакомиться с **OpenAI API**;
- проверить ноутбук и интернет;
- подготовить рабочую среду.

### Наше рабочее понимание ограничений

Наша команда исходит из следующего:

#### Нельзя заранее

- писать код конкретного hackathon-проекта;
- приносить готовый реализованный продукт;
- заранее делать готовое техническое решение неизвестного кейса;
- заранее готовить финальную презентацию под неизвестный кейс.

#### Можно готовить

- знания и research;
- рабочие процессы команды;
- prompts;
- prompt templates;
- инструкции для Codex;
- checklists;
- общие архитектурные паттерны;
- UX-подходы и понимание интерфейсных паттернов;
- знакомство с технологиями;
- настройку среды и инструментов.

> Этот блок отражает **рабочее понимание нашей команды**. Если 23 сентября организаторы дадут более точное правило, следовать ему.

---

## 8. Codex — обязательная часть процесса

В официальных требованиях HackAlem указано, что команда должна использовать **Codex** во время разработки.

Codex здесь нужно воспринимать не как необязательный autocomplete, а как один из основных инструментов building process.

На площадке/через инфраструктуру хакатона участникам предоставляется доступ к технологическим ресурсам OpenAI.

В материалах HackAlem фигурируют:

- около **$600,000 совокупных OpenAI API credits/resources для участников**;
- около **$300,000 доступа к Codex**;
- дополнительные ресурсы/призы для победителей.

Фактические credentials, promo codes, limits и способ активации нужно брать только с платформы HackAlem / Telegram-бота в день хакатона.

### Для Codex

Не предполагать заранее:

- конкретный API key;
- конкретные rate limits;
- конкретную сумму credits на нашу команду;
- доступность конкретной модели;
- доступность стороннего сервиса.

Сначала проверить реально выданные credentials и доступные инструменты.

---

## 9. OpenAI API

В официальных и партнёрских материалах HackAlem OpenAI API фигурирует как один из основных ресурсов для разработки AI-решений.

Практический принцип:

**если use case можно убедительно реализовать через OpenAI API + нормальную application logic, не усложнять стек без необходимости.**

Agentic-часть должна быть функциональной, а не декоративной.

Хорошие признаки agentic solution:

- model получает задачу/intent;
- анализирует контекст;
- выбирает или вызывает tools;
- выполняет несколько осмысленных шагов;
- работает со structured output;
- принимает решение в пределах разрешённых полномочий;
- оставляет понятный trace / evidence;
- при рискованном действии запрашивает human approval.

Но конкретная архитектура должна вытекать из кейса.

---

## 10. Кейсы и критерии оценки

Хакатон построен вокруг **реальных отраслевых кейсов**.

Для каждого кейса могут быть собственные критерии.

Из интервью с организаторами:

- в каждом треке есть конкретные задачи;
- у задачи есть свои критерии оценки;
- решения оценивает независимое жюри;
- сильнейшие проекты проходят дальше на Demo Day;
- часть кейсов создаётся совместно с компаниями;
- хороший проект потенциально может перейти в дальнейшее сотрудничество или пилот.

### Поэтому Codex не должен выдумывать rubric

Сразу после публикации кейса нужно сохранить в проекте отдельный блок:

```md
## Challenge
...

## Mandatory requirements
...

## Evaluation criteria
...

## Submission requirements
...

## Non-goals
...
```

И использовать его как основу всех технических решений.

---

## 11. Формат результата

Цель за 5 часов — не production-ready система.

Цель — максимально убедительный **working prototype**, который:

1. решает конкретную боль из кейса;
2. реально работает end-to-end;
3. демонстрирует AI/agentic behavior;
4. понятен за короткое demo;
5. технически достаточно надёжен, чтобы demo не развалилось;
6. показывает ценность лучше, чем набор абстрактных AI-фич;
7. соответствует конкретному rubric.

При конфликте между:

- большим количеством features;
- и стабильным end-to-end flow,

приоритет — **стабильный end-to-end flow**.

---

## 12. Техническая дисциплина во время 5 часов

Рекомендуемый принцип работы:

### Не строить всё сразу

Сначала создать minimum vertical slice:

**input → AI reasoning/tool use → result → UI/demo**

После того как этот путь реально работает, добавлять улучшения.

### Порядок приоритета

1. Challenge compliance
2. Working end-to-end flow
3. Demo reliability
4. Core agentic behavior
5. UX clarity
6. Evidence / auditability
7. Additional features
8. Polish

### Не тратить время без необходимости на

- сложную production infrastructure;
- Kubernetes;
- microservices ради microservices;
- полноценную auth-систему;
- масштабируемость на миллионы пользователей;
- огромную БД;
- полноценный billing;
- сложный design system;
- абстрактную multi-agent architecture без пользы для кейса.

---

## 13. Git / commit discipline

Так как прогресс в GitHub отслеживается, Codex должен помогать поддерживать прозрачную историю разработки.

Желательно:

- commit после первого runnable skeleton;
- commit после working backend flow;
- commit после AI/tool integration;
- commit после frontend integration;
- commit после demo-ready state;
- commit после финальных fixes.

Не ждать конца 5 часов для первого крупного commit.

Commit messages должны быть понятными, например:

```text
feat: add challenge workflow skeleton
feat: implement agent tool execution
feat: connect frontend to agent API
fix: stabilize demo error handling
docs: add setup and demo instructions
```

---

## 14. Оборудование и доступ

Организаторы рекомендуют взять:

- ноутбук;
- зарядное устройство;
- **LAN adapter / USB-C → RJ45**;
- всё необходимое для локальной разработки.

В ранних материалах также рекомендовался ноутбук с хорошей поддержкой Wi-Fi (5 GHz / Wi-Fi 6), но организаторы явно делают акцент на проводном подключении как более стабильном варианте.

Перед стартом должны быть проверены:

- GitHub access;
- Codex;
- OpenAI tooling;
- local runtime;
- package managers;
- browser;
- IDE/editor;
- LAN/network;
- Git identity;
- необходимые аккаунты.

---

## 15. Telegram-бот и платформа

Через HackAlem platform / Telegram bot участникам должны поступать:

- организационная информация;
- доступ к командному GitHub;
- данные по кейсу;
- доступы / promo codes для OpenAI ресурсов;
- Codex-related access;
- важные объявления.

### Приоритет информации во время хакатона

Если возникает противоречие:

1. сообщение организатора на площадке;
2. актуальный case page / platform;
3. официальный Telegram / bot;
4. этот файл;
5. наши прошлые предположения.

---

## 16. Наша предварительная FinTech-подготовка

До раскрытия официального FinTech-кейса мы исследовали несколько направлений.

Это **idea bank, а не обязательная концепция проекта**.

Обсуждались:

### Financial Trust Agent / Financial Trust Mesh

Agentic interoperability layer для финансовых процессов между несколькими системами или организациями.

Идея:

- принять financial intent;
- собрать необходимые evidence;
- проверить документы;
- проверить policy/compliance;
- определить допустимый маршрут;
- запросить human approval при необходимости;
- выполнить или симулировать execution;
- сформировать verifiable result / audit trail.

Короткий принцип:

**AI proposes. Policy permits. Rail executes.**

### Cross-Border B2B Payment Trust Agent

Пример сценария:

> Компания хочет оплатить зарубежный invoice.

Агент:

1. принимает intent;
2. проверяет invoice;
3. проверяет identity / credentials;
4. делает compliance/policy checks;
5. сравнивает допустимые payment routes;
6. предлагает маршрут;
7. получает human approval;
8. выполняет/симулирует транзакцию;
9. создаёт trace / receipt.

### AI Financial Investigator

Unit21-like направление:

- приходит fraud/risk alert;
- AI собирает evidence;
- анализирует историю операций;
- анализирует связи/entities/devices;
- формирует reasoning;
- формирует recommendation;
- финальное чувствительное решение остаётся за человеком.

### Financial Twin / SME Finance

Другой исследованный угол:

- объединить financial data;
- оценить cash flow;
- обнаружить проблемы;
- спрогнозировать ситуацию;
- оценить financing readiness;
- сформировать explainable report.

### Важно

Ни одна из этих идей **не должна форсироваться**, если официальный кейс требует другое решение.

Codex должен использовать эти исследования только как библиотеку паттернов.

---

## 17. Customer discovery / отраслевой контекст

Команда заранее изучала FinTech и собиралась использовать Astana Financial Day / профильные мероприятия для понимания отраслевых болей.

Рассматривались реальные проблемные области:

- KYC / KYB;
- AML;
- fraud;
- sanctions/compliance;
- transaction monitoring;
- reconciliation;
- reporting;
- underwriting / credit assessment;
- cross-border payments;
- fragmented workflows;
- большое количество ручных проверок;
- необходимость audit trail;
- human approval в high-risk financial actions.

Это полезный problem-space context, но конкретный HackAlem challenge имеет приоритет.

---

## 18. Что Codex должен сделать сразу после получения кейса

Когда официальный кейс станет известен, НЕ начинать хаотично писать код.

Последовательность:

### Шаг 1 — разобрать кейс

Выдать кратко:

- problem;
- target user;
- expected outcome;
- mandatory requirements;
- evaluation criteria;
- available resources;
- constraints.

### Шаг 2 — определить demo story

Одно предложение:

> `Пользователь делает X → система делает Y → получает Z.`

Если это предложение невозможно сформулировать понятно, scope слишком большой.

### Шаг 3 — выбрать минимальный architecture

Определить только необходимое:

- frontend;
- backend;
- AI/model;
- tools;
- data/storage;
- external integrations;
- human gate.

### Шаг 4 — разделить работу на 3 параллельных потока

Пример:

- Person A: frontend/demo UX;
- Person B: backend/integrations;
- Person C: agent/OpenAI logic.

### Шаг 5 — сделать vertical slice

Как можно раньше получить работающий:

```text
UI
→ backend
→ AI
→ tool/data
→ response
→ UI
```

### Шаг 6 — только потом расширять

Добавлять:

- второй tool;
- better reasoning;
- evidence;
- metrics;
- visualization;
- polish.

---

## 19. Анти-паттерны

Во время HackAlem не делать следующее без сильной причины:

### 1. Fake AI

UI показывает «AI анализирует», но на деле всё hardcoded.

### 2. Chatbot-only

Обычный чат поверх LLM без meaningful action/tool use, если challenge требует agentic solution.

### 3. Architecture astronautics

Сложная multi-agent схема, которая не повышает качество demo.

### 4. Too many integrations

Пять реальных банков/API за 5 часов почти наверняка хуже, чем 1–2 хорошо работающих tool interfaces или mocks, если mocks разрешены кейсом.

### 5. No human gate in high-risk flow

Для финансовых решений с реальными последствиями autonomous execution без контроля может быть плохим product decision.

### 6. Presentationware

Красивый интерфейс без работающего flow.

### 7. Backend-only demo

Технически сильная система, которую жюри невозможно быстро понять.

### 8. Overbuilding

Пытаться за 5 часов создать полноценный production fintech platform.

---

## 20. Что считать успехом к 18:00

Минимальный хороший final state:

- repository запускается;
- README содержит setup;
- challenge requirements закрыты;
- основной user flow работает;
- AI реально используется;
- Codex использовался при разработке;
- tool/integration flow работает или корректно симулирован в разрешённых границах;
- критические ошибки обработаны;
- frontend демонстрирует value;
- есть понятные demo data;
- можно показать продукт за несколько минут;
- есть backup demo path на случай нестабильного внешнего API;
- Git history показывает реальную работу команды во время hackathon window.

---

## 21. Призы и ресурсы

В официальных материалах HackAlem заявлялся общий объём:

# **$1.1M в призах и технологических ресурсах**

Публичная разбивка:

- **$600k** — совокупные OpenAI API resources для участников;
- **$300k** — доступ к Codex;
- **$100k** — дополнительные OpenAI API tokens для победителей;
- **$100k** — денежный призовой фонд.

Также:

- фирменный merch;
- сертификаты;
- Demo Day;
- награждение на AI & Digital Bridge;
- потенциальная возможность продолжения проекта / pilot с компаниями для некоторых кейсов.

Не считать эти суммы прямым allocation нашей команде.

---

## 22. Участники и масштаб

Публично заявлено:

- до **2500 участников / мест**;
- формат offline;
- 18+;
- участвуют студенты, IT-специалисты, разработчики, дизайнеры, инженеры, AI/ML специалисты, фрилансеры и tech enthusiasts с подтверждаемым опытом;
- участие бесплатное;
- дорогу и проживание участники оплачивают самостоятельно.

---

## 23. Источники

Основные источники, использованные для этого файла:

1. **hackalem.ai** — официальный сайт HackAlem AI.
2. **Официальный Telegram HackAlem (@hackalem)** — свежие правила, расписание, GitHub requirements, check-in, репетиция и operational updates.
3. **HackAlem platform / Astana Hub platform** — регистрация, команда, репозиторий и hackathon flow.
4. **Министерство искусственного интеллекта и цифрового развития РК / gov.kz** — официальная информация о партнёрах, ресурсах, участниках и формате.
5. **The Tech, интервью с представителем Silkroad Innovation Hub** — формат 5 часов, треки, кейсы, критерии и дальнейший Demo Day.
6. **Рабочий контекст нашей команды** — FinTech, состав команды, разделение ролей и правила подготовки, которые мы применяем к себе.

---

# TL;DR FOR CODEX

```text
EVENT: HackAlem AI 2026
DATE: 23 Sep 2026
LOCATION: Astana, International Exhibition Center / EXPO, Mangilik El 53/1
FORMAT: offline agentic-AI hackathon
TEAM: 3 people
OUR TRACK: FinTech
CHECK-IN: 09:00–12:00
OPENING: 12:00–13:00
CODING: 13:00–18:00
BUILD TIME: 5 hours

MANDATORY:
- use Codex during development
- work in the official team GitHub repository
- follow the exact challenge and its rubric
- progress is tracked during the hackathon

DO NOT:
- bring pre-written hackathon project code
- hide development in another repository
- overbuild
- force our old FinTech idea onto a different challenge
- invent evaluation criteria or unavailable APIs

GOAL:
Build the smallest convincing working end-to-end agentic solution
that directly solves the published challenge and survives the demo.

PRIORITY:
challenge compliance
> working vertical slice
> demo reliability
> agentic behavior
> UX clarity
> extra features

OUR PRE-HACKATHON FINTECH IDEAS ARE ONLY A PATTERN LIBRARY:
- Financial Trust Agent / Trust Mesh
- Cross-Border B2B Payment Agent
- AI Financial Investigator / Unit21-like workflow
- Financial Twin / SME finance

When the challenge is published:
READ IT FIRST → EXTRACT RUBRIC → DEFINE ONE DEMO STORY
→ SPLIT WORK BETWEEN 3 PEOPLE → BUILD VERTICAL SLICE → ITERATE.
```

---

# 24. Контекст нашей команды

> Этот раздел дополняет общий контекст HackAlem и описывает именно нашу команду: роли, реальные сильные стороны, ограничения, рабочие договорённости и предварительные технические решения.
>
> Он нужен Codex/Claude/ChatGPT, чтобы AI не давал абстрактные советы "для любой команды", а учитывал, кто именно что делает, как мы работаем и какой результат хотим получить.
>
> Важно: **этот документ — контекст, а не финальный implementation plan.**
>
> Полный пошаговый план на 13:00–18:00 будет разработан отдельно после этого документа. После плана будут подготовлены отдельные stage-specific prompts для каждого участника, а не один большой промпт на всю роль.

## 24.1. Состав команды

В команде 3 человека:

1. **Нурасыл** — team lead / AI agents / agentic architecture / product & FinTech reasoning.
2. **Даулет** — backend.
3. **Аки** — frontend / visual layer / presentation support.

Команда участвует в треке:

# FinTech

Официальный конкретный кейс до начала хакатона неизвестен.

Поэтому команда **не должна заранее проектировать решение под fraud / AML / payments / lending или любой другой конкретный FinTech use case**.

До выдачи кейса мы готовим:

- рабочий процесс;
- архитектурные паттерны;
- универсальный agentic harness;
- prompts/templates;
- правила интеграции;
- командную дисциплину;
- способы review;
- demo/reliability подходы.

Конкретная доменная архитектура выбирается только после получения официального challenge и evaluation criteria.

---

# 25. Роли и ответственность

## 25.1. Нурасыл

Основная роль:

# Team Lead + AI / Agentic System Owner

Нурасыл:

- принимает финальные решения по scope;
- держит целостную картину решения;
- отвечает за AI/agentic architecture;
- отвечает за orchestration;
- проектирует agents;
- проектирует tools;
- проектирует structured outputs;
- определяет HumanGate / approval policy;
- следит за соответствием решения FinTech-смыслу;
- помогает разбирать официальный case;
- следит, чтобы команда не ушла в overengineering;
- следит за временем;
- принимает решения в спорных architectural/integration вопросах;
- может презентовать решение устно;
- обладает самым глубоким FinTech-контекстом в команде.

### Практический опыт Нурасыла

Нурасыл уже построил Oqera — достаточно крупную agentic AI-систему.

Релевантные паттерны и знания, которые можно переносить на HackAlem **как опыт и архитектурное мышление, но не как заранее написанный код**:

- multi-agent orchestration;
- manager / orchestrator → specialists;
- tool calling;
- structured outputs;
- workflows;
- task decomposition;
- persistent state;
- memory;
- HumanGate;
- verification;
- tracing / auditability;
- agent prompts;
- skills/instructions;
- API integrations;
- backend ↔ agent coordination;
- end-to-end AI application architecture;
- работа с coding agents;
- использование AI для генерации и проверки кода.

Нурасыл в основном строит системы **с помощью AI coding tools**, а не вручную пишет весь код.

Это важно учитывать:

> Скорость Нурасыла на HackAlem определяется не скоростью ручного кодинга, а тем, насколько хорошо он может декомпозировать задачу, дать правильный prompt coding agent'у, проверить результат и удержать архитектуру.

### Дополнительная роль

Нурасыл следит за временем и ведёт 25/5 циклы команды.

Он не должен превращаться в человека, который лично исправляет каждый frontend/backend bug.

Иначе AI/agentic core и team-lead функции начнут конкурировать за его время.

---

## 25.2. Даулет

Основная роль:

# Backend Owner + Integration Owner

Предпочтительный стек:

- Python;
- FastAPI.

У Даулета есть общее понимание разработки, но команда не исходит из предположения, что он вручную за 5 часов построит сложный backend без AI.

Как и остальные, он активно использует coding agents.

Основная ответственность:

- FastAPI application;
- routes/endpoints;
- Pydantic schemas;
- business/application logic;
- storage layer;
- integration с agent layer;
- integration с frontend;
- внешние API/tools там, где backend должен выступать adapter;
- error handling;
- startup/run scripts;
- cross-platform compatibility;
- integration fixes.

### Важная дополнительная обязанность

Даулет должен быть главным человеком, который **реализует исправления контрактов между подсистемами**.

Пример:

```text
Frontend ожидает поле:
risk_score

Agent возвращает:
risk

Backend contract определён:
score
```

Нурасыл принимает решение, какой контракт является каноническим.

Даулет приводит backend/integration layer к этому контракту и помогает остальным синхронизироваться.

То есть:

```text
Нурасыл:
решает WHAT / WHY / canonical contract

Даулет:
реализует HOW на integration/backend стороне
```

---

## 25.3. Аки

Основная роль:

# Frontend Owner + Presentation Support

Это первый хакатон Аки.

Она знает frontend немного, но сможет активно использовать:

- Claude Code;
- Codex;
- Figma;
- AI-assisted frontend generation.

Поэтому её работа должна строиться не по принципу:

> "Разберись сама, какой продукт нужен и как должна выглядеть архитектура."

А по принципу:

> "Вот user flow, вот API contract, вот состояния интерфейса, вот визуальные приоритеты — теперь сгенерируй и доведи frontend."

Основные зоны ответственности:

- frontend shell;
- основные screens;
- input flow;
- result states;
- evidence visualization;
- agent/activity visualization;
- approval UI / HumanGate, если нужен;
- error/loading states;
- visual polish;
- screenshots/demo assets;
- presentation support после стабилизации core.

### Presentation

Вероятно, именно Аки будет больше всего заниматься оформлением презентации.

Но презентация не должна отнимать первые часы хакатона.

Presentation work имеет смысл начинать только когда:

- понятна проблема;
- понятен основной flow;
- работает core;
- уже можно сделать screenshots;
- architecture не меняется каждые 15 минут.

---

# 26. Реальный профиль команды

## 26.1. Сильные стороны

Команда не является классической группой, где каждый участник вручную кодит свой модуль.

Правильнее считать её:

# "3 human operators + несколько coding agents"

Основные AI-инструменты:

- Codex — обязательный инструмент HackAlem;
- ChatGPT Pro;
- Claude Code;
- Figma.

По информации команды, на HackAlem ожидается:

- ChatGPT Pro 5x;
- OpenAI API credits порядка $50 для команды/участника — фактическое выделение проверить в день хакатона;
- официальный GitHub repository.

Это означает, что основной multiplier команды — качественное управление AI:

- правильная декомпозиция;
- хороший контекст;
- строгие contracts;
- параллельные задачи;
- быстрый review;
- регулярное слияние;
- минимизация конфликтов.

---

## 26.2. Слабые стороны и риски

### Риск 1 — никто не является сильным manual frontend/backend engineer

Frontend и backend реально можно построить благодаря AI.

Но AI также способен:

- придумать несовместимые schemas;
- создать лишние abstraction layers;
- менять stack;
- дублировать business logic;
- генерировать разные API conventions;
- усложнять architecture.

Поэтому главная проблема команды — **не отсутствие скорости кодинга**, а coordination overhead.

---

### Риск 2 — параллельная Git-работа

У команды нет большого опыта одновременной работы втроём через:

- branches;
- PR;
- merge;
- conflict resolution;
- shared API schemas;
- disciplined integration.

При этом HackAlem требует работу в одном официальном GitHub repository, и прогресс отслеживается.

Поэтому Git workflow должен быть максимально простым.

Не строить тяжёлый enterprise PR-process.

---

### Риск 3 — overengineering

Команда выбрала aggressive risk profile:

# C — хотим технически и визуально амбициозное решение

Цель:

# выиграть HackAlem

Нурасыл особенно заинтересован в:

- agentic architecture;
- multi-agent;
- orchestration;
- advanced AI flows.

Это может стать преимуществом, но также это главный риск.

Важно:

> Multi-agent architecture не должна использоваться ради самого слова "multi-agent".

Критерии конкретного кейса заранее неизвестны.

Нельзя предполагать, что количество агентов автоматически даёт дополнительные баллы.

Agent count — не KPI.

---

### Риск 4 — integration too late

Самый плохой сценарий:

```text
Нурасыл 2 часа строит agent system отдельно.

Даулет 2 часа строит backend отдельно.

Аки 2 часа строит красивый frontend отдельно.

После этого команда впервые пытается соединить всё вместе.
```

Так работать нельзя.

Главный принцип:

# One vertical system, built in parallel.

---

# 27. Решения по командному управлению

## 27.1. Decision maker

Финальный decision-maker:

# Нурасыл

Это необходимо из-за 5-часового ограничения.

Команда может обсуждать решения, но если спор затягивается:

- Нурасыл выбирает направление;
- решение фиксируется;
- команда продолжает работу.

Не требуется полный consensus по каждому техническому вопросу.

---

## 27.2. Architecture owner

Architecture owner:

# Нурасыл

Но это не означает, что он реализует все architecture changes самостоятельно.

Разделение:

```text
Architecture decision → Нурасыл

Backend/integration implementation → Даулет

Frontend implementation → Аки

Agent implementation → Нурасыл
```

---

## 27.3. Time owner

Time owner:

# Нурасыл

Он контролирует:

- текущий цикл;
- remaining time;
- feature freeze;
- scope cuts;
- переход от development к reliability/demo.

---

## 27.4. Pitch

Нурасыл способен презентовать решение устно.

Аки, вероятно, будет отвечать за подготовку/оформление presentation materials.

Финальное распределение "кто говорит на Demo Day" пока не зафиксировано и будет зависеть от case и формата.

---

# 28. Рабочий ритм: 25/5

Команда решила использовать циклы:

# 25 минут работа + 5 минут sync / review / отдых

Причина:

- разработка идёт очень быстро через AI;
- каждые 25 минут части системы могут разойтись;
- официальный progress проверяется примерно каждый час;
- каждые 30 минут нужен integration checkpoint.

Структура одного цикла:

```text
00:00–00:25
Focused work

00:25–00:27
AI review / compatibility check

00:27–00:30
Human sync
```

На human sync обсуждается только:

1. Что реально работает?
2. Что сломано?
3. Кто кого блокирует?
4. Что изменилось в contract?
5. Что нужно исправить прямо сейчас?
6. Что каждый делает следующие 25 минут?
7. Что режем, если не успеваем?

Не проводить длинные brainstorm-сессии после старта разработки.

---

# 29. Использование AI reviewers

Команда хочет, чтобы каждые 25 минут coding agents проверяли совместимость системы и выдавали конкретный report.

Это хорошая идея.

Review должен проверять не "красоту кода вообще", а integration risks.

## AI review для agent layer

Проверить:

- agent input schema;
- agent output schema;
- tool signatures;
- tool return types;
- exception behavior;
- timeout behavior;
- backend integration;
- structured outputs;
- approval states;
- evidence fields.

---

## AI review для backend

Проверить:

- routes;
- request schemas;
- response schemas;
- frontend expectations;
- agent expectations;
- validation;
- error codes;
- serialization;
- env dependencies;
- startup;
- cross-platform issues.

---

## AI review для frontend

Проверить:

- actual endpoint;
- request body;
- expected response;
- optional/missing fields;
- loading state;
- error state;
- empty state;
- HumanGate state;
- result rendering.

---

## Integration reviewer

Раз в цикл или минимум раз в два цикла один AI получает context всего repository и отвечает примерно в формате:

```text
CRITICAL
- ...

CONTRACT MISMATCHES
- ...

BROKEN FLOWS
- ...

FIX NOW
1. ...
2. ...

CAN WAIT
- ...
```

Не нужны длинные essays.

Нужен actionable report.

---

# 30. Первые 30 минут хакатона

Хакатон:

- coding/building: 13:00–18:00;
- общий лимит: 5 часов.

Официальный case станет известен только во время хакатона.

Поэтому команда сознательно резервирует первые:

# 30 минут

на разбор кейса.

Это не "потерянные 30 минут".

Это защитный механизм против создания неправильного продукта.

## Результат первых 30 минут должен быть конкретным

К 13:30 команда должна зафиксировать:

### Challenge

Что буквально требуется.

### Target user

Кто пользователь.

### Problem

Какую конкретную боль решаем.

### Mandatory requirements

Что обязательно должно присутствовать.

### Evaluation criteria

За что реально оценивают.

### Constraints

Что запрещено / ограничено.

### Demo story

Одно предложение:

```text
User does X
→ system performs Y
→ returns Z
→ high-risk action requests approval if necessary.
```

### Architecture

Только необходимая.

### Agent roles

Только нужные.

### Tools

Какие реально нужны.

### API contract

Что frontend/backend/agent отправляют друг другу.

### Definition of Done

Что должно работать, чтобы решение уже можно было показывать.

---

# 31. Предварительная архитектурная гипотеза

Это НЕ финальная architecture.

Это default starting point, который должен быть подтверждён или изменён после получения официального case.

## Frontend

Предварительно:

- React;
- Vite;
- Tailwind.

Причины:

- быстро;
- минимум ceremony;
- много AI-generated examples;
- удобно для Codex/Claude;
- хороший fit для demo UI.

Если case или шаблон репозитория диктует другой frontend stack, следовать repository/case.

---

## Backend

Предварительно:

# Python + FastAPI

Это соответствует предпочтению Даулета.

Использовать:

- FastAPI;
- Pydantic;
- simple service layer;
- minimal dependencies.

Не создавать сложную enterprise architecture.

---

## Agent layer

Предварительная гипотеза:

# OpenAI Agents SDK

Почему это выглядит подходящим:

- hackathon связан с OpenAI;
- Codex обязателен;
- есть OpenAI API resources;
- нужны agents/tools;
- есть handoff-style orchestration;
- есть tracing;
- меньше custom plumbing, чем у более тяжёлых orchestration frameworks.

Но:

> Agents SDK — default hypothesis, а не религия.

Если case требует другого execution model, stack можно изменить.

---

## State / Database

Предварительный default:

# SQLite

Почему:

- встроен в Python;
- нет отдельного DB server;
- Mac/Windows;
- достаточно для 5-hour prototype;
- можно хранить runs/evidence/decisions;
- легко bootstrap.

Не использовать PostgreSQL просто потому, что он "production-grade".

PostgreSQL нужен только если case действительно получает от этого пользу.

---

## Repository

Официальный repository:

# один GitHub repo

Возможная структура:

```text
/
├── frontend/
├── backend/
├── agents/
├── shared/
├── docs/
└── README.md
```

Это лишь шаблон.

Не создавать лишние packages, если repository template уже имеет структуру.

---

# 32. Почему нужен API contract

Перед параллельной реализацией frontend/backend/agent команда должна договориться о минимальном contract.

Это не означает длинную OpenAPI-спецификацию.

Достаточно определить:

```text
request
response
error
status
approval state
evidence schema
```

Пример только для объяснения:

```json
POST /api/analyze

{
  "case_id": "case_123"
}
```

Ответ:

```json
{
  "status": "review_required",
  "summary": "...",
  "score": 82,
  "evidence": [],
  "recommended_action": "...",
  "requires_approval": true
}
```

После фиксации contract:

```text
Аки
может делать frontend на mock JSON

Даулет
может реализовать endpoint

Нурасыл
может заставить agent выдавать нужную schema
```

Таким образом три направления работают параллельно.

---

# 33. Универсальный agentic pattern

До получения кейса не создаём `FraudAgent`, `AMLAgent`, `LoanAgent`.

Готовим только универсальный pattern.

Базовая форма:

```text
                USER
                  │
                  ▼
            ORCHESTRATOR
                  │
          ┌───────┴───────┐
          ▼               ▼
     SPECIALIST A     SPECIALIST B
          │               │
          ▼               ▼
        TOOLS           TOOLS
          └───────┬───────┘
                  ▼
               VERIFIER
                  │
            policy / risk
             /          \
           low          high
           │              │
           ▼              ▼
        ACTION        HUMAN GATE
           │              │
           └──────┬───────┘
                  ▼
                RESULT
```

Default ограничение:

- 1 orchestrator;
- 1–2 specialists;
- optional verifier;
- optional HumanGate.

Не начинать с 8–10 агентов.

---

# 34. Multi-agent policy

Команда заинтересована в multi-agent решении.

Это допустимо и потенциально может дать сильный demo.

Но правило:

# Multi-agent by usefulness, not by decoration.

Нужно уметь ответить:

- почему эти роли разделены;
- почему одному agent хуже;
- какие tools принадлежат каждой роли;
- как они координируются;
- что verifier реально проверяет.

Плохой аргумент:

> "У нас 7 агентов, поэтому система сложная."

Хороший аргумент:

> "Investigator собирает evidence, Policy Agent применяет формальные ограничения, а Verifier проверяет, что итоговое действие подкреплено evidence и не нарушает policy."

---

# 35. Human-in-the-loop policy

Команда уже зафиксировала принцип.

## Low-risk action

Если действие:

- обратимо;
- не несёт высокой ответственности;
- не создаёт существенных финансовых/юридических последствий;

agent может выполнить действие автоматически.

## High-risk action

Если действие:

- блокирует деньги;
- отклоняет клиента;
- инициирует существенную транзакцию;
- создаёт финансовое обязательство;
- несёт regulatory/compliance последствия;
- трудно обратимо;

нужен:

# HumanGate / approval

Общий принцип:

```text
AI can investigate
AI can recommend
AI can prepare
AI can execute low-risk action

High-impact action → human approval
```

Конкретная policy должна зависеть от официального кейса.

---

# 36. Explainability и auditability

Команда предпочитает вариант:

```text
не просто:
Risk = 87%

а:
Risk = 87%
+ evidence
+ executed checks
+ tool results
+ recommended action
+ approval requirement
```

Это особенно важно для FinTech.

При этом:

# НЕ показывать скрытый chain-of-thought модели.

Показывать operational trace / audit trail.

Например:

```text
✓ Transaction loaded
✓ Customer history checked
✓ Counterparty checked
✓ Policy rules evaluated

Evidence
- New beneficiary
- Amount 3.8x normal range
- First cross-border transfer in 12 months

Decision
Manual review required

Approval
Required
```

Это полезно:

- пользователю;
- жюри;
- auditability;
- explainability;
- demo.

---

# 37. Demo UX ambition

Команда выбрала уровень:

# C — визуальный wow

Желаемый demo может включать:

- polished FinTech dashboard;
- live execution statuses;
- agent/activity timeline;
- evidence cards;
- risk/decision visualization;
- HumanGate;
- animations;
- final result;
- clear audit trail.

Но визуальный слой строится **поверх работающего vertical slice**.

Правило:

```text
Working ugly flow
before
Beautiful broken flow
```

---

# 38. Demo engineering

Команда допускает и считает нормальным использовать:

- seed data;
- prepared demo scenarios;
- mock external integrations;
- deterministic fixtures;
- fallback data;
- replay of previous successful run;
- backup demo path.

Это не должно превращаться в Fake AI.

Если заявлено:

> Agent вызывает transaction API

то либо agent реально вызывает соответствующий tool interface, либо UI/README честно показывает, что внешний financial rail mock/simulated.

Запрещено создавать иллюзию реального банка/API, если его нет.

---

# 39. Internet / infrastructure

Организаторы заявляют, что инфраструктура и интернет были протестированы.

Тем не менее внешние сервисы остаются failure point.

Поэтому команда не должна делать core demo зависимым от 5 внешних API.

Лучше:

- 1 реальная ключевая integration;
- остальные realistic tools/mocks;

чем:

- 5 нестабильных live integrations.

---

# 40. Cross-platform requirement

В команде:

- Нурасыл — MacBook;
- Аки — MacBook;
- Даулет — Windows.

Поэтому solution должен запускаться как минимум на:

- macOS;
- Windows.

Избегать:

- shell-only setup без Windows alternative;
- platform-specific paths;
- hardcoded `/Users/...`;
- assumptions о bash;
- Docker-only dependency, если Docker не проверен у всех.

README должен быть достаточен для запуска на новом устройстве.

---

# 41. Deployment

Deployment пока не выбран.

Default principle:

> Demo не должен зависеть от deployment, если deployment не требуется challenge.

Минимум:

- проект запускается локально;
- README понятный;
- frontend/backend доступны на любом laptop команды;
- demo можно провести с одного устройства.

Deployment можно добавить, если:

- нужен shared URL;
- это важно rubric;
- это сильно улучшает judge experience;
- core уже стабилен.

Не жертвовать работающим core ради Vercel/Railway/Render в последние 30 минут.

---

# 42. Черновой 5-hour macro-flow

Это не финальный подробный plan.

Это только текущая договорённость о временной логике.

## 13:00–13:30

Challenge decomposition / brainstorm.

Цель:

- понять case;
- прочитать rubric;
- выбрать demo story;
- выбрать минимальную architecture;
- выбрать agents;
- определить tools;
- зафиксировать API contract;
- разделить работу.

## После 13:30

Работа идёт 25/5 циклами.

Предварительно:

```text
Cycle 1
vertical slice

Cycle 2
core

Cycle 3
core complete

Cycle 4
agent depth

Cycle 5
UX / wow

Cycle 6
integration / presentation start

Cycle 7
reliability

Cycle 8
feature freeze / demo

Cycle 9
submission / final verification
```

Точный schedule будет разработан отдельно.

---

# 43. Feature-cut policy

Команда готова резать features, если это необходимо.

Это особенно важно после середины хакатона.

Если:

```text
основной flow не работает
+
есть 4 красивых дополнительных агента
```

то дополнительные агенты должны быть удалены/заморожены.

Приоритет:

```text
working core
>
extra agent
>
extra animation
>
extra integration
```

Надежда "что такого не случится" не является strategy.

AI reviewers и 25/5 sync нужны именно для раннего обнаружения таких ситуаций.

---

# 44. Предварительное распределение работы

## Нурасыл

До core stability:

- challenge interpretation;
- architecture;
- agent system;
- tools;
- structured output;
- HumanGate logic;
- FinTech logic;
- quality;
- scope;
- time.

После core stability:

- agent quality;
- prompt tuning;
- judge/rubric review;
- demo story;
- final product reasoning.

---

## Даулет

До core stability:

- backend skeleton;
- schemas;
- API;
- storage;
- agent integration;
- frontend integration.

После core stability:

- integration fixes;
- reliability;
- error handling;
- cross-platform run;
- final startup verification.

---

## Аки

До core stability:

- frontend shell;
- mock data;
- input;
- loading;
- results;
- evidence UI;
- approval UI.

После core stability:

- visual polish;
- activity visualization;
- screenshots;
- architecture diagram support;
- presentation.

---

# 45. Что НЕ решено заранее

Codex и другие AI должны понимать, что следующие решения **открыты** до получения case.

Не считать заранее выбранным:

- конкретный FinTech use case;
- fraud/AML/KYC/payment/lending и т.д.;
- конкретное количество agents;
- необходимость multi-agent;
- конкретные external APIs;
- необходимость RAG;
- необходимость vector DB;
- необходимость PostgreSQL;
- необходимость Redis;
- необходимость deployment;
- конкретная UI information architecture;
- конкретные evaluation metrics;
- точная структура presentation.

Даже OpenAI Agents SDK — пока рабочий default, а не immutable decision.

---

# 46. Что уже можно считать решённым

Можно считать зафиксированным:

- команда из 3 человек;
- FinTech track;
- Нурасыл — lead + AI/agents;
- Даулет — backend;
- Аки — frontend/presentation;
- Python + FastAPI — предпочтение backend;
- один официальный GitHub repo;
- Codex обязателен;
- Claude Code используется дополнительно;
- Figma используется;
- цель — выиграть;
- risk profile — aggressive;
- первые ~30 минут идут на case analysis;
- затем ритм 25/5;
- Нурасыл принимает финальные scope/architecture решения;
- Даулет является главным implementation owner интеграционных исправлений;
- multi-agent можно использовать, если он функционально оправдан;
- high-risk action → HumanGate;
- объяснимость и evidence важны;
- demo engineering допустим;
- старый Oqera code не переносится;
- Oqera patterns/knowledge можно использовать;
- весь code HackAlem создаётся во время разрешённого hackathon window в официальном repository.

---

# 47. Как использовать этот файл с Codex

Перед началом планирования можно дать Codex инструкцию:

```text
Прочитай HACKALEM_TEAM_CONTEXT.md полностью.

Это канонический контекст нашей команды и хакатона.

Не начинай писать код.

Сначала:
1. перечисли ключевые ограничения;
2. перечисли сильные стороны команды;
3. перечисли основные риски;
4. отметь все решения, которые уже зафиксированы;
5. отдельно перечисли решения, которые нельзя принимать до получения официального кейса.

Не предлагай конкретный FinTech продукт, пока официальный case неизвестен.
```

---

# 48. Как использовать этот файл участникам команды

Каждый участник может загрузить этот файл в свой ChatGPT / Claude / Codex session и добавить свою роль.

## Для Нурасыла

Дополнительный контекст:

```text
Я Нурасыл.

Моя роль:
- team lead;
- AI/agent architecture;
- agent implementation;
- FinTech reasoning;
- scope/time decisions.

При ответах учитывай, что я должен избегать ситуации, где лично чиню все backend/frontend проблемы.

Если видишь overengineering — укажи прямо.
```

---

## Для Даулета

Дополнительный контекст:

```text
Я Даулет.

Моя роль:
- backend owner;
- FastAPI;
- Pydantic schemas;
- integrations;
- storage;
- integration fixes;
- cross-platform startup.

Нурасыл принимает architecture/scope decisions.
Я отвечаю за то, чтобы backend, agent layer и frontend реально сходились по контрактам.

Если обнаруживаешь несовместимость, дай мне конкретный patch plan.
```

---

## Для Аки

Дополнительный контекст:

```text
Я Аки.

Моя роль:
- frontend owner;
- UI;
- result/evidence visualization;
- HumanGate UI;
- loading/error states;
- visual polish;
- later presentation support.

Это мой первый хакатон.

Не усложняй frontend architecture без необходимости.
Если backend ещё не готов, используй согласованный mock JSON/API contract и продолжай UI независимо.
```

---

# 49. Следующий этап после этого документа

Этот документ НЕ является финальным execution plan.

Следующий отдельный этап работы:

# FULL HACKATHON EXECUTION PLAN

Он должен описать:

- что происходит до 13:00;
- что делаем в 13:00;
- первые 30 минут;
- каждый 25/5 cycle;
- кто что получает на вход;
- кто что должен выдать;
- какие commits должны появляться;
- когда integration review;
- когда feature freeze;
- когда presentation;
- когда demo rehearsal;
- когда submission;
- что происходит при отставании;
- какие fallback branches существуют.

Только после утверждения этого плана нужно писать prompts.

---

# 50. Как должны быть устроены prompts

Команда НЕ хочет:

```text
один гигантский prompt для Аки
один гигантский prompt для Даулета
один гигантский prompt для Нурасыла
```

Предпочтительная модель:

# stage-specific prompts

Например для frontend:

```text
AKI-01
Read challenge + contract + build frontend skeleton

AKI-02
Connect mock response and render states

AKI-03
Connect real backend

AKI-04
Build evidence / trace UI

AKI-05
Add approval state

AKI-06
Run integration review

AKI-07
Polish final demo

AKI-08
Prepare screenshots / presentation assets
```

Backend аналогично:

```text
DAULET-01
Bootstrap backend

DAULET-02
Define contracts

DAULET-03
Integrate agent layer

DAULET-04
Implement tools/storage

DAULET-05
Integration check

DAULET-06
Reliability/error handling

DAULET-07
Final startup verification
```

AI/agent layer:

```text
NURASYL-01
Analyze challenge

NURASYL-02
Select agent architecture

NURASYL-03
Build first agent vertical slice

NURASYL-04
Add specialists/tools

NURASYL-05
Add verifier/HumanGate

NURASYL-06
Tune structured outputs

NURASYL-07
Judge/rubric review

NURASYL-08
Final agent reliability
```

Это только иллюстрация будущего подхода.

Конкретный prompt catalog должен быть создан **после полного execution plan**.

---

# 51. Требование к AI во время HackAlem

Любой AI assistant, который получает этот файл, должен соблюдать следующий порядок:

```text
OFFICIAL CHALLENGE
        ↓
MANDATORY REQUIREMENTS
        ↓
EVALUATION CRITERIA
        ↓
ONE DEMO STORY
        ↓
MINIMUM WORKING ARCHITECTURE
        ↓
VERTICAL SLICE
        ↓
INTEGRATION
        ↓
AGENT DEPTH
        ↓
POLISH
        ↓
RELIABILITY
        ↓
SUBMISSION
```

Не наоборот.

Нельзя начинать с:

```text
"Давайте сделаем 8 агентов, graph DB, blockchain, vector search..."
```

пока не доказано, что это помогает case.

---

# 52. Canonical summary for AI assistants

```text
We are a 3-person FinTech HackAlem team.

Hackathon:
- 23 Sep 2026
- Astana
- 13:00–18:00
- 5 hours
- official case revealed during event
- official GitHub repo
- Codex required
- progress monitored

Team:
- Nurassyl: team lead + AI/agents + architecture + FinTech reasoning
- Daulet: backend, Python/FastAPI, integration owner
- Aki: frontend + UI + presentation support, first hackathon

How we build:
- heavy use of Codex / Claude Code / ChatGPT / Figma
- humans manage architecture, scope, quality, integration
- code is built during the hackathon
- no reuse of Oqera code
- Oqera architectural knowledge/patterns are allowed as experience

Goal:
- win

Risk profile:
- aggressive / ambitious
- willing to use multi-agent and polished UI
- but working end-to-end flow has priority

Workflow:
- first ~30 min: challenge/rubric decomposition
- then 25 min work + 5 min AI review/human sync
- one canonical API contract
- vertical slice first
- integration continuously
- feature freeze before end

Default technical hypothesis:
- React + Vite + Tailwind
- FastAPI + Pydantic
- OpenAI Agents SDK
- SQLite
- one monorepo

These are defaults, not immutable decisions.

Agent pattern:
- orchestrator
- 1–2 specialists
- optional verifier
- HumanGate for high-risk actions
- tools
- structured output
- evidence/audit trail

Do not expose hidden chain-of-thought.
Show operational trace/evidence instead.

Do not assume:
- exact FinTech use case
- exact rubric
- exact APIs
- exact agent count
- need for Postgres/RAG/vector DB/deployment

Next planning step:
Create a complete 5-hour execution plan.
Only after that, create multiple stage-specific prompts
for Nurassyl, Daulet and Aki.
```

---

# 53. Главный принцип команды

Если в любой момент возникает выбор между:

```text
более сложной AI architecture
```

и

```text
понятным, работающим, убедительным end-to-end demo
```

по умолчанию выбирать:

# работающий убедительный demo

Но если core стабилен, команда сознательно готова использовать оставшееся время для:

- multi-agent depth;
- better reasoning;
- evidence;
- HumanGate;
- agent visualization;
- polished FinTech UX;
- сильного wow-effect.

Это и есть текущая стратегия команды.
