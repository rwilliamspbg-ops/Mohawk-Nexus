function round6(value) {
  return Math.round(Number(value) * 1_000_000) / 1_000_000;
}

const {
  BRIDGE_CONTRACT_NAME,
  BRIDGE_CONTRACT_SCHEMA_VERSION,
  BRIDGE_CONTRACT_MANIFEST_VERSION,
  BRIDGE_CONTRACT_SCHEMA_SHA256,
} = require("./bridgeContract");

function swipScale(value) {
  return round6(Number(value) * 1.5);
}

function flApplyUpdate(state, value) {
  const round = Number(state.round ?? 0);
  const updates = Array.isArray(state.updates) ? state.updates.map(Number) : [];
  updates.push(Number(value));

  if (updates.length >= 2) {
    const sum = updates.reduce((acc, v) => acc + v, 0);
    return {
      round: round + 1,
      global: round6(sum / updates.length),
      updates: [],
    };
  }

  return {
    round,
    updates: updates.map(round6),
  };
}

module.exports = {
  flApplyUpdate,
  swipScale,
  BRIDGE_CONTRACT_NAME,
  BRIDGE_CONTRACT_SCHEMA_VERSION,
  BRIDGE_CONTRACT_MANIFEST_VERSION,
  BRIDGE_CONTRACT_SCHEMA_SHA256,
};
