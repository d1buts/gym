# Architecture index

Normative documents for Workout Tracker v1:

1. [Architecture review](ARCHITECTURE_REVIEW.md)
2. [ADR-001: authority boundaries](ADR-001-authority-boundaries.md)
3. [ADR-002: Python and SQLite](ADR-002-python-sqlite-v1.md)
4. [Data model](DATA_MODEL.md)
5. [Synchronization protocol](SYNC_PROTOCOL.md)
6. [Metrics](METRICS.md)
7. [Security and backup](SECURITY_AND_BACKUP.md)

Machine-readable contracts:

- [Source schema](../../config/schema.yaml)
- [Progression rules](../../config/progression-rules.yaml)
- [Local settings template](../../config/settings.example.yaml)

The root
[WORKOUT_TRACKER_ARCHITECTURE.md](../../WORKOUT_TRACKER_ARCHITECTURE.md)
is the system overview. If an overview statement conflicts with a normative
contract, the accepted ADR and then the more specific normative contract take
precedence.
