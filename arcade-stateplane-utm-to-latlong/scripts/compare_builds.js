// Cross-check two builds against each other in all four output modes, confirm the
// modes agree, and exercise the edge cases.
//
//   node compare_builds.js                      # condensed vs documented
//   node compare_builds.js a.txt b.txt          # any two builds
//
// Needs a points file from validate.py; run that first, or pass --points <file>.
const fs = require('fs');
const { compile, BUILTINS } = require('./harness.js');
const NAMES = Object.keys(BUILTINS), VALUES = NAMES.map(n => BUILTINS[n]);

const D = __dirname + '/../builds/';
// Pull --points <file> out before reading the positional build paths, so the flag can
// be used on its own.
const argv = process.argv.slice(2);
const ptsArg = argv.indexOf('--points');
const ptsFile = ptsArg >= 0 ? argv.splice(ptsArg, 2)[1] : __dirname + '/_validate_points.json';
const C = argv[0] || (D + 'arcade_latlong_condensed.txt');
const O = argv[1] || (D + 'arcade_latlong_documented.txt');
if (!ptsFile || !fs.existsSync(ptsFile)) {
  console.error('no reference points at ' + ptsFile +
                '\nRun validate.py first (it leaves the file behind), or pass --points <file>.');
  process.exit(1);
}
const pts = JSON.parse(fs.readFileSync(ptsFile, 'utf8'));
const MODES = ['LAT', 'LON', 'BOTH', 'RULE'];

const fn = {};
for (const m of MODES) { fn['C' + m] = compile(C, m); fn['O' + m] = compile(O, m); }
const feat = (w, x, y) => ({ geometry: { X: x, Y: y, spatialReference: { wkid: w } } });
const run = (f, p) => f(...VALUES, feat(p[0], p[1], p[2]));

let diffBuild = 0, diffMode = 0, diffBoth = 0, n = 0;
let worstBuild = 0;
for (const p of pts) {
  const r = {};
  for (const m of MODES) { r['C' + m] = run(fn['C' + m], p); r['O' + m] = run(fn['O' + m], p); }
  for (const m of MODES) {
    const a = JSON.stringify(r['C' + m]), b = JSON.stringify(r['O' + m]);
    if (a !== b) {
      diffBuild++;
      if (m === 'LAT' || m === 'LON') worstBuild = Math.max(worstBuild, Math.abs(r['C' + m] - r['O' + m]));
      if (diffBuild <= 3) console.log('  build differ', m, p[0], a, b);
    }
  }
  // RULE dictionary must equal the separate LAT / LON runs
  const d = r.CRULE.result.attributes;
  if (d.LAT_CALCULATED !== r.CLAT || d.LON_CALCULATED !== r.CLON) {
    diffMode++;
    if (diffMode <= 3) console.log('  RULE vs LAT/LON differ', p[0], d, r.CLAT, r.CLON);
  }
  // BOTH text must parse back to the same numbers at its 6-dp resolution
  const m2 = /^Lat: (-?[\d.]+), Lon: (-?[\d.]+)$/.exec(r.CBOTH);
  if (!m2) { diffBoth++; if (diffBoth <= 3) console.log('  BOTH unparseable', p[0], r.CBOTH); }
  else {
    if (Math.abs(parseFloat(m2[1]) - r.CLAT) > 5e-7 || Math.abs(parseFloat(m2[2]) - r.CLON) > 5e-7) {
      diffBoth++;
      if (diffBoth <= 3) console.log('  BOTH mismatch', p[0], r.CBOTH, r.CLAT, r.CLON);
    }
  }
  n++;
}
console.log('points compared        :', n, '(x4 modes x2 builds =', n * 8, 'values)');
console.log('build A vs build B     :', diffBuild, 'differing values, worst numeric delta', worstBuild);
console.log('RULE vs LAT/LON        :', diffMode, 'mismatches');
console.log('BOTH text vs numbers   :', diffBoth, 'mismatches');

console.log('\n--- edge cases (build A) ---');
const cases = [
  ['null geometry',        { geometry: null }],
  ['missing geometry',     {}],
  ['NAD27 UTM 15N (26715)', feat(26715, 500000, 3300000)],
  ['Web Mercator (3857)',  feat(3857, -9000000, 4000000)],
  ['GCS WGS84 (4326)',     feat(4326, -89.09, 37.49)],
  ['wkid 0 (unknown SR)',  feat(0, 100, 100)],
  ['x/y = 0,0 in 6455',    feat(6455, 0, 0)],
  ['absurd x/y in 6455',   feat(6455, 1e12, 1e12)],
  ['NaN coordinates',      feat(6455, NaN, NaN)],
  ['UTM 1N west edge',     feat(32601, 221412.8427, 743513.2686)],
  ['UTM 60S',              feat(32760, 420604.3221, 1830911.2305)],
];
for (const [label, f] of cases) {
  for (const m of ['LAT', 'RULE']) {
    let out;
    try { out = JSON.stringify(fn['C' + m](...VALUES, f)); }
    catch (e) { out = 'THREW: ' + e.message; }
    console.log(('  ' + label).padEnd(26), m.padEnd(5), out);
  }
}
