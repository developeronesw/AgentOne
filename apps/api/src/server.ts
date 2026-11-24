import Fastify from "fastify";
const app = Fastify({ logger: true, bodyLimit: 64 * 1024 });
const port = Number(process.env.NODE_PORT ?? 8080);
const apiKey = process.env.API_KEY ?? "";
const intelligenceUrl = process.env.PYTHON_SERVICE_URL ?? "http://intelligence:8081";

app.get("/health", async () => ({ status: "ok", service: "agentone-api", version: "0.1.0" }));

app.post<{ Body: { url: string; max_pages?: number } }>("/v1/analyze", async (request, reply) => {
  if (!apiKey || request.headers["x-api-key"] !== apiKey) {
    return reply.code(401).send({ error: "Unauthorized" });
  }
  if (!request.body || typeof request.body.url !== "string" || request.body.url.length > 2048) {
    return reply.code(400).send({ error: "A valid URL string is required." });
  }
  const maxPages = request.body.max_pages;
  if (maxPages !== undefined && (!Number.isInteger(maxPages) || maxPages < 1 || maxPages > 20)) {
    return reply.code(400).send({ error: "max_pages must be an integer from 1 to 20." });
  }
  try {
    const upstream = await fetch(`${intelligenceUrl}/v1/analyze`, {
      method: "POST",
      headers: { "content-type": "application/json", "x-api-key": apiKey },
      body: JSON.stringify(request.body),
      signal: AbortSignal.timeout(45000)
    });
    const payload = await upstream.json().catch(() => ({ error: "Invalid intelligence response" }));
    return reply.code(upstream.status).send(payload);
  } catch (err) {
    request.log.error({ err }, "Python intelligence service failed");
    return reply.code(502).send({ error: "Intelligence service unavailable" });
  }
});
app.listen({ host: "0.0.0.0", port }).catch((err) => {
  app.log.error(err);
  process.exit(1);
});
