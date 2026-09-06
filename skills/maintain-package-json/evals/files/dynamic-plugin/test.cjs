const assert = require('node:assert/strict');
const render = require('./index.cjs');
assert.equal(render('Hello'), 'HELLO');
console.log('dynamic plugin: ok');
