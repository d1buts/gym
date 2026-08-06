# ADR-002: Python і SQLite для локального аналітичного контуру

- **Status:** Accepted
- **Date:** 2026-07-24
- **Decision owner:** repository owner

## Context

Локальний контур виконує schema validation, Google Sheets pull,
нормалізацію, аналітику, звіти й restore verification. Згідно з ADR-003,
основним користувацьким продуктом є Google Spreadsheet із контрольованою
ChatGPT integration; локальний CLI є її допоміжним validation/analytics
layer. Multi-user і server database не входять до поточного milestone.

## Decision

- Runtime: Python 3.12+.
- Dependency workflow: uv-style project management.
- External and normalized validation boundary: Pydantic.
- Analytical store: SQLite з foreign keys; WAL для readers і транзакційне
  promotion staging data.
- Automated verification: pytest-compatible tests.
- Numeric calculations: `Decimal` або scaled integers; SQLite `REAL` не є
  authoritative representation для loads і metric evidence.

Конкретні libraries для Sheets client, CLI rendering і tabular processing
обираються під час phase planning. Вони не є частиною цього ADR.

## Consequences

- Перший milestone не залежить від server database.
- Spreadsheet лишається придатною для ручного використання без локального CLI.
- Business logic не повинна залежати від CLI framework або Google client.
- Raw capture, normalization, reconciliation, metrics і rendering мають
  окремі модульні межі.
- Майбутній web/mobile client може використовувати окремий API без
  переписування metric semantics.

## Revisit when

- з’являється multi-user authentication;
- потрібні concurrent remote writes;
- SQLite перестає відповідати обсягу або deployment model;
- основний продукт стає TypeScript-first web application.
