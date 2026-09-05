// 指定された Istanbul JSON だけを読み、statement coverage のしきい値を判定する。
// テストは実行しない。PASS はテスト成功やレポートの鮮度を保証しない。
const fs = require('node:fs');
const path = require('node:path');

const USAGE = 'Usage: node read-coverage.cjs <report.json> <threshold> [files...]';
const SCOPE = 'Scope: report thresholds only; test success and report freshness are not verified.';

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
  const args = process.argv.slice(2);
  if (args.length === 1 && args[0] === '--help') {
    console.log(`${USAGE}

既存の Istanbul coverage-final.json 形式を読み取り専用で検査します。
プロジェクトのルートを cwd にしてください。対象省略時は全ファイルを検査します。
threshold は 0〜100 の十進数、files は cwd 基準の相対パスまたは絶対パスです。
対象は正規化後の完全一致で選択し、しきい値の判定には丸め前の比率を使います。
実行可能な statement がないファイルは N/A、測定可能な対象がなければエラーです。
終了コード: 0 = 測定可能な全対象がしきい値以上、1 = 未達または入力エラー。
テストの実行・レポートの探索・ファイルの変更は行いません。
PASS はこのレポートのしきい値判定だけを表し、テスト成功や鮮度を保証しません。
${SCOPE}`);
    return 0;
  }
  const [reportFile, rawThreshold, ...targets] = args;
  if (!reportFile || rawThreshold === undefined) {
    console.error(USAGE);
    fail('report path and threshold are required');
  }
  if (!/^([0-9]{1,2}(\.[0-9]+)?|100(\.0+)?)$/.test(rawThreshold)) {
    console.error(USAGE);
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
  console.log(`Report: ${path.resolve(reportFile)}`);
  console.log(SCOPE);
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
