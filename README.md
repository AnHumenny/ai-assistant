# AI Sales Assistant

Небольшой AI-ассистент интернет-магазина. Отвечает на типовые вопросы
клиентов (товар, доставка, возврат, брак, скидки) по регламенту
из базы знаний.

Стек: FastAPI + PostgreSQL + pgvector + React. Эмбеддинги — локальная
модель `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
(384 измерения). LLM — любой OpenAI-совместимый endpoint.

## Что умеет

- Отвечает на вопросы по регламенту (6 фактов в базе знаний).
- Ищет релевантные факты через pgvector (cosine similarity, порог 0.25).
- Возвращает два поля: `customer_reply` (клиенту) и `manager_hint` (менеджеру).
- Защищён от галлюцинаций: если факта в базе нет — fallback
  «Уточню у менеджера, он свяжется с вами», LLM не вызывается.
- Защищён от prompt injection и попыток получить скидку: guard срабатывает
  до retrieval и до LLM.

## Демо

[![Демо AI Sales Assistant](https://img.youtube.com/vi/_S01g3BYyX0/maxresdefault.jpg)](https://youtu.be/_S01g3BYyX0) 

## Структура

```
.
|-- backend
|   |-- alembic
|   |   |-- env.py
|   |   |-- README
|   |   |-- script.py.mako
|   |   `-- versions
|   |       `-- 1702bfee913d_init.py
|   |-- alembic.ini
|   |-- app
|   |   |-- core
|   |   |   |-- config.py
|   |   |   |-- db
|   |   |   |-- embedding.py
|   |   |   |-- __init__.py
|   |   |   `-- llm.py
|   |   |-- __init__.py
|   |   |-- main.py
|   |   `-- modules
|   |       |-- assistant
|   |       `-- __init__.py
|   |-- ReadMe.md
|   |-- requirements.txt
|   |-- scripts
|   |   `-- generate_embeddings.py
|   `-- tests
|       |-- manual_crash_test.py
|       |-- manual_semantic_search.py
|       `-- test_guards.py
|-- frontend
|   |-- env_example
|   |-- eslint.config.js
|   |-- index.html
|   |-- package.json
|   |-- package-lock.json
|   |-- public
|   |   |-- favicon.svg
|   |   `-- icons.svg
|   |-- ReadMe.md
|   |-- README.md
|   |-- src
|   |   |-- App.css
|   |   |-- App.jsx
|   |   |-- assets
|   |   |   |-- hero.png
|   |   |   |-- react.svg
|   |   |   `-- vite.svg
|   |   |-- index.css
|   |   `-- main.jsx
|   `-- vite.config.js
`-- README.md
```

## Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

Заполнить `.env` в корне:

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname
LLM_API_KEY=sk-...
LLM_MODEL=модель
# LLM_BASE_URL=https://openrouter.ai/api/v1   # опционально
```

Накатить миграции (создаст схему, включит pgvector, засеет 6 фактов):

```bash
alembic -c backend/alembic.ini upgrade head
```

Посчитать эмбеддинги (один раз, при первом запуске скачает модель ~470 МБ):

```bash
python -m backend.scripts.generate_embeddings
```

Запустить API:

```bash
uvicorn backend.app.main:app --reload
```

- API: `http://127.0.0.1:8000`
- Health: `GET /api/v1/health`
- Chat: `POST /api/v1/chat`

## Frontend

```bash
cd frontend
npm install
npm run dev
```

- UI: `http://localhost:5173`

## API

### `POST /api/v1/chat`

Request:

```json
{ "message": "доставка заказа 1842" }
```

Response:

```json
{
  "customer_reply": "Статус конкретного заказа уточню у менеджера. Доставка курьером на следующий день, слот с 18:00 до 21:00.",
  "manager_hint": "Уточнить статус и детали доставки заказа 1842."
}
```

## Краш-тест

```bash
python -m backend.tests.manual_crash_test
```

## Тесты

```bash
python -m pytest backend/tests/ -v
```

- `test_guards.py` - guard на инъекции/скидки, fallback, вызов LLM (моки, без БД).
- `test_llm.py` - парсинг JSON и plain-text ответов LLM.
- `manual_*.py` - ручные скрипты (pytest их не собирает).

## База знаний

6 фактов регламента лежат в миграции `backend/alembic/versions/1702bfee913d_init.py`
и засеиваются при `alembic upgrade head`. Изменить регламент → отредактировать
список в миграции → пересоздать БД → пересчитать эмбеддинги. Подробнее —
в `backend/README.md`.