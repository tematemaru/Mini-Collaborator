# Mini Collaborator

A small HTTP service that receives callbacks from third-party systems and stores everything they send, so you can inspect exactly what arrived: headers, query string, body, client IP, method and timestamp.

Give a client a token, hand it the callback URL that belongs to that token, and every request it sends to that URL is recorded and grouped under the token.

## Features

- **Token issuing** — `GET /generate` returns a UUID4 token together with a ready-to-use callback URL
- **Callback capture** — `GET`/`POST`/`PUT`/`DELETE`/`PATCH` on `/c/{token}` are all recorded, including headers, query parameters and raw body
- **Log inspection** — read the full journal for a token, newest first
- **Statistics** — total count, unique client IPs, per-method breakdown, time range and a short recent list
- **Automatic cleanup** — a background task deletes records older than a configurable age

> Русский: сервис принимает коллбэки от внешних систем по токену и сохраняет всё, что они прислали, — заголовки, query, тело, IP, метод и время. Выдаёте клиенту токен, отдаёте ему ссылку для коллбэка, всё пришедшее собирается под этим токеном.

## Quick Start

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows

```bat
python -m venv venv
venv\Scripts\activate
```

### Both platforms

```bash
pip install -r requirements.txt
cp .env.sample .env
python run.py
```

The service listens on `http://<HOST>:<PORT>` — `0.0.0.0:8000` by default. Check that it is up:

```bash
curl http://127.0.0.1:8000/
```

> Русский: создайте виртуальное окружение, активируйте его, установите зависимости, скопируйте `.env.sample` в `.env` и запустите сервис. Проверка готовности — запрос `curl http://127.0.0.1:8000/`. Перед первым использованием задайте в `.env` реальный `LOCAL_IP`, иначе в выданных ссылках будет `127.0.0.1` и внешние клиенты до вас не дотянутся.

## Docker

```bash
docker build -t mini-collaborator .
docker run -p 8000:8000 --env-file .env mini-collaborator
```

The image is built from `Dockerfile` (`python:3.10-slim`), exposes port `8000` and starts `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

Because the database is a SQLite file (`callbacks.db`) kept inside the container, its data is lost when the container is removed. Mount a host directory to keep it:

```bash
docker run -p 8000:8000 --env-file .env -v "$(pwd)/data:/app/data" \
  -e DATABASE_URL=sqlite:////app/data/callbacks.db mini-collaborator
```

> Русский: сборка образа и запуск контейнера с пробросом порта 8000 и передачей `.env`. Учтите, что SQLite-база лежит внутри контейнера и удаляется вместе с ним — монтируйте директорию и переопределяйте `DATABASE_URL`, если коллбэки должны переживать пересоздание контейнера.

## Environment Variables

Copy `.env.sample` to `.env` and adjust. Values are read from the process environment (a `.env` file is loaded on startup) and every variable has a default, so the service starts with an empty `.env`.

| Variable | Type | Default | Meaning |
|---|---|---|---|
| `HOST` | string | `0.0.0.0` | Address uvicorn binds to |
| `PORT` | int | `8000` | Port uvicorn listens on |
| `LOCAL_IP` | string | `127.0.0.1` | IP substituted into `callback_url` and `server_ip` |
| `DATABASE_URL` | string | `sqlite:///callbacks.db` | SQLAlchemy connection URL |
| `CLEANUP_HOURS` | int | `24` | Maximum record age in hours; older records are deleted |
| `CLEANUP_INTERVAL` | int | `3600` | Seconds between cleanup passes |
| `DEBUG` | bool | `False` | `true` enables auto-reload, debug logging and SQL echo |

Notes:

- If a variable is not set, the default above is used — the service does not fail to start.
- `PORT`, `CLEANUP_HOURS` and `CLEANUP_INTERVAL` are converted to integers; a non-numeric value makes startup fail.
- `DEBUG` is true only when its value lowercases to `true`.
- **`LOCAL_IP` matters most.** It is what gets substituted into the `callback_url` returned by `GET /generate` and into `server_ip` at `/`. Leave it at `127.0.0.1` and callbacks sent from another machine will not reach you. Set it to the machine's real address on the local network, for example `192.168.1.100`.

