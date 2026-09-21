const fs = require('node:fs');
const phase = process.argv[2];
fs.appendFileSync(process.env.EVENT_LOG, JSON.stringify([phase, ...process.argv.slice(3)]) + '\n');
if (process.env.FAIL_PHASE === phase) process.exit(7);
