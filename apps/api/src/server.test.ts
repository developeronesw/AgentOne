import test from "node:test";
import assert from "node:assert/strict";
test("API port default is 8080", () => {
  assert.equal(Number(process.env.NODE_PORT ?? 8080), 8080);
});