> Русский: все семь переменных перечислены в таблице со значениями по умолчанию — они совпадают с `app/config.py`. Переменные необязательны: незаданное значение заменяется значением по умолчанию, а числовые переменные (`PORT`, `CLEANUP_HOURS`, `CLEANUP_INTERVAL`) приводит к целому числу, и некорректное значение приведёт к падению на старте. Отдельно отмечена `LOCAL_IP` — она подставляется в `callback_url` из `GET /generate`, поэтому вместо `127.0.0.1` нужно указать реальный адрес машины в локальной сети, иначе внешние клиенты не смогут достучаться.

## API Reference

All endpoints are unauthenticated.

### `GET /`

Health and status.

Response `200`:

```json
{
  "status": "ok",
  "service": "Mini Collaborator",
  "version": "2.0.0",
  "server_ip": "192.168.1.100"
}
```

```bash
curl http://127.0.0.1:8000/
```

> Русский: диагностический эндпоинт без аутентификации. Возвращает признак работоспособности `status`, название сервиса, версию и значение `LOCAL_IP` в поле `server_ip`.

### `GET /generate`

Issues a fresh token. A new one is generated on every call; the token itself is **not** written to the database, so it shows up in `GET /tokens` only after at least one callback arrives.

Response `200`:

```json
{
  "token": "f8122962-e378-4fb3-9de0-11ff65c4678b",
  "callback_url": "http://192.168.1.100:8000/c/f8122962-e378-4fb3-9de0-11ff65c4678b",
  "dns": "f8122962-e378-4fb3-9de0-11ff65c4678b.collab.local",
  "created_at": "2026-10-01T18:15:54.117287"
}
```

| Field | Meaning |
|---|---|
| `token` | UUID4 identifier used to group callbacks |
| `callback_url` | Full URL to hand to the third party; built from `LOCAL_IP` and `PORT` |
| `dns` | `<token>.collab.local` placeholder, only useful if you set up that DNS record |
| `created_at` | ISO 8601 timestamp, UTC |

```bash
curl http://127.0.0.1:8000/generate
```

> Русский: каждый вызов выдаёт новый уникальный токен UUID4. Готовый `callback_url` собирается из `LOCAL_IP` и `PORT`, а не из адреса, по которому пришёл запрос. Поле `dns` — заготовка под DNS-запись `collab.local`, без её настройки не работает. Токен не сохраняется в базе: он появится в `GET /tokens` только после первого коллбэка.

### `/c/{token}`

Callback receiver. Accepts `GET`, `POST`, `PUT`, `DELETE` and `PATCH`.

Stored per request: the token, client IP (`"unknown"` if unavailable), HTTP method, all request headers as a JSON object, all query parameters as a JSON object, the body decoded as a string with errors ignored, and a UTC creation timestamp.

The token is **not validated** — any string is accepted and recorded, whether or not `GET /generate` ever issued it.

Response `200`:

```json
{
  "status": "received",
  "token": "f8122962-e378-4fb3-9de0-11ff65c4678b",
  "timestamp": "2026-10-01T18:16:58.468614"
}
```

On a failure while reading the body or saving to the database the service still responds with HTTP **200**, and the body is a two-element array holding the error and the intended status code:

```json
[{"error": "database is locked"}, 500]
```

> Русский: принимает пять методов — `GET`, `POST`, `PUT`, `DELETE`, `PATCH`. Сохраняет IP клиента, метод, все заголовки, все query-параметры, тело (ошибки декодирования игнорируются) и время. Токен **не проверяется** — принимается любая строка, даже если `GET /generate` её никогда не выдавал. Обратите внимание на ошибочный ответ: HTTP-статус остаётся **200**, а `500` находится вторым элементом массива в теле, то есть на код ответа это не влияет.

```bash
curl -s -X POST "http://127.0.0.1:8000/c/$TOKEN?source=demo" \
  -H "Content-Type: application/json" \
  -d '{"order": 42, "amount": 19.99}'
```

### `GET /tokens`

Distinct tokens that already have at least one stored callback.

Response `200`:

```json
{"tokens": ["f8122962-e378-4fb3-9de0-11ff65c4678b", "1c9f0b7a-2d3e-4f5a-8b6c-7d8e9f0a1b2c"]}
```

Returns an empty list on an empty database — no error.

