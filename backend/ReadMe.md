# Backend — AI Sales Assistant

FastAPI-приложение: принимает сообщение клиента, ищет релевантные факты
в pgvector, генерирует ответ через LLM. Защищено от галлюцинаций и
prompt injection.

## Поток запроса

```
POST /api/v1/chat
        │
        ▼
service.process_message(message)
        │
        ├── [Слой 1] guard: _is_injection / _asks_discount
        │       └── если сработал → ChatResponse без LLM
        │
        ├── [Слой 2] retrieval: embedding → pgvector cosine
        │       └── фильтр sim >= SIMILARITY_THRESHOLD (0.25)
        │
        ├── [Слой 3] если relevant пуст → fallback без LLM
        │
        ▼
llm_client.complete_structured → ChatResponse
```

## Защита от галлюцинаций — три слоя

1. **Guard на инъекции/скидки** (`_INJECTION_PATTERNS`, `_DISCOUNT_PATTERNS`).
   Срабатывает **до** retrieval и LLM. Regex-маркеры: «забудь», «игнорируй»,
   «дай скидку», «промокод», «ты теперь», «system prompt» и т.п.
   На попытку со скидкой → `NO_DISCOUNT_REPLY`.
   На прочую инъекцию → `FALLBACK_REPLY`.

2. **Порог similarity** (`SIMILARITY_THRESHOLD = 0.25`). Если ни один чанк
   не прошёл порог — fallback без LLM. Порог подобран эмпирически под
   `paraphrase-multilingual-MiniLM-L12-v2` на русских коротких фразах:
   - релевантные вопросы дают 0.3–0.55,
   - «погода в Москве» — 0.22 (отсекается).

3. **Системный промпт** (`SYSTEM_PROMPT` в `service.py`).
   Правила: только факты из контекста, никаких выдумок, «статус заказа
   уточню у менеджера», «скидок нет ни при каких условиях», уточнение
   про брак при возврате.

## База знаний

Таблица `knowledge_documents`:

| Поле | Тип | Назначение |
|---|---|---|
| id | int | PK |
| name | varchar(255) | название факта |
| category | varchar(255) | product / delivery / refund / defect / policy |
| topic | varchar(64) | машинный ключ (delivery_courier и т.п.) |
| description | text | текст факта |
| recommended_with | json | список связанных продуктов (сейчас везде `[]`) |
| embedding | vector(384) | эмбеддинг `name + ". " + description` |

Сид — в миграции `1702bfee913d_init.py`. При `alembic upgrade head`
создаётся схема, включается `CREATE EXTENSION vector`, вставляются 6 фактов.

## Как обновить регламент

1. Отредактировать список `KNOWLEDGE` в `1702bfee913d_init.py`.
2. Пересоздать БД:
   ```bash
   alembic -c backend/alembic.ini downgrade base
   alembic -c backend/alembic.ini upgrade head
   ```
3. Пересчитать эмбеддинги:
   ```bash
   python -m backend.scripts.generate_embeddings
   ```

Скрипт считает только те строки, где `embedding IS NULL`, — идемпотентен.

## Alembic

Из-за раскладки `backend/alembic.ini` + пакет `backend/` в корне — запускать
**из корня проекта** с явным `-c`:

```bash
cd ~/work/repository/AI-bot
alembic -c backend/alembic.ini current
alembic -c backend/alembic.ini upgrade head
```

В `backend/alembic.ini` прописан абсолютный `prepend_sys_path` — иначе
Alembic не находит пакет `backend`.

## Модели и эмбеддинги

- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, 384 измерения.
- Скачивается автоматически при первом запуске (~470 МБ) в `~/.cache/huggingface/`.
- Синглтон `embedding_client` в `core/embedding.py` — модель грузится один раз
  на процесс.

## LLM

`core/llm.py` — тонкая обёртка над `openai.AsyncOpenAI`. Работает с любым
OpenAI-совместимым endpoint (OpenAI, OpenRouter, локальный Ollama, etc.)
через `LLM_BASE_URL` в `.env`.

Ответ парсится как JSON в `ChatResponse`. Если LLM вернул plain-text
(`customer_reply: ...\nmanager_hint: ...`) — есть fallback-парсер.

## Тесты

```bash
python -m pytest backend/tests/ -v
```

- `test_guards.py` — 4 unit-теста, без БД/LLM/модели (всё замокано):
  - инъекция + скидка → `NO_DISCOUNT_REPLY`, LLM не вызван, эмбеддинг не считался,
  - инъекция без скидки → `FALLBACK_REPLY`, LLM не вызван,
  - нерелевантный вопрос (retrieval пуст) → `FALLBACK_REPLY`, LLM не вызван,
  - релевантный вопрос → LLM вызван, контекст содержит вопрос и факт.
- `test_llm.py` — парсинг JSON и plain-text, обработка ValidationError.

## Ручные скрипты

Не собираются pytest-ом (префикс `manual_`):

```bash

python -m backend.tests.manual_semantic_search


python -m backend.tests.manual_crash_test
```