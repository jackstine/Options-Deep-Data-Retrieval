
## Architecture Diagram

```
┌─────────────────┐
│   Commands      │  CLI entry points
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Pipelines     │  Orchestration layer
└────────┬────────┘
         │
         ├──────────┐
         ▼          ▼
┌──────────────┐ ┌──────────────┐
│   Services   │ │ Repositories │  Business logic & Data access
└──────┬───────┘ └──────┬───────┘
       │                │
       │                ▼
       │         ┌──────────────┐
       │         │   Database   │  PostgreSQL
       │         └──────────────┘
       │
       ▼
┌──────────────┐
│    Models    │  Data structures
└──────────────┘
```