```bash
curl http://127.0.0.1:8000/tokens
```

> Русский: список уникальных токенов, по которым уже есть хотя бы одна запись коллбэка. Каждый токен присутствует один раз, даже если записей много. На пустой базе — пустой список, а не ошибка.

### `GET /logs/{token}`

Journal for one token, newest first.

Response `200` — an array sorted by `created_at` descending:

```json
[
  {
    "id": 6,
    "ip": "127.0.0.1",
    "method": "POST",
    "headers": {"host": "127.0.0.1:8000", "content-type": "application/json"},
    "query": {"source": "demo"},
    "body": "{\"order\": 42, \"amount\": 19.99}",
    "created_at": "2026-10-01T18:16:58.530591"
  }
]
```

`headers` and `query` come back as JSON objects, not as strings containing JSON. For an unknown token the response is `200` with an empty array — not `404`.

```bash
curl "http://127.0.0.1:8000/logs/$TOKEN"
```

> Русский: журнал по одному токену, отсортированный по времени от новых к старым. Поля `headers` и `query` возвращаются как готовые JSON-объекты, а не как строки с JSON внутри. Для неизвестного токена ответ — **200 с пустым массивом**, а не 404.

### `GET /stats/{token}`

Aggregated statistics for one token.

Response `200`:

```json
{
  "total": 3,
  "unique_ips": 1,
  "methods": {"POST": 2, "PUT": 1},
  "first_request": "2026-10-01T18:17:02.885718",
  "last_request": "2026-10-01T18:17:02.918125",
  "recent": [
    {"time": "2026-10-01T18:17:02.885718", "method": "POST", "ip": "127.0.0.1"}
  ]
}
```

| Field | Meaning |
|---|---|
| `total` | Number of stored callbacks for the token |
| `unique_ips` | Number of distinct client IPs |
| `methods` | Callback count per HTTP method |
| `first_request` / `last_request` | Oldest and newest callback, ISO 8601 UTC |
| `recent` | Up to 10 entries with `time`, `method`, `ip` |

When the token has no records the service responds with HTTP **200** and the array:

```json
[{"error": "Token not found"}, 404]
```

The `404` is the second array element, not the HTTP status code.

`recent` is taken from an unsorted query result, so when a token has more than 10 callbacks it is not guaranteed to be the 10 newest ones — for a strict time window read `/logs/{token}` and filter on `created_at` yourself.

```bash
curl "http://127.0.0.1:8000/stats/$TOKEN"
```

> Русский: агрегаты по токену — общее число записей, количество уникальных IP, распределение по HTTP-методам, границы по времени и список `recent`. Поле `recent` берётся из неотсортированной выборки, поэтому при более чем 10 коллбэках это не обязательно 10 самых свежих — для точного окна времени читайте `/logs/{token}` и фильтруйте по `created_at`. При отсутствии записей HTTP-статус снова **200**, а `404` находится вторым элементом массива `[{"error": "Token not found"}, 404]`, то есть на код ответа не влияет.

### `DELETE /logs/{token}`

Deletes every stored callback for the token. Records belonging to other tokens are left untouched.

Response `200`:

```json
{"deleted": 3, "token": "f8122962-e378-4fb3-9de0-11ff65c4678b"}
```

Returns `deleted: 0` when there was nothing to remove — no error.

```bash
curl -s -X DELETE "http://127.0.0.1:8000/logs/$TOKEN"
```

> Русский: удаляет все записи по указанному токену и возвращает их количество в поле `deleted`. Записи других токенов не затрагиваются. Если удалять было нечего, приходит `deleted: 0` без ошибки.

## Usage Examples

The full flow: get a token, send it a callback, inspect what came back, then clean up. The token from step 1 is reused throughout.

```bash
# 1. Issue a token and remember it
TOKEN=$(curl -s http://127.0.0.1:8000/generate | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
echo "$TOKEN"

# 2. Send a callback to the URL that belongs to it
curl -s -X POST "http://127.0.0.1:8000/c/$TOKEN?source=demo" \
  -H "Content-Type: application/json" \
  -d '{"order": 42, "amount": 19.99}'

# 3. A different method is captured the same way
curl -s -X PUT "http://127.0.0.1:8000/c/$TOKEN" -d 'plain text body'

# 4. Read the journal, newest first
curl -s "http://127.0.0.1:8000/logs/$TOKEN" | python3 -m json.tool

# 5. Aggregate statistics
curl -s "http://127.0.0.1:8000/stats/$TOKEN" | python3 -m json.tool

# 6. The token is now listed
curl -s http://127.0.0.1:8000/tokens

# 7. Clean up
curl -s -X DELETE "http://127.0.0.1:8000/logs/$TOKEN"
```

