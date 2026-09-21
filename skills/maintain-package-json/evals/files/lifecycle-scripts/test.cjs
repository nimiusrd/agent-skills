const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'fixture-hooks-'));
try {
  for (const command of ['build', 'build:copy']) {
    for (const failure of ['', 'pre', 'build']) {
      const log = path.join(tmp, 'events.jsonl');
      fs.writeFileSync(log, '');
      const result = spawnSync('npm', ['run', command, '--', 'a b', 'x;y'], {
        env: {...process.env, EVENT_LOG: log, FAIL_PHASE: failure}, encoding: 'utf8'
      });
      const events = fs.readFileSync(log, 'utf8').trim().split('\n').filter(Boolean).map(x => JSON.parse(x));
      const expected = failure === 'pre' ? [['pre']] : failure === 'build' ? [['pre'], ['build', 'a b', 'x;y']] : [['pre'], ['build', 'a b', 'x;y'], ['post']];
      assert.deepEqual(events, expected, result.stdout + result.stderr);
      assert.equal(result.status === 0, failure === '', result.stdout + result.stderr);
    }
  }
} finally { fs.rmSync(tmp, {recursive: true, force: true}); }
