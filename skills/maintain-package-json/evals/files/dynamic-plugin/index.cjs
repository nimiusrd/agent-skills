const config = require('./plugin.json');
const plugin = require(config.prefix + config.name);
module.exports = value => plugin(value);
