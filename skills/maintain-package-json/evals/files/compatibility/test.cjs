const assert = require("node:assert/strict");
assert.equal(require("fixture-addon")(), "stable");
assert.equal(require("fixture-engine")(), "stable");
