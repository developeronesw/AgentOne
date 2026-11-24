# AgentOne
**Discover · Qualify · Grow** — by Developer One.

AgentOne is a universal business intelligence and prospecting platform. Initial backend includes a Python website-intelligence service, Node.js API gateway, PostgreSQL, Redis, Docker Compose and CI tests.

## Current backend milestone
- Python 3.12 FastAPI: bounded crawling, structured extraction, public contact observations, keyword taxonomy signals, preliminary site checks.
- Node.js 22 + TypeScript Fastify API gateway.
- Postgres and Redis containers prepared for database/queue integration.
- URL validation and public-IP checks, redirects revalidated manually, standard ports only.
- Robots.txt and sitemap discovery; capped crawl pages, request timeout, content size limits.
- No generative LLM dependency. Evidence-based observations; no unsupported claims.

## Local install
1. Install Docker Engine and Docker Compose v2.
2. Clone and enter the repository on `main`.
3. Copy `.env.example` to `.env`, set a long random `API_KEY` and strong `POSTGRES_PASSWORD`.
4. Run `docker compose up --build -d`.
5. Health checks: API `http://localhost:8080/health`; intelligence `http://localhost:8081/health`.
6. POST `http://localhost:8080/v1/analyze` with JSON `{"url":"https://example.com"}` and header `x-api-key: <API_KEY>`.

## Tests
Python: `PYTHONPATH=intelligence pytest intelligence/tests -q`.
API: `cd apps/api && npm install && npm run build && npm test`.

## Security and deployment notes
Development baseline, **not production-ready**. Before test-domain deployment, configure TLS, reverse proxy, firewall, secret management, rate limiting, authentication and tenant isolation, monitoring, backups, crawl-policy review and more SSRF/DNS-rebinding tests. Keep secrets out of Git. Only analyze sites you are authorized to access. "No website listed" is not proof a business has no website.
