# Деплой

Локальная разработка и деплой — через **docker compose**. Вся система
(сервисы + брокер + общая инфраструктура) описывается в корневом
`docker-compose.yml`. Каждый сервис имеет свой `Dockerfile` в
`services/<name>/`.

## Запуск локально

```bash
cp .env.example .env          # заполни переменные
docker compose up --build     # поднять всё
docker compose up <service>   # только один сервис (+ зависимости)
docker compose down           # остановить
```

## Структура docker-compose.yml

```yaml
services:
  broker:              # один на систему (Kafka / Redpanda / NATS)
    image: <broker-image>
    ports: ["9092:9092"]
    volumes: ["broker-data:/data"]

  <service-a>:         # сервис = отдельный контейнер
    build: { context: ./services/<service-a> }
    depends_on: [broker]
    env_file: .env
    # внешние порты — только если сервис принимает трафик снаружи

volumes:
  broker-data:
```

Правила:

- `build.context` указывает на `services/<name>/` (там же `Dockerfile`).
- `depends_on: [broker]` для сервисов, читающих/пишущих в брокер.
- Переменные — из `.env` / `.env.example`; секрета в репо не держать.
- Сеть по умолчанию изолирует сервисы; внешние порты открывать осознанно.
- Брокер и общие volumes описываются в корневом compose, не в сервисах.

## Dockerfile сервиса

Собирается из команд `build` выбранного стека (`docs/STACKS.md`). Минимальный
скелет зависит от стека — держи его в `services/<name>/Dockerfile`. Общие
требования:

- Мультистадийная сборка: stage сборки → тонкий runtime-образ.
- В runtime-образе — только артефакт `build` и необходимые runtime-зависимости.
- Не запускать от root, где позволяет стек.
- Healthcheck, если сервис его предоставляет.

## Переменные окружения

`/.env.example` — шаблон переменных, коммитится. `/.env` — реальные значения,
в `.gitignore`. На сервис одна строка конфигурации в `docker-compose.yml`
через `env_file: .env` или явный `environment:`.

## Сборка и проверка перед деплоем

Перед тем как поднимать compose:

- Прогнать `lint / test / build` для каждого затронутого сервиса (команды —
  `AGENTS.md` → *Команды проверки по стекам*).
- `docker compose build` — убедиться, что образы собираются.
- `docker compose config` — проверить валидность compose.