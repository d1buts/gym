# Workout Tracker

Spreadsheet-first персональний workout tracker: продумана Google Spreadsheet
із чотирма тренувальними комплексами, формулами й дашбордом; контрольоване
додавання тренувань через ChatGPT; відтворювана аналітика та evidence-backed
recommendations.

## Product outcome

Користувацький цикл:

```text
відкрити комплекс → виконати тренування → описати його в ChatGPT
→ перевірити preview → підтвердити запис → переглянути прогрес
→ отримати й окремо прийняти рекомендацію
```

Google Spreadsheet залишається придатною для ручної роботи без ChatGPT.
Python/SQLite є допоміжним validation, snapshot, analytics і restore layer,
а не основним інтерфейсом.

## Status

Продуктову ціль виправлено й зафіксовано в ADR-003, PRD та двох нормативних
specs. GSD planning перебудовується під Spreadsheet-first milestone;
виконуваної реалізації ще немає.

## Start here

1. [Product requirements](docs/prd/PRD-GOOGLE-SHEETS-WORKOUT-COACH.md)
2. [Architecture](WORKOUT_TRACKER_ARCHITECTURE.md)
3. [Workbook specification](docs/specs/SPEC-GOOGLE-SHEETS-WORKBOOK.md)
4. [ChatGPT integration specification](docs/specs/SPEC-CHATGPT-WORKOUT-CAPTURE.md)
5. [Project context](.planning/PROJECT.md)
6. [Requirements traceability](.planning/REQUIREMENTS.md)
7. [Roadmap](.planning/ROADMAP.md)
8. [Agent instructions](AGENTS.md)

## Repository map

```text
.planning/                 GSD project context, requirements and roadmap
4-day upper lower program/ Human-readable program bootstrap specification
gym equipment/             Confirmed equipment and exercise references
config/                    Versioned schemas and executable rules
docs/architecture/         ADRs and normative technical contracts
docs/prd/                  Product requirements
docs/specs/                Workbook and ChatGPT integration contracts
```

## Privacy

Never commit a live spreadsheet locator, OAuth material, populated local
configuration, personal exports, SQLite databases, reports, logs or backups.
Use `.env.example` and `config/settings.example.yaml` only as templates.

The security review found sensitive operational metadata in already-pushed
public history. See
[Security and backup](docs/architecture/SECURITY_AND_BACKUP.md) before
publishing further changes.

## Planning

The current planning artifacts must be generated from the accepted ADR, PRD
and specs. `.planning/STATE.md` is authoritative for the next workflow after
the GSD rebaseline completes.
