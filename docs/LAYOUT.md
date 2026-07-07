# Раскладка каталогов

Монорепо системы микросервисов. Каждый сервис — отдельный каталог в
`services/<name>/`, свой стек (один на сервис) и свой `Dockerfile`. Сервисы
общаются через брокер, заданный в корневом `docker-compose.yml`.

```
<project>/
  AGENTS.md                 правила работы
  README.md
  docker-compose.yml        оркестрация: сервисы + брокер + сеть + volumes
  .env.example              переменные окружения (копируется в .env)
  .gitignore
  LICENSE  LICENSE-DOCS
  docs/
    INDEX.md                карта документации
    ARCHITECTURE.md         система сервисов, брокер, потоки, деплой
    BACKLOG.md              очередь задач
    STACKS.md               toolchain/layout/команды по стекам
    LAYOUT.md               этот файл
    DEPLOYMENT.md           docker-compose: сервисы, сети, запуск локально
    specs/
      <service>/
        <module>.md         контракт модуля (по одному на модуль)
      EXAMPLE.md           # пример — удали
    adr/                    архитектурные решения
  services/
    <service-a>/            один сервис = один стек
      <manifest>            pyproject.toml / go.mod / Cargo.toml / package.json
      <lock>                uv.lock / go.sum / Cargo.lock / pnpm-lock.yaml
      Dockerfile
      <src>                 исходники по layout выбранного стека (см. STACKS.md)
      README.md             (опц.) краткое описание сервиса + его стек
    <service-b>/
      …
  shared/                   (опц.) общие схемы/контракты между сервисами
                            (proto/JSON-schema/генерируемые SDK)
```

## Модули и спеки

Внутри сервиса код делится на модули. **Каждый модуль — отдельный спек** в
`docs/specs/<service>/<module>.md` по канонической структуре (см.
`docs/INDEX.md` → *Как работать со спеками*). Модуль — это:

- Python: пакет/подпакет под `src/` сервиса.
- Go: пакет под `internal/` или `pkg/` сервиса.
- Rust: crate (если workspace) или модуль под `src/` сервиса.
- TypeScript: директория/модуль под `src/` сервиса.

## Где живут общие вещи

- Контракты модулей — `docs/specs/<service>/<module>.md`.
- Состав сервисов, брокер, потоки — `docs/ARCHITECTURE.md`.
- Деплой (compose, сети, переменные) — `docs/DEPLOYMENT.md`.
- Общие схемы между сервисами — `shared/` (если есть) + ссылка из `ARCHITECTURE.md`.
- Кросс-сервисные конвенции (event envelope, форматы) — `docs/CONVENTIONS.md`
  (заведи при необходимости) или во внешнем хабе.
- ADR — `docs/adr/` (или внешний хаб — см. `AGENTS.md` → *ADR*).

## Новый сервис

Чек-лист добавления сервиса в систему:

1. `services/<name>/` с манифестом выбранного стека (команды — `docs/STACKS.md`).
2. `services/<name>/Dockerfile`.
3. Запись в `docker-compose.yml` (build context, depends_on брокера, env).
4. Спеки модулей: `docs/specs/<name>/<module>.md`.
5. Строка в таблице сервисов `docs/ARCHITECTURE.md`.
6. Если сервис публикует/читает топики — описать в разделе «Брокер» `ARCHITECTURE.md`.