Pointing a third-party service at the URL is the same thing from its side — it just posts to `callback_url` from `GET /generate`:

```bash
curl -s -X POST "http://192.168.1.100:8000/c/$TOKEN" -d 'anything they send'
```

> Русский: сквозной сценарий — токен из `GET /generate` сохраняется в shell-переменную `TOKEN` и переиспользуется во всех следующих командах. Переменная экспортируется как обычный результат `curl`, поэтому все примеры копируются и выполняются подряд без правок. Внешний сервис при этом просто отправляет запрос на `callback_url` — специальная интеграция не требуется.

## Project Structure

| Path | Purpose |
|---|---|
| `run.py` | Entry point — starts uvicorn from `HOST`, `PORT`, `DEBUG` |
| `app/main.py` | FastAPI application: all routes and the background cleanup task |
| `app/config.py` | Reads every setting from the environment with defaults |
| `app/models.py` | SQLAlchemy `Callback` model and table mapping |
| `app/database.py` | Engine, session factory and the `get_db` dependency |
| `requirements.txt` | Pinned dependencies |
| `.env.sample` | Template for `.env` — copy it and adjust |
| `Dockerfile` | Image definition, `python:3.10-slim`, exposes 8000 |

Table `callbacks` is created automatically at startup if it does not exist yet.

> Русский: точка входа — `run.py`, вся логика и маршруты — в `app/main.py`, настройки — в `app/config.py`, модель `Callback` — в `app/models.py`, движок и сессии — в `app/database.py`. Таблица `callbacks` создаётся автоматически при старте, если её ещё нет.

## Troubleshooting

**Port 8000 is already in use**

The process refuses to start or logs an address-in-use error. Free the port or move the service: set `PORT=8080` in `.env` and use the new port in the examples. Find the current holder with `lsof -i :8000`.

**Callbacks do not arrive — check `LOCAL_IP`**

`GET /generate` builds `callback_url` from `LOCAL_IP`, not from the address the request came in on. If `LOCAL_IP` is still `127.0.0.1`, a client on another machine receives a URL pointing at itself. Set `LOCAL_IP` to the machine's real network address and restart the service.

**Data disappears after recreating the container**

`callbacks.db` lives inside the container filesystem, so `docker rm` takes the data with it. Mount a host directory and point `DATABASE_URL` at it — see the Docker section above.

**A freshly issued token is missing from `GET /tokens`**

Expected behaviour: `GET /generate` does not persist the token. It appears only once at least one callback has been recorded for it. Send a request to `/c/<token>` and re-check.

**`recent` does not show the latest callbacks**

`recent` is built from an unsorted query, so with more than 10 callbacks the entries are not guaranteed to be the newest. Use `GET /logs/{token}`, which is sorted by `created_at` descending.

**Error responses carry a 200 status**

`GET /stats/{token}` for an unknown token and `/c/{token}` on a save failure both respond with HTTP 200 and a two-element array such as `[{"error": "Token not found"}, 404]`. The numeric code lives inside the body. If you are branching on the HTTP status, check the array contents too.

**Records vanish earlier than expected**

The cleanup task deletes anything older than `CLEANUP_HOURS`. Lower it to keep history longer, and remember it runs every `CLEANUP_INTERVAL` seconds.

> Русский: разобран типовой набор проблем — занятый порт, незаданный `LOCAL_IP`, потеря SQLite-базы при пересоздании контейнера, отсутствие токена в списке до первого коллбэка, неполный `recent` в статистике и неожиданный HTTP-статус 200 при ошибке. Для каждой указано конкретное действие: сменить `PORT`, задать реальный адрес в `LOCAL_IP`, смонтировать директорию, отправить тестовый коллбэк, читать отсортированный `/logs/{token}` и разбирать тело ответа как массив.
