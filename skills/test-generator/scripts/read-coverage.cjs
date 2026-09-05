// Istanbul JSON を検証してから、丸め前の値で statement coverage を判定する。
const fs = require('node:fs');
const path = require('node:path');

function object(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function fail(message) {
  throw new Error(message);
}

function counters(value, label, arrays = false) {
  if (!object(value)) fail(`${label} must be an object`);
  for (const [id, hits] of Object.entries(value)) {
    const counts = arrays ? hits : [hits];
    if (!Array.isArray(counts) || counts.length === 0) {
      fail(`${label}[${id}] must contain hit counts`);
    }
    if (counts.some((hit) => !Number.isSafeInteger(hit) || hit < 0)) {
      fail(`${label}[${id}] must contain non-negative integer hit counts`);
    }
  }
}

function main() {
  const [reportFile, rawThreshold, ...targets] = process.argv.slice(2);
  const threshold = Number(rawThreshold);
  if (!reportFile || !rawThreshold || !Number.isFinite(threshold) || threshold < 0 || threshold > 100) {
    fail('expected report path and a threshold between 0 and 100');
  }
  if (!/^([0-9]{1,2}(\.[0-9]+)?|100(\.0+)?)$/.test(rawThreshold)) {
    fail('threshold must be a decimal number between 0 and 100');
  }
  // 29/50*100 のような二進浮動小数点誤差も判定へ持ち込まない。
  const thresholdScale = 10n ** BigInt((rawThreshold.split('.')[1] || '').length);
  const thresholdUnits = BigInt(rawThreshold.replace('.', ''));

  const report = JSON.parse(fs.readFileSync(reportFile, 'utf8'));
  if (!object(report) || Object.keys(report).length === 0) {
    fail('coverage report must be a non-empty Istanbul file map');
  }

  const entries = new Map();
  for (const [file, data] of Object.entries(report)) {
    if (!file || !object(data)) fail(`invalid file entry: ${file}`);
    const normalized = path.resolve(file);
    if (entries.has(normalized)) fail(`duplicate normalized file path: ${file}`);
    if (typeof data.path !== 'string' || path.resolve(data.path) !== normalized) {
      fail(`file path mismatch: ${file}`);
    }
    counters(data.s, `${file}: s`);
    const ids = Object.keys(data.s);
    if (!object(data.statementMap) || Object.keys(data.statementMap).length !== ids.length ||
        ids.some((id) => !Object.hasOwn(data.statementMap, id))) {
      fail(`statementMap and s do not match: ${file}`);
    }
    // f/b は statement 判定に使わないが、存在する counter の破損は見逃さない。
    if (Object.hasOwn(data, 'f')) counters(data.f, `${file}: f`);
    if (Object.hasOwn(data, 'b')) counters(data.b, `${file}: b`, true);
    entries.set(normalized, {
      file: path.relative(process.cwd(), normalized),
      total: ids.length,
      covered: Object.values(data.s).filter((hit) => hit > 0).length,
    });
  }

  const requested = targets.length ? [...new Set(targets.map((file) => path.resolve(file)))] : [...entries.keys()];
  const missing = requested.filter((file) => !entries.has(file));
  if (missing.length) fail(`requested files are missing from this report: ${missing.join(', ')}`);
  const selected = requested.map((file) => entries.get(file));

  let allPass = true;
  let measured = 0;
  console.log('=== Coverage Report ===');
  for (const entry of selected) {
    if (entry.total === 0) {
      console.log(`N/A ${entry.file} (no executable statements)`);
      continue;
    }
    measured += 1;
    const percentage = (entry.covered / entry.total) * 100;
    const pass = BigInt(entry.covered) * 100n * thresholdScale >= BigInt(entry.total) * thresholdUnits;
    allPass = allPass && pass;
    console.log(`${pass ? 'PASS' : 'FAIL'} ${percentage.toFixed(1)}% ${entry.file} (${entry.covered}/${entry.total} statements)`);
  }
  if (!measured) fail('no statements to evaluate in the selected files');
  return allPass ? 0 : 1;
}

try {
  process.exitCode = main();
} catch (error) {
  console.error(`ERROR: coverage report validation failed: ${error.message}`);
  process.exitCode = 1;
}
