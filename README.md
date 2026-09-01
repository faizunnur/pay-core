# PayCore Payments API

PayCore is the internal payments API for **Northwind Retail**. It accepts a
payment request, runs a fraud/risk check, records the transaction in Postgres and
returns a receipt.

> **Note for students:** PayCore contains known, intentional weaknesses used as
> teaching material. Do not deploy this to a real environment or process real
> card data with it.

## Stack

| Layer | Choice |
| --- | --- |
| Language | Python 3.11 |
| Web framework | FastAPI |
| Database | PostgreSQL 15 |
| Cache | Redis 7 |
| Tests | pytest |
| Linting | ruff |
| Containers | Docker + Docker Compose |
| CI | GitHub Actions |

## Quick start with Docker

```bash
cp .env.example .env
docker compose up --build
```

Then open <http://localhost:8000/docs> for the generated API documentation.

## Quick start without Docker

You still need Postgres and Redis running locally (or start just those two with
`docker compose up db redis`).

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Endpoints

| Method | Path | What it does |
| --- | --- | --- |
| GET | `/health` | Liveness. The process is up. |
| GET | `/ready` | Readiness. Postgres and Redis are reachable. |
| POST | `/payments` | Take a payment request, risk-check it, record it. |
| GET | `/payments/{id}` | Fetch one receipt. |
| GET | `/merchants/{id}` | Look up one merchant. |

Example:

```bash
curl -X POST http://localhost:8000/payments \
  -H "Content-Type: application/json" \
  -d '{
        "merchant_id": "11111111-1111-1111-1111-111111111111",
        "card_token": "tok_visa_4242",
        "amount_cents": 2500,
        "currency": "CAD",
        "description": "coffee beans"
      }'
```

## Tests and linting

```bash
pytest
ruff check .
```

Both run in CI on every pull request, together with a Docker build. Run them
locally before you push.

## Repository layout

```
app/          FastAPI application: routes, schemas, models, config
services/     Risk engine and ledger
tests/        pytest suite
infra/        Terraform (Week 3)
k8s/          Kubernetes manifests (Week 9)
policies/     OPA/Rego policies (Week 15)
docs/         Architecture, runbook, contributing guide
```

`infra/`, `k8s/` and `policies/` are empty on purpose. They fill up as the course
goes on.

## Ports used across the course

| Port | Service | From week |
| --- | --- | --- |
| 8000 | PayCore API | 1 |
| 5432 | PostgreSQL | 1 |
| 6379 | Redis | 1 |
| 8200 | HashiCorp Vault | 5 |
| 8080 | Jenkins | 6 |
| 9000 | SonarQube | 7 |
| 9090 | Prometheus | 13 |
| 3000 | Grafana | 13 |
| 5601 | Kibana | 13 |

Keep them free on your machine.

## Contributing

Read [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) before your first pull request.
Short version: branch as `feature/<initials>-<short-description>`, keep it small,
`ruff check .` and `pytest` pass before you open the PR, and `main` only takes
squash merges through a reviewed pull request.

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - what talks to what, and why
- [docs/RUNBOOK.md](docs/RUNBOOK.md) - operating the service (expanded in Week 13)
- [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) - branching and pull request rules
