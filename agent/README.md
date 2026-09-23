# Investigator boundary

Текущий статус: четыре read-only tools, общий snapshot service и HTTP route работают. `openai_model.py` подключает официальный OpenAI Responses SDK к существующему ограниченному loop. Реальный сетевой smoke ranking и node profile пройден с `gpt-5.6-luna` (подробности ниже). Аналитическому CLI ключ не нужен.

## Что уже работает

- `boundary.py`: четыре async операции в формах `docs/API_CONTRACT.md`, общие пределы и точные строковые gid.
- `session.py`: проверка входного вопроса и tool arguments, максимум шесть последовательных попыток, общий 30-секундный deadline, сверка `meta/snapshot_id`, проверка ограниченных ответов и реальный `ToolCall` trace.
- `evidence.py`: из доверенного `CommonRecipientsResponse` получает существующий transport `Evidence` shape для получателя и каждого пути от выбранного gid. Факты явно содержат `path_not_money_provenance` и `date_only`. Они говорят о структурной достижимости, а не о происхождении или хронологической передаче средств.
- `validation.py`: сверяет каждый возвращённый fact с фактическим tool output, ссылки, известные gid, snapshot и обязательные limitations. Числа в свободном `Finding.text` не принимаются.
- `harness.py`: один loop с инъекцией model adapter. Он проверяет каждый citation по фактически выполненным tool calls и snapshot, отбрасывает неподтверждённые числа, обвинения и утверждения о вероятности преступления. При timeout, отсутствии модели или ошибке возвращает честный status без findings/evidence.
- `openai_model.py`: stateless adapter к Responses API. Модель выбирает один из четырёх tools, затем получает ограниченный tool result и пишет краткие findings с evidence IDs. Для ranking и subgraph adapter дополнительно читает профиль через тот же `ToolSession`, чтобы вывод можно было подкрепить числовыми facts.
- `fixture_provider.py`: ограниченные синтетические примеры для проверок. Не выдаёт fixture за live и не подставляет чужую карточку для отсутствующего gid.

## Проверка

Из корня репозитория:

```powershell
python -m unittest discover -s agent -p 'test_*.py' -v
```

Проверены успешный профиль, общий получатель и пустое пересечение, неизвестный gid, неверная ссылка/значение fact, устаревший snapshot, depth=4, шесть вызовов, timeout, ошибка модели, отсутствие модели и отбрасывание неподтверждённой фразы. Unit tests не требуют API key. Интеграционные тесты используют реальные Parquet и подменяют только внешний provider boundary.

## Настройка и настоящий smoke

Из корня репозитория после расчёта `pipeline/out/snapshot.json`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
# OPENAI_API_KEY заранее установлен человеком в локальном окружении backend.
$env:OPENAI_MODEL = 'gpt-5.6-luna' # необязательно, значение по умолчанию
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Не записывайте ключ в репозиторий или командный лог. Без ключа `/api/investigate` возвращает `status=unavailable`, а остальные routes и аналитический CLI работают. Ошибка/таймаут модели возвращаются в существующей форме `InvestigationResponse`. Общий deadline — 30 секунд, максимум 6 tool calls.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s integration -p 'test_*.py' -v
.\.venv\Scripts\python.exe -m agent.live_smoke --scenario all
```

Последняя команда делает настоящие model requests через существующий API над рассчитанным snapshot и требует ключа. Она проверяет tool activity, точные gid и evidence против snapshot. Проверка ссылок сама по себе не доказывает смысл произвольного текста модели; numerical facts следует показывать из возвращённых `Evidence` objects.

### Проверенный live gate — 23 сентября 2026

`python -m agent.live_smoke --scenario all` завершился с PASS на `gpt-5.6-luna`, snapshot `ffc9f16fa9385251100f6cf1`. Вызовы настоящего OpenAI Responses API выполнены без mocks.

- Ranking: модель выбрала `rank_entities`; adapter затем выполнил три `get_entity_profile` через существующий ToolSession. Получены три findings и десять facts из snapshot.
- Node profile: модель выбрала `get_entity_profile` для точного строкового gid; получены два findings и девять facts из snapshot.
- Проверены точные gid, существование evidence и полное совпадение числовых facts. Текст просмотрен отдельно: priority описан как очередь проверки, роль отделена от priority, достижимость направлена от seed к узлу, происхождение средств не утверждается. В финальном прогоне выдуманных сущностей или фактов не обнаружено.
- `all` включает только ranking и node profile. Graph/common recipients не проверялись с live provider; их существующие интеграционные проверки используют подмену внешней модели.
- После финального live smoke повторены целевые наборы: `unittest discover -s agent -p "test_*.py" -v` — 31/31 PASS; `unittest discover -s integration -p "test_*.py" -v` — 7/7 PASS.

Ранние live прогоны выявили смену event loop между запросами TestClient, смешение роли с причинами priority, неоднозначное направление seed reach и сокращённые моделью evidence IDs. Исправления ограничены контекстом TestClient, уточнениями prompt и enum точных evidence IDs в существующем structured output провайдера. Backend по-прежнему проверяет facts; Transport Contract v1, tools и расчёты не менялись. Это smoke двух сценариев, не гарантия корректности любого свободного текста.
