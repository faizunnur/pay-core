# PayCore Architecture

PayCore is the internal payments API for Northwind Retail. It does three things:

1. Accepts a payment request (card token, amount, currency, merchant id).
2. Runs a fraud/risk check against a rules service.
3. Records the transaction in Postgres and returns a receipt.

Small enough to read in an afternoon. Real enough to have real security problems.

## The picture

```
                 +---------------------------+
   client   -->  |  FastAPI  (app/main.py)   |
   (POS,         |                           |
   webshop)      |  /health   /ready         |
                 |  /payments /merchants     |
                 +------------+--------------+
                              |
                 +------------v--------------+
                 |  risk engine              |
                 |  services/risk_engine.py  |
                 +---+------------------+----+
                     |                  |
             cache   |                  |  merchant history
             lookup  |                  |  (rebuilt on a cache miss)
                     v                  v
              +-------------+    +----------------+
              |   Redis 7   |    | PostgreSQL 15  |
              +-------------+    +--------+-------+
                                          ^
                 +------------------------+
                 |  ledger
                 |  services/ledger.py  (writes the transaction row)
                 +---------------------
```

## Request lifecycle: POST /payments

1. `app/routers/payments.py` validates the body against `PaymentRequest`
   (`app/schemas.py`). Bad amounts and currencies are rejected with 422 before
   anything else happens.
2. `services/risk_engine.py` scores the request from 0 to 100:
   - static rules on the request itself (amount bands, currency, token shape);
   - the merchant's recent behaviour, read from Redis, and rebuilt from the
     `transactions` table when the cache does not have it.
3. A score at or above `RISK_ENGINE_THRESHOLD` (default 70) is `declined`,
   anything below is `approved`. Either way it is a real decision and it gets
   recorded.
4. `services/ledger.py` writes one row to `transactions` and the router returns
   the receipt with a 201.

## Data model

| Table | Columns | Notes |
| --- | --- | --- |
| `merchants` | `id`, `name`, `country`, `risk_tier`, `created_at` | One row per shop |
| `transactions` | `id`, `merchant_ref`, `card_token`, `amount_cents`, `currency`, `status`, `risk_score`, `description`, `created_at` | One row per payment attempt |

Amounts are stored in cents as integers. No floats anywhere near money.

## Trust boundaries

- **Client to API** - anyone who can reach the API can post a payment. There is
  no authentication in this build.
- **API to Postgres** - credentials come from environment variables read in
  `app/config.py`.
- **API to Redis** - unauthenticated, on the internal network.
- **API to the rules service** - an optional outbound HTTP call, controlled by
  `RULES_SERVICE_URL`.

Each of those boundaries gets attention later in the course. Write down what you
notice about them now; you will be asked.

## Where things land later

| Directory | Currently | Fills up in |
| --- | --- | --- |
| `infra/` | empty | Week 3 (Terraform) |
| `k8s/` | empty | Week 9 (manifests) |
| `policies/` | empty | Week 15 (OPA/Rego) |
| `docs/RUNBOOK.md` | stub | Week 13 |
