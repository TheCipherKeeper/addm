# AI Microservices Template

[![Template](https://img.shields.io/badge/repo-template-blueviolet)](#)
[![License: MIT](https://img.shields.io/badge/code-MIT-green)](LICENSE)
[![Docs: CC BY 4.0](https://img.shields.io/badge/docs-CC%20BY%204.0-lightgrey)](LICENSE-DOCS)

Универсальная заготовка-первоисточник для **системы микросервисов в одном
монорепо**. Программа — это совокупность сервисов; сервисы общаются между собой
через **брокер** (Kafka/Redpanda/NATS — зафиксируй один); вся система
развёртывается как контейнеры в **docker compose**.

Каждый сервис реализуется на **одном** из стеков: Python, Go, Rust или
TypeScript (бэкенд). Методология и команды подстраиваются под выбранный стек —
один сервис = один язык, но разные сервисы в монорепо могут быть на разных стеках.

Содержит методологию, а не код: иерархию документов, модель ветвления,
рабочий цикл, каноническую структуру спеков, ADR, раскладку монорепо и модель
деплоя. Клонируй, добавляй сервисы — и работай по одним правилам с людьми и агентами.

## Что внутри

```
AGENTS.md               правила работы (для людей и агентов)
docker-compose.yml      оркестрация: сервисы + брокер + volumes
.env.example            переменные окружения для локального запуска
docs/
  INDEX.md              карта документации, точка входа
  ARCHITECTURE.md       система сервисов, брокер, потоки, деплой
  BACKLOG.md            очередь задач
  STACKS.md             toolchain/layout/команды по стекам
  LAYOUT.md             раскладка каталогов монорепо
  DEPLOYMENT.md         docker-compose: сервисы, сети, запуск локально
  specs/<svc>/<mod>.md  контракты модулей (по одному на модуль, сгруппированы по сервисам)
  adr/                  архитектурные решения
services/
  <service>/            один сервис = один стек = один Dockerfile
    <manifest>          pyproject.toml / go.mod / Cargo.toml / package.json
    Dockerfile
    <src>               исходники по layout выбранного стека
shared/                 (опц.) общие схемы/контракты между сервисами
```

## Быстрый старт

1. Создай репо из шаблона (кнопка *Use this template* на GitHub) или склонируй
   и оторви историю: `git checkout --orphan main && git add -A && git commit -m "init"`.
2. **Выбери брокер** (один на систему): Kafka / Redpanda / NATS. Зафиксируй в
   `docs/ARCHITECTURE.md` и `docker-compose.yml`.
3. Заведи сервисы в `services/<name>/`, по одному стеку на сервис. Команды
   выбранного стека — в `AGENTS.md` → *Команды проверки по стеку* и `docs/STACKS.md`.
4. Опиши сервисы и потоки в `docker-compose.yml` (см. `docs/DEPLOYMENT.md`).
5. Заполни `docs/ARCHITECTURE.md` (состав сервисов, брокер, потоки) и
   `docs/BACKLOG.md`.
6. Создавай спеки под модули сервисов: `docs/specs/<service>/<module>.md`.
   Удали `docs/specs/EXAMPLE.md`.

## Документация

| Файл | Что |
|---|---|
| `AGENTS.md` | Правила работы: ветвление, коммиты, что можно/нельзя, команды по стекам |
| `docs/INDEX.md` | Карта документации |
| `docs/ARCHITECTURE.md` | Система: сервисы, брокер, потоки данных, деплой |
| `docs/BACKLOG.md` | Очередь задач |
| `docs/STACKS.md` | Toolchain, layout и команды для Python/Go/Rust/TS |
| `docs/LAYOUT.md` | Раскладка каталогов монорепо |
| `docs/DEPLOYMENT.md` | docker-compose: сервисы, сети, запуск локально |
| `docs/specs/` | Контракты модулей (по сервисам) |
| `docs/adr/` | Архитектурные решения (ADR) |

## Разработка

```bash
git checkout dev
git pull
git checkout -b feat/<задача>

# внести изменения
lint      # команды выбранного стека — AGENTS.md / docs/STACKS.md
test
build

git commit -m "feat: ..."
git push
# открыть PR в dev
```

Локальный запуск всей системы:

```bash
cp .env.example .env
docker compose up --build
```

Полный цикл — в `AGENTS.md`. Задачи — в `docs/BACKLOG.md`. Деплой — в
`docs/DEPLOYMENT.md`.

## Лицензия

- Код: [MIT](LICENSE)
- Документация: [CC BY 4.0](LICENSE-DOCS)