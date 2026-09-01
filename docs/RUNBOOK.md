# PayCore Runbook

> Stub. This file gets filled in properly in Week 13, when we cover
> observability and on-call. For now it holds only what a person needs at 3am to
> get the stack running and to know what depends on what.

## Service summary

| Field | Value |
| --- | --- |
| Service | PayCore Payments API |
| Owner | Northwind Retail, payments team |
| Repository | `paycore` |
| Runtime | Python 3.11 / FastAPI |
| Datastores | PostgreSQL 15, Redis 7 |
| Ports | API 8000, Postgres 5432, Redis 6379 |

## Health checks

| Endpoint | Meaning |
| --- | --- |
| `GET /health` | The process is up. Never touches a dependency. |
| `GET /ready` | Postgres and Redis are both reachable. Returns 503 if either is not. |

## Start and stop the local stack

```bash
cp .env.example .env
docker compose up --build      # start
docker compose logs -f api     # watch
docker compose down            # stop
docker compose down -v         # stop and drop the data
```

## Common situations

**`/ready` reports `database: unavailable`**
Postgres is not up, or the credentials do not match. Check `docker compose ps`
and the `POSTGRES_*` values in your `.env`.

**`/ready` reports `cache: unavailable`**
Redis is down. Payments still work: the risk engine falls back to reading
merchant history straight from Postgres. Watch the response times while it does.

**Everything is being declined**
Check `RISK_ENGINE_THRESHOLD`. A low threshold declines everything. The reason
codes behind each decision are on the payment log line, next to the score.

**Port already in use on startup**
Something else owns 8000, 5432 or 6379. See the port table in the README.

## To be written in Week 13

- [ ] Dashboards, and the alerts that page a human
- [ ] SLOs and the error budget
- [ ] Escalation path and who is on call
- [ ] Rollback procedure with the exact commands
- [ ] Post-incident review template
