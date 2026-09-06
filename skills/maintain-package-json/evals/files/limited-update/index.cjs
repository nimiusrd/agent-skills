const format = require('fixture-formatter');
const helper = require('fixture-helper');
module.exports = value => helper(format(value));
