import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";

// The academy's review generators are Python; their unit tests (negation and
// unknown cases of the source classifier, the claim ledger's validation rules)
// run here so that `npm test` and `npm run check` cover them.
test("Python unit tests for the academy review generators pass", () => {
  const run = spawnSync(
    "python3",
    ["-m", "unittest", "discover", "-s", "tests/py"],
    {
      encoding: "utf8",
    },
  );
  assert.equal(run.status, 0, `${run.stdout}\n${run.stderr}`);
});
