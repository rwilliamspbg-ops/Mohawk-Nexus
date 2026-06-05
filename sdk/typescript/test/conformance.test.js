const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const {
  flApplyUpdate,
  swipScale,
  BRIDGE_CONTRACT_NAME,
  BRIDGE_CONTRACT_SCHEMA_VERSION,
  BRIDGE_CONTRACT_MANIFEST_VERSION,
  BRIDGE_CONTRACT_SCHEMA_SHA256,
} = require("../src/index");

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

test("bridge contract metadata", () => {
  const versionPath = path.join(__dirname, "..", "..", "bridge", "bridge_contract.version.json");
  const version = JSON.parse(fs.readFileSync(versionPath, "utf8"));

  assert.equal(BRIDGE_CONTRACT_NAME, version.contract);
  assert.equal(BRIDGE_CONTRACT_SCHEMA_VERSION, version.schema_version);
  assert.equal(BRIDGE_CONTRACT_MANIFEST_VERSION, version.manifest_version);
  assert.equal(BRIDGE_CONTRACT_SCHEMA_SHA256.length, 64);
});
