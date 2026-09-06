const assert = require('node:assert/strict');
const render = require('./index.cjs');
assert.equal(render('Hello'), '[Hello]');
console.log('limited update: ok');
