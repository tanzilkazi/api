# API Integration Lab

## Purpose

This project exists to level up my API integration skills from “I can call an endpoint” to “I can design, debug, and run integrations that behave like production systems.”

The goal is to:

- Understand how real APIs behave under load, failure, and bad data
- Learn how to structure integrations cleanly (clients, config, logging)
- Handle auth, pagination, filters, rate limits, schema drift, and nulls
- Build small services that talk to multiple external APIs reliably
- Add observability (logging, basic metrics) and resilience (retries, backoff)
- Treat even small scripts like production-adjacent code

I’ll be adding `.py` files over time; ChatGPT will use this README and the code to track my intent and teaching sequence.

---

## Learning Outcomes

From this project, I want to become comfortable with:

- **HTTP client behaviour**

  - Requests, sessions, timeouts
  - Retries with backoff and jitter

- **Authentication & security**

  - API keys, OAuth2, headers
  - Environment-based secrets (`.env`, no secrets in code)

- **Data access patterns**

  - Pagination
  - Filters & query parameters
  - Joining API data with my own logic

- **Reliability & performance**

  - Rate limit handling
  - Caching & retries
  - Failure modes: network errors, stale tokens, 4xx/5xx responses

- **Robustness & maintenance**

  - Logging & debugging HTTP calls
  - Schema drift & null handling
  - Building a CLI or script that feels “production-y”

- **System glue**
  - Webhooks and async triggers
  - Integrating Slack / Notion / Gmail / similar
  - Deploying a small service to a cheap host (Railway, Fly.io, etc.)

---

## 14-Day Practical Path

This repo is organised roughly around this 14-day plan:

| Day   | Focus                                           |
| ----- | ----------------------------------------------- |
| 1–2   | Requests, retries, sessions                     |
| 3–4   | Auth systems + environment secrets              |
| 5     | Logging & instrumenting HTTP calls              |
| 6–7   | Webhooks + async triggers                       |
| 8–9   | Build tiny service calling 3 APIs               |
| 10    | Write failure tests (rate limits, stale tokens) |
| 11–12 | Add Slack/Notion/Gmail integration              |
| 13    | Deploy somewhere cheap (Railway/Fly)            |
| 14    | Document “API integration checklist”            |

Each `src/exercises/dayXX_*.py` file will implement practical tasks for that day.

---
