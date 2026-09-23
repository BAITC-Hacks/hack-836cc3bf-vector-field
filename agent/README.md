# Investigator boundary

Текущий статус: контур read-only tools и один ограниченный model-agnostic loop проверены **на синтетических fixtures**. Живой сервис по исходным Parquet, реальная модель и HTTP route ещё не подключены. Этот пакет не нужен для запуска аналитического CLI.

## Что уже работает

- `boundary.py`: четыре async операции в формах `docs/API_CONTRACT.md`, общие пределы и точные строковые gid.
- `session.py`: проверка входного вопроса и tool arguments, максимум шесть последовательных попыток, общий 30-секундный deadline, сверка `meta/snapshot_id`, проверка ограниченных ответов и реальный `ToolCall` trace.
- `evidence.py`: из доверенного `CommonRecipientsResponse` получает существующий transport `Evidence` shape для получателя и каждого пути от выбранного gid. Факты явно содержат `path_not_money_provenance` и `date_only`. Они говорят о структурной достижимости, а не о происхождении или хронологической передаче средств.
- `validation.py`: сверяет каждый возвращённый fact с фактическим tool output, ссылки, известные gid, snapshot и обязательные limitations. Числа в свободном `Finding.text` не принимаются.
- `harness.py`: один loop с инъекцией model adapter. Он отдаёт модели только ограниченные результаты вызовов вместе с доверенными `Evidence` для цитирования, заменяет текст findings осторожными шаблонами, пропускает next checks только из доверенных профилей или шаблона для пути; timeout, отсутствие модели и ошибки возвращают честный status без findings/evidence.
- `fixture_provider.py`: ограниченные синтетические примеры для проверок. Не выдаёт fixture за live и не подставляет чужую карточку для отсутствующего gid.

## Проверка

Из корня репозитория:

```powershell
python -m unittest discover -s agent -p 'test_*.py' -v
```

Проверены успешный профиль, общий получатель и пустое пересечение, неизвестный gid, неверная ссылка/значение fact, устаревший snapshot, depth=4, шесть вызовов, timeout, ошибка модели, отсутствие модели и отбрасывание неподтверждённой фразы. Тесты не требуют API key или сторонних Python-зависимостей.

## Подключение live backend

Backend должен передать в `investigate(request, tools, model, meta=..., known_gids=...)` provider, который реализует `InvestigatorTools` поверх **тех же in-process service-функций и snapshot**, что API. Нельзя выполнять HTTP-запросы к собственному серверу, пересчитывать роли или читать Parquet отдельно в агенте. `meta.snapshot_id` связан с hashes входных данных и config, `known_gids` — полный набор текущего snapshot.

Перед подключением модели live provider должен предоставить:

1. Полные `EntityResponse` с ролью, priority и структурированным evidence, включая шесть `priority_component_*`.
2. `SubgraphResponse` и `EntityListResponse` по контракту, с лимитами и точными string gid.
3. `CommonRecipientsResponse` с реально существующими направленными рёбрами, кратчайшими путями-свидетельствами и детерминированным tie-breaking. `agent/evidence.py` проверяет форму ответа, но не может проверить граф без snapshot service.
4. Текущий `meta`, набор gid и независимость core routes/CSV от доступности модели.

`InvestigatorModel` пока является Protocol. Реальный SDK adapter подключать после Core Green; он должен выдавать `ToolAction` или `FinalAction`, без нового orchestration слоя. Ошибки валидации не превращаются в `completed`. Проверка ссылок не доказывает смысл произвольного текста, поэтому итоговый текст формируется из контролируемых шаблонов, а числовые значения должны отображаться из facts.
