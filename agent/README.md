# Investigator boundary

Текущий статус: четыре read-only tools, общий snapshot service и HTTP route работают. `openai_model.py` подключает официальный OpenAI Responses SDK к существующему ограниченному loop. Реальный сетевой smoke требует `OPENAI_API_KEY` и пока не выполнен. Аналитическому CLI ключ не нужен.

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
$env:OPENAI_API_KEY = '<ключ только в локальном окружении>'
$env:OPENAI_MODEL = 'gpt-6-luna' # необязательно, значение по умолчанию
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Не записывайте ключ в репозиторий или командный лог. Без ключа `/api/investigate` возвращает `status=unavailable`, а остальные routes и аналитический CLI работают. Ошибка/таймаут модели возвращаются в существующей форме `InvestigationResponse`. Общий deadline — 30 секунд, максимум 6 tool calls.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s integration -p 'test_*.py' -v
.\.venv\Scripts\python.exe -m agent.live_smoke --scenario all
```

Последняя команда делает настоящие model requests через существующий API над рассчитанным snapshot и требует ключа. Она проверяет tool activity, точные gid и evidence против snapshot. Проверка ссылок сама по себе не доказывает смысл произвольного текста модели; numerical facts следует показывать из возвращённых `Evidence` objects.
