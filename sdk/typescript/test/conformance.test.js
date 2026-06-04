const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const { flApplyUpdate, swipScale } = require("../src/index");

test("conformance cases", () => {
  const fixturePath = path.join(__dirname, "..", "..", "fixtures", "conformance", "cases.json");
  const payload = JSON.parse(fs.readFileSync(fixturePath, "utf8"));

  for (const c of payload.cases) {
    if (c.kind === "swip_scale") {
      const got = { result: swipScale(c.input.value) };
      assert.deepEqual(got, c.expected, c.name);
      continue;
    }

    if (c.kind === "fl_apply_update") {
      const got = flApplyUpdate(c.input.state, c.input.value);
      assert.deepEqual(got, c.expected, c.name);
      continue;
    }

    throw new Error(`unknown case kind: ${c.kind}`);
  }
});
