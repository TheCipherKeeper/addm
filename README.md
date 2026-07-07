# AI Project Template

[![Template](https://img.shields.io/badge/repo-template-blueviolet)](#)
[![License: MIT](https://img.shields.io/badge/code-MIT-green)](LICENSE)
[![Docs: CC BY 4.0](https://img.shields.io/badge/docs-CC%20BY%204.0-lightgrey)](LICENSE-DOCS)

Универсальная заготовка-первоисточник для старта любого проекта, в котором
разработка ведётся вместе с AI-агентами. Не привязана к языку или стеку:
правила описаны обобщённо, а там, где нужен пример, — помечены плейсхолдером.

Содержит методологию, а не код: иерархию документов, модель ветвления,
рабочий цикл, каноническую структуру спеков и ADR. Клонируй, подставь свой
стек — и работай по одним правилам с людьми и агентами.

## Что внутри

```
AGENTS.md             правила работы в репозитории (для людей и агентов)
docs/INDEX.md         карта документации, точка входа
docs/ARCHITECTURE.md  архитектура системы (скелет-плейсхолдер)
docs/BACKLOG.md       очередь задач
docs/specs/           контракты модулей (по одному файлу на модуль)
docs/adr/             архитектурные решения (ADR)
```

## Быстрый старт

1. Создай репо из шаблона (кнопка *Use this template* на GitHub) или склонируй
   и оторви историю: `git checkout --orphan main && git add -A && git commit -m "init"`.
2. Пройди по `AGENTS.md` и замени плейсхолдеры под свой проект:
   - `<STACK>` — язык/рантайм/сборщик (Rust+Cargo, Python+uv, Node+pnpm, …).
   - Команды проверки (lint / test / build) под свой стек.
   - Решить, где живут ADR: в `docs/adr/` (по умолчанию) или во внешнем хабе
     (см. заметку в `AGENTS.md` → *ADR*).
3. Заполни `docs/ARCHITECTURE.md` и `docs/BACKLOG.md` под свою систему.
4. Удали `docs/specs/EXAMPLE.md` и создавай спеки под свои модули.

## Документация

| Файл | Что |
|---|---|
| `AGENTS.md` | Правила работы: ветвление, коммиты, что можно/нельзя |
| `docs/INDEX.md` | Карта документации |
| `docs/ARCHITECTURE.md` | Архитектура: слои, потоки данных, доверительная граница |
| `docs/BACKLOG.md` | Очередь задач |
| `docs/specs/` | Контракты модулей (по одному файлу на модуль) |
| `docs/adr/` | Архитектурные решения (ADR) |

## Разработка

```bash
git checkout dev
git pull
git checkout -b feat/<задача>

# внести изменения
lint      # см. команды под свой стек в AGENTS.md
test
build

git commit -m "feat: ..."
git push
# открыть PR в dev
```

Полный цикл — в `AGENTS.md`. Задачи — в `docs/BACKLOG.md`.

## Лицензия

- Код: [MIT](LICENSE)
- Документация: [CC BY 4.0](LICENSE-DOCS)