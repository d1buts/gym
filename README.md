# Workout Tracker

Персональний workout-tracker, у якому Google Sheets зберігає operational
training facts, а локальний Python CLI у майбутньому забезпечить validation,
immutable snapshots, SQLite analytics, evidence-backed reports і перевірене
відновлення.

## Status

Проєкт перебуває на стадії архітектури та GSD planning. Виконуваного CLI ще
немає.

- 22 v1 requirements mapped to 5 phases.
- Architecture ingest: 0 blockers, 0 warnings.
- Runtime: Python 3.12+, Pydantic, SQLite, pytest-compatible design.
- V1: read-only Google Sheets pull; capture, write-back і recommendations
  відкладені.

## Start here

1. [Project context](.planning/PROJECT.md)
2. [Requirements](.planning/REQUIREMENTS.md)
3. [Roadmap](.planning/ROADMAP.md)
4. [Architecture](WORKOUT_TRACKER_ARCHITECTURE.md)
5. [Architecture review](docs/architecture/ARCHITECTURE_REVIEW.md)
6. [Agent instructions](AGENTS.md)

## Repository map

```text
.planning/                 GSD project context, requirements and roadmap
4-day upper lower program/ Human-readable training program
gym equipment/             Confirmed equipment and exercise references
config/                    Versioned contracts and rule definitions
docs/architecture/         ADRs and normative technical specifications
```

Planned runtime directories such as `src/`, `data/`, `reports/` and `tests/`
will be created by phase execution, not by architecture-only work.

## Privacy

Never commit a live spreadsheet locator, OAuth material, populated local
configuration, personal exports, SQLite databases, reports or backups.
Use `.env.example` and `config/settings.example.yaml` as templates.

The security review found sensitive operational metadata in already-pushed
public history. See
[Security and backup](docs/architecture/SECURITY_AND_BACKUP.md) before
publishing further changes.

## Next workflow

The project is ready for:

```text
$gsd-plan-phase 1
```
